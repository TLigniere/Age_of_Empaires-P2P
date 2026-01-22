import pickle
import os
from ai_strategies.base_strategies import AI

# ========== MODIFIÉ : Sauvegarde simplifiée avec GameState ==========
def save_game_state(game_state, filename="saves/default_game.pkl"):
    """
    Sauvegarde l'état complet du jeu dans un fichier.
    
    Args:
        game_state: Instance de GameState contenant tout l'état du jeu
        filename: Chemin du fichier de sauvegarde
    """
    try:
        with open(filename, "wb") as file:
            pickle.dump(game_state, file)
        print(f"[INFO] Game saved to {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to save game: {e}")

def load_game_state(filename="saves/default_game.pkl"):
    """
    Charge l'état du jeu depuis un fichier de sauvegarde.
    
    Args:
        filename: Chemin du fichier de sauvegarde
    
    Returns:
        GameState: Instance de GameState ou None si échec
    """
    if os.path.exists(filename):
        try:
            with open(filename, "rb") as file:
                game_state = pickle.load(file)
            print(f"[INFO] Game loaded from {filename}")
            return game_state
        except Exception as e:
            print(f"[ERROR] Failed to load game: {e}")
            return None
    else:
        print(f"[WARNING] Save file {filename} does not exist.")
        return None
# ====================================================================


# ========== OPTIONNEL : Fonction de compatibilité avec l'ancien format ==========
def load_legacy_save(filename):
    """
    Charge un ancien format de sauvegarde (units, buildings, game_map, ai)
    et le convertit en GameState.
    
    Utilisé pour la rétrocompatibilité avec les anciennes sauvegardes.
    
    Returns:
        GameState ou None
    """
    if os.path.exists(filename):
        try:
            with open(filename, "rb") as file:
                data = pickle.load(file)
            
            # Vérifier si c'est l'ancien format (tuple de 4 éléments)
            if isinstance(data, tuple) and len(data) == 4:
                units, buildings, game_map, ai = data
                
                # Importer GameState ici pour éviter les imports circulaires
                from controller import GameState
                
                # Créer un nouveau GameState
                game_state = GameState()
                game_state.units = units
                game_state.buildings = buildings
                game_state.game_map = game_map
                game_state.player_ai = ai
                game_state.player_side = 'J1'  # Par défaut
                
                # Assigner les propriétaires si non définis
                for unit in game_state.units:
                    if not hasattr(unit, 'owner'):
                        unit.owner = 'J1'
                
                for building in game_state.buildings:
                    if not hasattr(building, 'owner'):
                        building.owner = 'J1'
                
                print(f"[INFO] Legacy save converted from {filename}")
                return game_state
            else:
                # C'est déjà un GameState
                return data
                
        except Exception as e:
            print(f"[ERROR] Failed to load legacy save: {e}")
            return None
    else:
        print(f"[WARNING] Save file {filename} does not exist.")
        return None
# ================================================================================