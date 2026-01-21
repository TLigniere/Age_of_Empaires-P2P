import pickle
import os

# Fichier temporaire pour sauvegarder l'état du jeu
SAVE_FILE = 'game_state.pkl'

def save_game_state(units, buildings, game_map, ai):
    """Sauvegarde l'état du jeu dans un fichier."""
    with open(SAVE_FILE, 'wb') as f:
        pickle.dump((units, buildings, game_map, ai), f)

def load_game_state():
    """Charge l'état du jeu à partir d'un fichier."""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'rb') as f:
            return pickle.load(f)
    return None, None, None, None


