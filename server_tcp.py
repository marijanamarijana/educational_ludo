import random
import socket
import string
import threading
import json
import uuid

from data import multiple_choice_questions, true_false_questions

# HOST = "0.0.0.0" # for cloud
HOST = "127.0.0.1" # for local
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
        self.players = {}
        self.player_order = []
        self.game_state = {
            "players": {},
            "turn_id": None,
            "game_started": False,
            "winner_id": None,
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
                self.players[p]["conn"].sendall(len(data).to_bytes(4, 'big') + data)
            except:
                continue

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
        self.pass_turn()

    def switch_duel_to_quiz(self):
        if self.game_state["duel"]["active"]:
            self.game_state["duel"]["phase"] = "QUIZ"
            self.broadcast()

    def add_player(self, conn):
        p_uuid = str(uuid.uuid4())
        self.players[p_uuid] = {"conn": conn, "name": None, "color": None}
        self.player_order.append(p_uuid)
        self.game_state["players"][p_uuid] = {
            "name": None, "color": None, "pawns": [-1] * 4, "finished": [False] * 4
        }
        return p_uuid

    def remove_player(self, p_uuid):
        if p_uuid in self.players:
            if self.game_state["turn_id"] == p_uuid:
                self.pass_turn()

            del self.players[p_uuid]
            if p_uuid in self.game_state["players"]:
                del self.game_state["players"][p_uuid]
            if p_uuid in self.player_order:
                self.player_order.remove(p_uuid)

    def pass_turn(self):
        if not self.player_order:
            return

        try:
            curr_idx = self.player_order.index(self.game_state["turn_id"])
            next_idx = (curr_idx + 1) % len(self.player_order)
            self.game_state["turn_id"] = self.player_order[next_idx]
        except ValueError:
            self.game_state["turn_id"] = self.player_order[0]

    def check_winner(self):
        for pid, pdata in self.game_state["players"].items():
            if all(pdata["finished"]):
                self.game_state["winner_id"] = pid
                return pid
        return None


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
                    player_id = lobby.add_player(conn)
                    lobby.game_state["turn_id"] = player_id

                conn.sendall(len(json.dumps({"type": "lobby_created", "code": code, "player_id": player_id}).encode()).to_bytes(4, "big") +
                             json.dumps({"type": "lobby_created", "code": code, "player_id": player_id}).encode())

            elif t == "join_lobby":
                code = msg.get("code")
                with lock:
                    lobby = lobbies.get(code)
                    if lobby is None or len(lobby.players) >= lobby.max_players:
                        err = {"type": "error", "message": "Lobby full or does not exist"}
                        conn.sendall(len(json.dumps(err).encode()).to_bytes(4, "big") + json.dumps(err).encode())
                        continue
                    player_id = lobby.add_player(conn)
                    lobby.broadcast()
                conn.sendall(len(json.dumps({"type": "lobby_joined", "code": code, "player_id": player_id}).encode()).to_bytes(4, "big") +
                             json.dumps({"type": "lobby_joined", "code": code, "player_id": player_id}).encode())

            elif t == "register":
                print("registering")
                if lobby and player_id is not None:
                    new_name = msg.get("name")
                    new_color = msg.get("color")

                    name_taken = False
                    color_taken = False

                    with lock:
                        for i, p in enumerate(lobby.players.values()):
                            if p["name"] == new_name:
                                name_taken = True
                            if p["color"] == new_color:
                                color_taken = True

                    if name_taken or color_taken:
                        reason = "Името" if name_taken else "Бојата"
                        if name_taken and color_taken: reason = "Името и бојата"

                        err = {"type": "error", "message": f"{reason} веќе постои!"}
                        conn.sendall(len(json.dumps(err).encode()).to_bytes(4, "big") + json.dumps(err).encode())
                    else:
                        lobby.players[player_id]["name"] = new_name
                        lobby.players[player_id]["color"] = new_color
                        lobby.game_state["players"][player_id]["name"] = new_name
                        lobby.game_state["players"][player_id]["color"] = new_color
                        lobby.broadcast()

            elif t == "start_game":
                if lobby and conn == lobby.host:
                    lobby.game_state["game_started"] = True
                    lobby.broadcast()

            elif t == "rolling_dice":
                data = json.dumps({"type": "dice_state", "value": msg.get("value")}).encode('utf-8')
                for p in lobby.players:
                    try:
                        lobby.players[p]["conn"].sendall(len(data).to_bytes(4, 'big') + data)
                    except:
                        continue

            elif t == "move":
                if lobby and player_id == lobby.game_state["turn_id"]:
                    p_idx, steps = msg.get("pawn", -1), msg.get("dice", 0)
                    data = json.dumps({"type": "dice_state", "value": None}).encode('utf-8')
                    for p in lobby.players:
                        try:
                            lobby.players[p]["conn"].sendall(len(data).to_bytes(4, 'big') + data)
                        except:
                            continue
                    if p_idx == -1:
                        winner = lobby.check_winner()
                        if winner:
                            lobby.broadcast()
                            continue
                        lobby.pass_turn()
                        lobby.broadcast()
                        continue
                    p_data = lobby.game_state["players"][player_id]["pawns"]
                    if p_idx != -1:
                        if p_data[p_idx] == -1 and steps == 6:
                            p_data[p_idx] = 0
                        elif p_data[p_idx] != -1:
                            p_data[p_idx] += steps
                    if p_data[p_idx] < 0:
                        p_data[p_idx] = 0
                    winner = lobby.check_winner()
                    if winner:
                        lobby.broadcast()
                        continue
                    lobby.pass_turn()
                    lobby.broadcast()

            elif t == "duel_ready":
                if not hasattr(lobby, 'duel_ready_players'):
                    lobby.duel_ready_players = set()

                lobby.duel_ready_players.add(msg.get("player"))

                p1 = lobby.game_state["duel"]["p1"]
                p2 = lobby.game_state["duel"]["p2"]

                if p1 in lobby.duel_ready_players and p2 in lobby.duel_ready_players:
                    lobby.switch_duel_to_quiz()
                    lobby.duel_ready_players.clear()

            elif t == "initiate_duel":
                duel = lobby.game_state["duel"]
                lobby.game_state["turn_id"] = msg["p1"]
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
                lobby.broadcast()

            elif t == "duel_answer":
                duel = lobby.game_state["duel"]
                q_idx = duel["q_index"]
                player_id = msg["player"]
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

            elif t == "exit":
                player_id = msg.get("player")
                print("player clicked menu")
                with lock:
                    if player_id in lobby.players:
                        lobby.remove_player(player_id)
                        lobby.broadcast()

                    if not lobby.players and lobby.code in lobbies:
                        del lobbies[lobby.code]
                        print("Lobby deleted, no players left.")



    except Exception as e:
        print("Client disconnected:", e)
    finally:
        if lobby and player_id is not None:
            with lock:
                if player_id in lobby.players:
                    lobby.remove_player(player_id)
                    lobby.broadcast()

                if not lobby.players and lobby.code in lobbies:
                    del lobbies[lobby.code]
                    print("Lobby deleted, no players left.")
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
