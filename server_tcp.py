import random
import socket
import threading
import json
import time

from data import multiple_choice_questions, true_false_questions


class LudoServer:
    def __init__(self, host='127.0.0.1', port=62743):
        self.host = host
        self.port = port
        self.kill = False
        self.lock = threading.Lock()

        self.players = []
        self.game_state = {
            "players": [],
            "turn": 0,
            "game_started": False,
            "duel": {
                "active": False,
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

    def reset_game(self):
        print("[SERVER] All players disconnected. Resetting game...")
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

    def broadcast(self):
        data = json.dumps(self.game_state).encode('utf-8')
        for conn in self.players:
            try:
                conn.sendall(len(data).to_bytes(4, 'big') + data)
            except:
                self.players.remove(conn)

    def handle_client(self, conn, addr):
        player_id = len(self.players) - 1

        try:
            while not self.kill:
                header = conn.recv(4)
                if not header: break
                msg_len = int.from_bytes(header, 'big')

                data = conn.recv(msg_len).decode('utf-8')
                msg = json.loads(data)

                if msg["type"] == "register":
                    self.game_state["players"][player_id]["name"] = msg["name"]
                    self.game_state["players"][player_id]["color"] = msg["color"]
                    if len(self.players) >= 2:
                        self.game_state["game_started"] = True


                elif msg["type"] == "move":
                    p_idx, steps = msg["pawn"], msg["dice"]
                    p_data = self.game_state["players"][player_id]["pawns"]

                    if p_idx != -1:
                        if p_data[p_idx] == -1 and steps == 6:
                            p_data[p_idx] = 0
                        else:
                            p_data[p_idx] += steps

                    self.game_state["turn"] = (self.game_state["turn"] + 1) % len(self.players)


                elif msg["type"] == "initiate_duel":
                    duel = self.game_state["duel"]
                    self.game_state["turn"] = msg["p1"]

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
                        "questions": random.sample(self.questions, 3)
                    })

                    threading.Timer(3.0, self.switch_duel_to_quiz).start()

                elif msg["type"] == "duel_answer":
                    duel = self.game_state["duel"]
                    q_idx = duel["q_index"]

                    if player_id == duel["p1"]:
                        duel["p1_answers"][str(q_idx)] = msg["correct"]
                    if player_id == duel["p2"]:
                        duel["p2_answers"][str(q_idx)] = msg["correct"]

                    if str(q_idx) in duel["p1_answers"] and str(q_idx) in duel["p2_answers"]:
                        if duel["q_index"] < 2:
                            duel["q_index"] += 1
                        else:
                            self.resolve_duel()

        except Exception as e:
            print(f"Player {player_id} disconnected: {e}")

        finally:
            with self.lock:
                if conn in self.players:
                    self.players.remove(conn)

                if len(self.players) == 0:
                    self.reset_game()
            conn.close()

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            print(f"Server started on {self.host}:{self.port}")

            threading.Thread(target=self.broadcast_loop, daemon=True).start()

            try:
                while not self.kill:
                    s.settimeout(1)
                    while len(self.players) < 4:
                        try:
                            conn, addr = s.accept()
                        except socket.timeout:
                            continue
                        self.players.append(conn)
                        self.game_state["players"].append({
                            "name": None,
                            "color": None,
                            "pawns": [-1, -1, -1, -1],
                            "finished": [False] * 4
                        })

                        welcome = json.dumps({"type": "welcome", "player_id": len(self.players) - 1, "game_state": self.game_state})
                        conn.sendall(len(welcome).to_bytes(4, 'big') + welcome.encode('utf-8'))

                        threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except KeyboardInterrupt:
                print("[SERVER] Shutdown signal received.")
            finally:
                self.shutdown_server()

    def shutdown_server(self):
        self.kill = True
        print("[SERVER] Closing player connections...")
        with self.lock:
            for conn in self.players:
                try:
                    conn.close()
                except:
                    pass
            self.players.clear()
        print("[SERVER] Server offline.")

    def broadcast_loop(self):
        while not self.kill:
            if self.players:
                self.broadcast()
            time.sleep(0.05)


if __name__ == "__main__":
    LudoServer().run()
