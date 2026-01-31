import sys, logging, json
from mpgameserver import EventHandler, ServerContext, TwistedServer


class LudoEventHandler(EventHandler):
    def __init__(self):
        super().__init__()
        self.game_state = {
            "players": [],
            "turn": 0,
            "game_started": False,
            "max_players": 4
        }
        self.connected_clients = []
        self.client_to_player_id = {}

    def starting(self):
        print("Server starting...")

    def connect(self, client):
        print(f"Client connected: {client}")

        player_id = len(self.game_state["players"])

        if player_id >= self.game_state["max_players"]:
            print(f"Game full! Rejecting client {client}")
            return

        self.client_to_player_id[client] = player_id

        self.game_state["players"].append({
            "name": None,
            "color": None,
            "pawns": [-1, -1, -1, -1],
            "finished": [False, False, False, False]
        })

        self.connected_clients.append(client)

        welcome_msg = {
            "type": "welcome",
            "player_id": player_id,
            "game_state": self.game_state
        }
        client.send(json.dumps(welcome_msg).encode("utf-8"))
        print(f"Assigned player ID {player_id} to client {client}")

    def disconnect(self, client):
        print(f"Client disconnected: {client}")
        if client in self.connected_clients:
            self.connected_clients.remove(client)
        if client in self.client_to_player_id:
            del self.client_to_player_id[client]

    def handle_message(self, client, seqnum, msg):
        try:
            if isinstance(msg, bytes):
                msg = json.loads(msg.decode("utf-8"))
        except Exception as e:
            print("Failed to decode message:", e)
            return

        # Get player ID for this client
        pid = self.client_to_player_id.get(client)
        if pid is None or pid >= len(self.game_state["players"]):
            print(f"Invalid player ID for client {client}")
            return

        player_data = self.game_state["players"][pid]

        if msg.get("type") == "register":
            player_data["name"] = msg.get("name")
            received_color = msg.get("color")
            if isinstance(received_color, list):
                received_color = tuple(received_color)
            player_data["color"] = received_color
            print(f"Player {pid} registered as {player_data['name']} with color {player_data['color']}")

            registered_count = sum(1 for p in self.game_state["players"] if p["name"] and p["color"])
            if registered_count == len(self.connected_clients) and registered_count > 0:
                self.game_state["game_started"] = True
                print(f"All {registered_count} players registered! Game starting.")

            self._broadcast_state()

        elif msg.get("type") == "move":
            if not self.game_state["game_started"]:
                print("Game not started yet")
                return

            if self.game_state["turn"] != pid:
                print(f"Not player {pid}'s turn (current turn: {self.game_state['turn']})")
                return

            pawn_idx = msg.get("pawn")
            dice = msg.get("dice")

            if pawn_idx is None or pawn_idx >= len(player_data["pawns"]):
                print(f"Invalid pawn index: {pawn_idx}")
                return

            if player_data["pawns"][pawn_idx] == -1:
                if dice == 6:
                    player_data["pawns"][pawn_idx] = 0
                    print(f"Player {pid} ({player_data['name']}) brought pawn {pawn_idx} into play")
            else:
                new_pos = player_data["pawns"][pawn_idx] + dice
                if new_pos >= 57:
                    new_pos = 57
                    player_data["finished"][pawn_idx] = True
                    print(f"Player {pid} ({player_data['name']}) finished pawn {pawn_idx}")
                else:
                    print(
                        f"Player {pid} ({player_data['name']}) moved pawn {pawn_idx} from {player_data['pawns'][pawn_idx]} to {new_pos}")
                player_data["pawns"][pawn_idx] = new_pos

            if dice != 6:
                self.game_state["turn"] = (self.game_state["turn"] + 1) % len(self.connected_clients)
                print(f"Next turn: Player {self.game_state['turn']}")

            self._broadcast_state()

    def _broadcast_state(self):
        state_msg = json.dumps(self.game_state).encode("utf-8")
        print(f"Broadcasting: game_started={self.game_state['game_started']}, turn={self.game_state['turn']}")
        for c in self.connected_clients:
            try:
                c.send(state_msg)
            except Exception as e:
                print(f"Failed to send to client {c}: {e}")


def main():
    host, port = "0.0.0.0", 1474
    logging.basicConfig(level=logging.INFO)
    ctxt = ServerContext(LudoEventHandler())
    server = TwistedServer(ctxt, (host, port))
    server.run()


if __name__ == "__main__":
    main()
