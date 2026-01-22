import subprocess
import threading
import sys
import os

# python test_game.py 5000 5001
MY_PORT = sys.argv[1] if len(sys.argv) > 1 else "5000"
DEST_PORT = sys.argv[2] if len(sys.argv) > 2 else "5001"
EXE_PATH = "./GameP2P.exe"

print(f"--- (Port {MY_PORT} -> {DEST_PORT}) ---")

try:
    proc = subprocess.Popen(
        [EXE_PATH, MY_PORT, DEST_PORT],
        stdin=subprocess.PIPE,  
        stdout=subprocess.PIPE, 
        stderr=sys.stderr,
        text=True,
        bufsize=1
    )
except FileNotFoundError:
    print("ERREUR: GameP2P.exe introuvable.")
    sys.exit(1)

def ecouter_proc_c():
    while True:
        line = proc.stdout.readline()
        if not line: break
        print(f"\n[RECU] {line.strip()}")
        print("message > ", end="", flush=True)

t = threading.Thread(target=ecouter_proc_c, daemon=True)
t.start()

# envoi vers proc c
try:
    print("Tapez vos ordres (ex: MOVE|10|20) ou 'quit'")
    while True:
        cmd = input("message > ")
        
        if cmd == "quit": break
        
        # Envoi au C
        if proc.poll() is None:
            proc.stdin.write(cmd + "\n")
            proc.stdin.flush()

except KeyboardInterrupt:
    pass

print("Arrêt...")
proc.terminate()