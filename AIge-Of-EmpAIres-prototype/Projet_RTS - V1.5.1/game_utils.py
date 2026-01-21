import pickle
import os
from ai_strategies.base_strategies import AI

def save_game_state(units, buildings, game_map, ai, filename="saves/default_game.pkl"):
    """Save the current game state to a specified file."""
    with open(filename, "wb") as file:
        pickle.dump((units, buildings, game_map, ai), file)
    print(f"[INFO] Game saved to {filename}")

def load_game_state(filename="saves/default_game.pkl"):
    """Load the game state from a specified file, if it exists."""
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            units, buildings, game_map, ai = pickle.load(file)
            print(f"[INFO] Game loaded from {filename}")
            return units, buildings, game_map, ai
    else:
        print(f"[WARNING] Save file {filename} does not exist.")
        return None, None, None, None
