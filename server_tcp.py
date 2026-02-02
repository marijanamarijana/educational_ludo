import random
import socket
import string
import threading
import json

from data import multiple_choice_questions, true_false_questions

HOST = "127.0.0.1"
PORT = 62743

lobbies = {}
lock = threading.Lock()


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase, k=4))


class Lobby:
    def __init__(self, code, host_conn, max_players=4):
        self.code = code
        self.host = host_conn
        self.max_players = max_players
        self.players = []
        self.game_state = {
            "players": [],
            "turn": 0,
            "game_started": False,
            "duel": {
                "active": False,
                "phase": "INTRO",
                "p1": None,
                "p2": None,
                "trigger_pawn": None,
                "target_pawn": None,
                "q_index": 0,
                "p1_answers": {},
                "p2_answers": {},
                "questions": []
            }
        }
        self.questions = list(multiple_choice_questions.questions + true_false_questions.questions)

    def broadcast(self):
        data = json.dumps({"type": "game_state", "game_state": self.game_state}).encode('utf-8')
        for p in self.players:
            try:
                p["conn"].sendall(len(data).to_bytes(4, 'big') + data)
            except:
                continue

    def reset_if_empty(self):
        if not self.players:
            self.game_state = {
                "players": [],
                "turn": 0,
                "game_started": False,
                "duel": {
                    "active": False,
                    "phase": "INTRO",
                    "p1": None,
                    "p2": None,
                    "trigger_pawn": None,
                    "target_pawn": None,
                    "q_index": 0,
                    "p1_answers": {},
                    "p2_answers": {},
                    "questions": []
                }
            }

    def resolve_duel(self):
        duel = self.game_state["duel"]
        p1_id = duel["p1"]
        p2_id = duel["p2"]
        p1_pawn = duel["trigger_pawn"]
        p2_pawn = duel["target_pawn"]

        p1_score = sum(1 for a in duel["p1_answers"].values() if a)
        p2_score = sum(1 for a in duel["p2_answers"].values() if a)

        if p1_score >= p2_score:
            self.game_state["players"][p2_id]["pawns"][p2_pawn] = -1
        else:
            self.game_state["players"][p1_id]["pawns"][p1_pawn] = -1

        duel["active"] = False
        duel["p1_answers"] = {}
        duel["p2_answers"] = {}
        duel["q_index"] = 0
        duel["p1"] = None
        duel["p2"] = None
        duel["phase"] = "INTRO"
        self.game_state["turn"] = (self.game_state["turn"] + 1) % len(self.players)

    def switch_duel_to_quiz(self):
        if self.game_state["duel"]["active"]:
            self.game_state["duel"]["phase"] = "QUIZ"


def handle_client(conn, addr):
    global lobbies
    lobby = None
    player_id = None

    try:
        while True:
            header = conn.recv(4)
            if not header: break
            size = int.from_bytes(header, "big")
            msg = json.loads(conn.recv(size).decode())
            t = msg.get("type")

            if t == "create_lobby":
                code = generate_code()
                lobby = Lobby(code, conn, msg.get("max_players", 4))
                with lock:
                    lobbies[code] = lobby
                    player_id = 0
                    lobby.players.append({"conn": conn, "name": None, "color": None})
                    lobby.game_state["players"].append({"name": None, "color": None, "pawns": [-1]*4, "finished": [False]*4})
                conn.sendall(len(json.dumps({"type": "lobby_created", "code": code, "player_id": 0}).encode()).to_bytes(4, "big") +
                             json.dumps({"type": "lobby_created", "code": code, "player_id": 0}).encode())

            elif t == "join_lobby":
                code = msg.get("code")
                with lock:
                    lobby = lobbies.get(code)
                    if not lobby or len(lobby.players) >= lobby.max_players:
                        err = {"type": "error", "message": "Lobby full or does not exist"}
                        conn.sendall(len(json.dumps(err).encode()).to_bytes(4, "big") + json.dumps(err).encode())
                        continue
                    player_id = len(lobby.players)
                    lobby.players.append({"conn": conn, "name": None, "color": None})
                    lobby.game_state["players"].append({"name": None, "color": None, "pawns": [-1]*4, "finished": [False]*4})
                conn.sendall(len(json.dumps({"type": "lobby_joined", "code": code, "player_id": player_id}).encode()).to_bytes(4, "big") +
                             json.dumps({"type": "lobby_joined", "code": code, "player_id": player_id}).encode())

            elif t == "register":
                if lobby and player_id is not None:
                    lobby.players[player_id]["name"] = msg.get("name")
                    lobby.players[player_id]["color"] = msg.get("color")
                    lobby.game_state["players"][player_id]["name"] = msg.get("name")
                    lobby.game_state["players"][player_id]["color"] = msg.get("color")
                    lobby.broadcast()

            elif t == "start_game":
                if lobby and conn == lobby.host:
                    lobby.game_state["game_started"] = True
                    lobby.broadcast()

            elif t == "move":
                if lobby and player_id is not None:
                    p_idx, steps = msg.get("pawn", -1), msg.get("dice", 0)
                    p_data = lobby.game_state["players"][player_id]["pawns"]
                    if p_idx != -1:
                        if p_data[p_idx] == -1 and steps == 6:
                            p_data[p_idx] = 0
                        else:
                            p_data[p_idx] += steps
                    lobby.game_state["turn"] = (lobby.game_state["turn"] + 1) % len(lobby.players)
                    lobby.broadcast()

            elif t == "initiate_duel":
                duel = lobby.game_state["duel"]
                lobby.game_state["turn"] = msg["p1"]
                duel.update({
                    "active": True,
                    "phase": "INTRO",
                    "p1": msg["p1"],
                    "p2": msg["p2"],
                    "trigger_pawn": msg["p1_pawn"],
                    "target_pawn": msg["p2_pawn"],
                    "q_index": 0,
                    "p1_answers": {},
                    "p2_answers": {},
                    "questions": random.sample(lobby.questions, 3)
                })
                threading.Timer(3.0, lobby.switch_duel_to_quiz).start()
                lobby.broadcast()

            elif t == "duel_answer":
                duel = lobby.game_state["duel"]
                q_idx = duel["q_index"]
                if player_id == duel["p1"]:
                    duel["p1_answers"][str(q_idx)] = msg["correct"]
                if player_id == duel["p2"]:
                    duel["p2_answers"][str(q_idx)] = msg["correct"]

                if str(q_idx) in duel["p1_answers"] and str(q_idx) in duel["p2_answers"]:
                    if duel["q_index"] < 2:
                        duel["q_index"] += 1
                    else:
                        lobby.resolve_duel()
                lobby.broadcast()

    except Exception as e:
        print("Client disconnected:", e)
    finally:
        if lobby and player_id is not None:
            with lock:
                if player_id < len(lobby.players):
                    del lobby.players[player_id]
                    del lobby.game_state["players"][player_id]
                lobby.reset_if_empty()
        conn.close()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server running at {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
