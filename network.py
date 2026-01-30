import time
import socket
from view import Print_Display

NETWORK_PYTHON_PORT = 5001
NETWORK_MY_PORT = 5000
NETWORK_DEST_PORT = 6000

class NetworkClient:
    def __init__(self, python_port, my_port):
        self.python_port = python_port
        self.bridge_port = my_port

        self.connected = False
        self.inbox = []
        self.last_msg_time = time.time()

        # Socket UDP Non-Bloquant
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", self.python_port))
        self.sock.setblocking(False)

        print(
            f"[NET] Client prêt sur port {self.python_port} -> Bridge {self.bridge_port}"
        )

    def poll(self):
        """Récupère les messages du C et vérifie le timeout"""
        try:
            while True:  # On vide tout le buffer d'un coup
                data, _ = self.sock.recvfrom(4096)
                msg = data.decode().strip()

                # Parsing simple
                if "|" in msg:
                    parts = msg.split("|", 1)
                    self.inbox.append((parts[0], parts[1]))
                else:
                    self.inbox.append((msg, ""))

                # Le spam de données maintient la connexion en vie
                self.last_msg_time = time.time()
                if not self.connected:
                    self.connected = True
                    Print_Display("[NET] Connexion détectée !")

        except BlockingIOError:
            pass  # Rien à lire
        except ConnectionResetError:
            pass

        # Timeout : Si le "spam" s'arrête pendant 2s, c'est mort
        if self.connected and (time.time() - self.last_msg_time > 2.0):
            Print_Display("[NET] ⚠️  Connexion perdue (Plus de données)")
            self.connected = False

    def send(self, msg_type, payload=""):
        """Envoie vers le C"""
        msg = f"{msg_type}|{payload}" if payload else msg_type
        try:
            self.sock.sendto(msg.encode(), ("127.0.0.1", self.bridge_port))
        except OSError:
            pass

    def send_ping(self, unit_id, x, y):
        """Envoie un ping pour notifier un mouvement de villager"""
        payload = f"unit_id:{unit_id},x:{x},y:{y}"
        self.send("PING", payload)

    def consume_messages(self):
        msgs = self.inbox[:]
        self.inbox.clear()
        return msgs


def send_simple_message_to_c(network, msg_type, payload):
    """Send a simple message to C process"""
    try:
        network.send(msg_type, payload)
        # Print_Display(f"[DEBUG] Sent to C: {msg_type}|{payload}")
    except Exception as e:
        Print_Display(f"[WARNING] Error sending message to C: {str(e)}")

def send_game_state_to_c(network, units, buildings, ai, player_side):
    """Send current game state to C process"""

    try:
        # Send unit positions
        for unit in units:
            msg = f"UNIT_UPDATE|id:{unit.network_id},type:{unit.unit_type},x:{unit.x},y:{unit.y},owner:{unit.owner}"
            network.send("UNIT_UPDATE", msg)
            # Print_Display(f"[DEBUG] Sent to C: {msg}")

        # Send resource information
        if ai and ai.resources:
            res_msg = f"wood:{ai.resources.get('Wood', 0)},gold:{ai.resources.get('Gold', 0)},food:{ai.resources.get('Food', 0)}"
            network.send("RESOURCES", res_msg)
            # Print_Display(f"[DEBUG] Sent to C: {res_msg}")

        # Send building information
        for building in buildings:
            bld_msg = f"type:{building.building_type},x:{building.x},y:{building.y},owner:{building.owner}"
            network.send("BUILDING_STATE", bld_msg)
            # Print_Display(f"[DEBUG] Sent to C: {bld_msg}")

    except Exception as e:
        Print_Display(f"[WARNING] Error sending game state to C: {str(e)}")


def load_network_client(Python_port, My_port):
    """Initializes and returns a NetworkClient instance."""

    try:
        client = NetworkClient(
            python_port=Python_port, my_port=int(My_port)
        )
        return client
    except Exception as e:
        Print_Display(f"[ERROR] Échec de la connexion au processus C : {e}")

client = None
        