import time
import subprocess
import sys
import random

import socket
import time

class NetworkClient:
    def __init__(self, python_port=6000, bridge_port=5000):
        self.python_port = python_port
        self.bridge_port = bridge_port
        
        self.connected = False
        self.inbox = []
        self.last_msg_time = time.time()
        
        # Socket UDP Non-Bloquant
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", self.python_port))
        self.sock.setblocking(False)
        
        print(f"[NET] Client prêt sur port {self.python_port} -> Bridge {self.bridge_port}")

    def poll(self):
        """Récupère les messages du C et vérifie le timeout"""
        try:
            while True: # On vide tout le buffer d'un coup
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
                    print("[NET] Connexion détectée !")
                    
        except BlockingIOError:
            pass # Rien à lire
        except ConnectionResetError:
            pass

        # Timeout : Si le "spam" s'arrête pendant 2s, c'est mort
        if self.connected and (time.time() - self.last_msg_time > 2.0):
            print("[NET] ⚠️  Connexion perdue (Plus de données)")
            self.connected = False

    def send(self, msg_type, payload=""):
        """Envoie vers le C"""
        msg = f"{msg_type}|{payload}" if payload else msg_type
        try:
            self.sock.sendto(msg.encode(), ("127.0.0.1", self.bridge_port))
        except OSError:
            pass

    def consume_messages(self):
        msgs = self.inbox[:]
        self.inbox.clear()
        return msgs


if len(sys.argv) < 4:
    print("Usage: python main.py <NET_ME> <NET_DEST> <PY_LOCAL>")
    sys.exit(1)

NET_ME = sys.argv[1]
NET_DEST = sys.argv[2]
PY_PORT = int(sys.argv[3])
BRIDGE_EXE = "./GameP2P.exe"

print(f"--- DÉMARRAGE MOTEUR JEU ---")
bridge_proc = subprocess.Popen([BRIDGE_EXE, NET_ME, NET_DEST, str(PY_PORT)])
time.sleep(0.5)

network = NetworkClient(python_port=PY_PORT, bridge_port=int(NET_ME))

running = True
last_spam_time = time.time()
frame_count = 0

try:
    print(">>> LE JEU TOURNE. SPAM DE DONNÉES ACTIF (20Hz) <<<")
    
    while running:
        current_time = time.time()
        
        # --- A. NETWORK UPDATE ---
        network.poll()
        
        for msg_type, payload in network.consume_messages():
            if msg_type == "ATTACK":
                print(f"⚔️  [EVENT] Attaque reçue : {payload}")
            # elif msg_type == "POS": ... (On update les unités silencieusement)

        if current_time - last_spam_time > 0.05: 
            rx = random.randint(0, 500)
            ry = random.randint(0, 500)
            network.send("POS", f"Unit1:{rx}:{ry}")
            
            last_spam_time = current_time
            
            if frame_count % 60 == 0: # Toutes les ~3 secondes
                network.send("ATTACK", "Archer_1->Base")
                print(">>> [ACTION] Envoi ordre ATTACK")

        frame_count += 1
        time.sleep(0.010) # ~100 FPS max pour la boucle

except KeyboardInterrupt:
    pass

finally:
    bridge_proc.terminate()
    print("\nFermeture du pont C et du jeu.")