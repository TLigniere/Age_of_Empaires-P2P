import curses
import time
import os
import pygame
import subprocess
import sys
import signal
from model import Map, Unit, Building, Joueur
from view import display_with_curses, handle_input, init_colors, Print_Display
from view_graphics import handle_input_pygame, render_map, screen_width, screen_height, TILE_WIDTH, TILE_HEIGHT, initialize_graphics
from game_utils import save_game_state, load_game_state
import socket
import time

import select
import json 


from ai_strategies.base_strategies import AI

from ai_strategies.strategie_No1_dev_ai import StrategieNo1  # Importer la stratégie spécifique
# Création de la stratégie choisie
current_strategy = StrategieNo1()

# Utilisation de la stratégie dans update_game
last_update_time = 0  # Initialiser last_update_time avant la boucle principale du jeu




# Constants
SAVE_DIR = "saves"
DEFAULT_SAVE = os.path.join(SAVE_DIR, "default_game.pkl")
GAME_PLAYING = "PLAYING"
GAME_PAUSED = "PAUSED"


# ADD CURSE INPUT
class SpecialCode:
    ENTER = ord('\n')

# ========== NETWORK CONFIGURATION ==========
# Set to True when you have the C process running
# Set to False for local testing without C process
ENABLE_NETWORK = False
# ==========================================

# Simple GameState object to track player_side and AI resources
class GameState:
    def __init__(self):
        self.player_side = 'J1'  # Default to J1
        self.player_ai = None  # Will be set later
        
    def set_player_ai(self, ai_obj):
        self.player_ai = ai_obj

# Global Variables
units, buildings, game_map, ai = None, None, None, None
game_state = GAME_PLAYING
player_side_state = GameState()  # Track player side
network = None  # Global network client

NETWORK_PYTHON_PORT = 5001
NETWORK_MY_PORT = 5000
NETWORK_DEST_PORT = 6000

class GameElement:
    def __init__(self, id, owner=None):
        self.id             = id
        self.owner          = owner        # Joueur qui possède cet élément (propriété métier)
        self.network_owner  = owner  # Joueur qui contrôle cet élément pour le réseau
        self.state          = {}           # État de l’élément (ex: mur endommagé, ressources)

    def can_modify(self, player):
        return self.network_owner == player

    def modify(self, player, changes):
        if self.can_modify(player):
            self.state.update(changes)
            # envoyer un message réseau au processus C
            return True
        return False

def list_saves():
    saves = [f for f in os.listdir(SAVE_DIR) if f.endswith(".pkl")]
    return saves

def load_existing_game(filename):
    global units, buildings, game_map, ai, ai
    loaded_units, loaded_buildings, loaded_map, loaded_ai = load_game_state(filename)
    if loaded_units and loaded_buildings and loaded_map and loaded_ai:
        units, buildings, game_map, ai = loaded_units, loaded_buildings, loaded_map, loaded_ai
        Print_Display(f"[INFO] Chargé : {filename}")
    else:
        Print_Display("[ERROR] Chargement échoué. Le fichier est corrompu ou n'existe pas.")
        

def load_existing_game_curses(stdscr):
    saves = list_saves()
    if not saves:
        stdscr.addstr(5, 0, "[INFO] Aucune sauvegarde trouvée.")
        stdscr.refresh()
        time.sleep(2)
        return

    selected_option = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Choisissez une sauvegarde à charger:")
        for i, save in enumerate(saves):
            if i == selected_option:
                stdscr.addstr(i + 1, 0, save, curses.A_REVERSE)
            else:
                stdscr.addstr(i + 1, 0, save)
        stdscr.refresh()

        key = stdscr.getch()

        match key:
            case curses.KEY_DOWN:
                selected_option = (selected_option + 1) % len(saves)
            case curses.KEY_UP:
                selected_option = (selected_option - 1) % len(saves)
            case SpecialCode.ENTER:  # Touche entrée
                # Charger la partie sélectionnée
                load_existing_game(os.path.join(SAVE_DIR, saves[selected_option]))
                # Après chargement, lancez directement la partie avec curses
                game_loop_curses(stdscr)
                return  # Quitte la fonction après avoir lancé la boucle de jeu
            

def load_existing_game_graphics(screen, font):
    saves = list_saves()
    if not saves:
        render_text(screen, font, "[INFO] Aucune sauvegarde trouvée.", (20, 50))
        pygame.display.flip()
        time.sleep(2)
        return

    selected_option = 0
    running = True
    while running:
        screen.fill((0, 0, 0))
        render_text(screen, font, "Choisissez une sauvegarde à charger:", (20, 20))
        for i, save in enumerate(saves):
            color = (255, 255, 255) if i == selected_option else (100, 100, 100)
            render_text(screen, font, save, (20, 60 + i * 40), color)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(saves)
                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(saves)
                elif event.key == pygame.K_RETURN:
                    # Charger la partie sélectionnée
                    load_existing_game(os.path.join(SAVE_DIR, saves[selected_option]))
                    # Après chargement, lancez directement la boucle de jeu graphique
                    game_loop_graphics()
                    return  # Quitte la fonction après avoir lancé la boucle de jeu

def clear_input_buffer(stdscr):
    stdscr.nodelay(True)
    while True:
        key = stdscr.getch()
        if key == -1:
            break
    stdscr.nodelay(False)



def choose_player_side_curses(stdscr):
    """Menu de sélection du camp (J1 ou J2) en mode curses"""
    options = ["Jouer en tant que Joueur 1 (Bleu)", "Jouer en tant que Joueur 2 (Rouge)"]
    selected = 0
    
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "=== Choisissez votre camp ===")
        for i, option in enumerate(options):
            if i == selected:
                stdscr.addstr(i + 2, 0, option, curses.A_REVERSE)
            else:
                stdscr.addstr(i + 2, 0, option)
        stdscr.refresh()
        
        key = stdscr.getch()
        match key:
            case curses.KEY_DOWN:
                selected = (selected + 1) % 2
            case curses.KEY_UP:
                selected = (selected - 1) % 2
            case SpecialCode.ENTER:
                return 'J1' if selected == 0 else 'J2'  

def choose_player_side_graphics(screen, font):
    """Menu de sélection du camp (J1 ou J2) en mode graphique"""
    options     = ["Jouer en tant que Joueur 1 (Bleu)", "Jouer en tant que Joueur 2 (Rouge)"]
    selected    = 0
    running     = True
    
    while running:
        screen.fill((0, 0, 0))
        title = font.render("=== Choisissez votre camp ===", True, (255, 255, 255))
        screen.blit(title, (20, 50))
        
        for i, option in enumerate(options):
            color   = (255, 255, 255) if i == selected else (100, 100, 100)
            text    = font.render(option, True, color)
            screen.blit(text, (20, 120 + i * 50))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % 2
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % 2
                elif event.key == pygame.K_RETURN:
                    return 'J1' if selected == 0 else 'J2'


def signal_handler(sig, frame):
    Print_Display("[INFO] Exiting due to CTRL+C")
    curses.endwin()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def reset_curses():
    curses.endwin()
    time.sleep(0.1)
    sys.stdout.flush()

def reset_graphics():
    try:
        import pygame
        pygame.quit()
    except ImportError:
        pass
    time.sleep(0.1)

def switch_mode(new_mode):
    save_game_state(units, buildings, game_map, ai)
    if new_mode == 'graphics':
        reset_curses()
        game_loop_graphics()
    elif new_mode == 'terminal':
        reset_graphics()
        curses.wrapper(game_loop_curses)
        pygame.quit()  # Assure que Pygame est complètement fermé



#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------
#------Boucle de MAJ des events et des IA
#-------------------------------------------------------------------------------------
def update_game(units, buildings, game_map, ai, strategy, delay, last_update_time):
    """
    Met à jour le jeu en utilisant la stratégie spécifiée pour les actions IA.

    Args:
        units (list): Liste des unités du jeu.
        buildings (list): Liste des bâtiments du jeu.
        game_map (Map): Carte du jeu.
        ai (AI): L'objet représentant l'IA du ai.
        strategy (AIStrategy): Stratégie actuellement utilisée pour l'IA.
        delay (float): Délai minimum entre les mises à jour.
        last_update_time (float): Temps de la dernière mise à jour.
    
    Returns:
        float: Temps de la dernière mise à jour (actualisé si nécessaire).
    """
    current_time = time.time()
    if current_time - last_update_time > delay:
        # Utiliser la stratégie actuelle pour gérer les actions de l'IA
        strategy.execute(units, buildings, game_map, ai)
        return current_time
    return last_update_time

def send_game_state_to_c(network, units, buildings, ai, player_side):
    """Send current game state to C process"""
    
    try:
        # Send unit positions
        for unit in units:
            msg = f"UNIT_UPDATE|id:{id(unit)},type:{unit.unit_type},x:{unit.x},y:{unit.y},owner:{unit.owner}"
            network.send("UNIT_STATE", msg)
            #Print_Display(f"[DEBUG] Sent to C: {msg}")
        
        # Send resource information
        if ai and ai.resources:
            res_msg = f"wood:{ai.resources.get('Wood', 0)},gold:{ai.resources.get('Gold', 0)},food:{ai.resources.get('Food', 0)}"
            network.send("RESOURCES", res_msg)
            #Print_Display(f"[DEBUG] Sent to C: {res_msg}")
        
        # Send building information
        for building in buildings:
            bld_msg = f"type:{building.building_type},x:{building.x},y:{building.y},owner:{building.owner}"
            network.send("BUILDING_STATE", bld_msg)
            #Print_Display(f"[DEBUG] Sent to C: {bld_msg}")

    except Exception as e:
        Print_Display(f"[WARNING] Error sending game state to C: {str(e)}")

# def periodic_autosave(units, buildings, game_map, ai, current_time, last_save_time, save_interval=5.0):
#     """Check if it's time to autosave (every save_interval seconds)"""
#     try:
#         if current_time - last_save_time > save_interval:
#             save_game_state(units, buildings, game_map, ai, DEFAULT_SAVE)
#             return current_time
#     except Exception as e:
#         Print_Display(f"[WARNING] Autosave failed: {e}")
#     return last_save_time

def escape_menu_curses(stdscr):
    options = ["1. Sauvegarder", "2. Charger", "3. Reprendre", "4. Retour au Menu Principal", "5. Quitter"]
    selected_option = 0

    while True:
        stdscr.clear()
        for i, option in enumerate(options):
            if i == selected_option:
                stdscr.addstr(i, 0, option, curses.A_REVERSE)  # Option surlignée
            else:
                stdscr.addstr(i, 0, option)
        stdscr.refresh()

        key = stdscr.getch()
        match key:

            case curses.KEY_DOWN:
                selected_option = (selected_option + 1) % len(options)

            case curses.KEY_UP:
                selected_option = (selected_option - 1) % len(options)

            case 27:  # Touche Échap pour quitter le menu
                return  # Quitte le menu pour reprendre la partie

            case SpecialCode.ENTER:  # Touche entrée
                
                match selected_option:
                    case 0:  # Sauvegarder
                        clear_input_buffer(stdscr)
                        stdscr.addstr(5, 0, "Nom de la sauvegarde :")
                        stdscr.refresh()

                        save_name = ""
                        while True:
                            key = stdscr.getch()
                            if key == ord('\n'):
                                if save_name.strip() == "":
                                    stdscr.addstr(6, 0, "Erreur : le nom ne peut pas être vide.")
                                    stdscr.refresh()
                                    time.sleep(2)
                                else:
                                    break
                            elif key in [curses.KEY_BACKSPACE, 127]:
                                save_name = save_name[:-1]
                                stdscr.addstr(6, 0, " " * 20)  # Efface la ligne précédente
                                stdscr.addstr(6, 0, save_name)
                                stdscr.refresh()
                                
                            elif 32 <= key <= 126:  # Caractères imprimables uniquement
                                save_name += chr(key)
                                stdscr.addstr(6, 0, save_name)
                                stdscr.refresh()

                        try:
                            save_game_state(units, buildings, game_map, ai, os.path.join(SAVE_DIR, f"{save_name}.pkl"))
                        except Exception as e:
                            stdscr.addstr(7, 0, f"Erreur : {str(e)}")
                            stdscr.refresh()
                            time.sleep(2)

                    case 1:  # Charger
                        load_existing_game_curses(stdscr)
                        return  # Après chargement, lancez la boucle de jeu

                    case 2:  # Reprendre
                        return  # Quitte le menu et reprend la partie

                    case 3:  # Retour au Menu Principal
                        curses.wrapper(main_menu_curses_internal)
                        return

                    case 4:  # Quitter
                        sys.exit(0)





def input_text_pygame(screen, font, prompt):
    input_text = ""
    running = True

    while running:
        screen.fill((0, 0, 0))
        prompt_surface = font.render(prompt, True, (255, 255, 255))
        input_surface = font.render(input_text, True, (255, 255, 255))
        screen.blit(prompt_surface, (20, 50))
        screen.blit(input_surface, (20, 100))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_text.strip() != "":
                        return input_text
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key in (pygame.K_ESCAPE, pygame.K_F12):  # Échappe ou F12 pour annuler
                    return None
                elif 32 <= event.key <= 126:  # Caractères imprimables uniquement
                    input_text += event.unicode


def escape_menu_graphics(screen):
    font = pygame.font.Font(None, 36)
    options = ["1. Sauvegarder", "2. Charger", "3. Reprendre", "4. Retour au Menu Principal", "5. Quitter"]
    selected_option = 0
    running = True

    while running:
        screen.fill((0, 0, 0))
        for i, option in enumerate(options):
            color = (255, 255, 255) if i == selected_option else (100, 100, 100)
            text = font.render(option, True, color)
            screen.blit(text, (20, 50 + i * 40))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_ESCAPE:  # Touche Échap pour quitter le menu
                    running = False
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:  # Touche entrée
                    if selected_option == 0:  # Sauvegarder
                        save_name = input_text_pygame(screen, font, "Nom de la sauvegarde :")
                        if save_name:
                            save_game_state(units, buildings, game_map, ai, os.path.join(SAVE_DIR, f"{save_name}.pkl"))
                    elif selected_option == 1:  # Charger
                        load_existing_game_graphics(screen, font)
                        return  # Après chargement, lancez la boucle de jeu

                    elif selected_option == 2:  # Reprendre
                        running = False  # Quitte le menu et reprend la partie

                    elif selected_option == 3:  # Retour au Menu Principal
                        main_menu_graphics()
                        return

                    elif selected_option == 4:  # Quitter
                        sys.exit(0)


def game_loop_curses(stdscr):
    global network
    
    # Initialiser le network client s'il n'existe pas
    if network is None:
        try:
            network = NetworkClient(python_port=NETWORK_PYTHON_PORT, my_port=int(NETWORK_MY_PORT))
        except Exception as e:
            Print_Display(f"[ERROR] Échec de la connexion au processus C : {e}")
            return

    max_height, max_width   = stdscr.getmaxyx()
    max_height              = max_height - 10
    max_width               = int(max_width/2-20)
    view_x, view_y          = 0, 0

    stdscr.nodelay(True)
    stdscr.timeout(100)

    last_update_time        = time.time()
    last_save_time          = time.time()
    last_network_send_time  = time.time()

    init_colors()

    while True:

        network.poll()

        messages = network.consume_messages()
        for msg_type, payload in messages:
            if msg_type == "PING":
                Print_Display("[PING] {payload}")
            else:
                Print_Display(f"[{msg_type}] {payload}")

        current_time = time.time()

        # Accéder au côté du joueur
        Joueur = player_side_state.player_side  # Retourne 'J1' ou 'J2'

        # Gère les entrées utilisateur et affiche la carte en curses
        view_x, view_y = handle_input(stdscr, view_x, view_y, max_height, max_width, game_map)
        display_with_curses(stdscr, game_map, units, player_side_state, ai, view_x, view_y)
        last_update_time = update_game(units, buildings, game_map, ai, strategy=current_strategy, delay=0.01, last_update_time=last_update_time)
        
        # Send periodic updates to C process (every 0.5 seconds)
        current_time = time.time()
        if current_time - last_network_send_time > 0.5:
            send_game_state_to_c(network, units, buildings, ai, player_side_state.player_side)
            last_network_send_time = current_time
        
        # Auto-save game state (every 5 seconds)
        # last_save_time = periodic_autosave(units, buildings, game_map, ai, current_time, last_save_time, save_interval=5.0)

        key = stdscr.getch()
        if key == curses.KEY_F12:
            reset_curses()
            game_loop_graphics()
            break
        elif key == 27:  # Touche Échap pour ouvrir le menu
            escape_menu_curses(stdscr)

# Correction dans la fonction game_loop_graphics
def game_loop_graphics():
    global units, buildings, game_map, ai, game_state, network

    # Réutiliser le network existant s'il existe, sinon en créer un nouveau
    if network is None:
        try:
            network = NetworkClient(python_port=NETWORK_PYTHON_PORT, my_port=int(NETWORK_MY_PORT))
        except Exception as e:
            Print_Display(f"[ERROR] Échec de la connexion au processus C : {e}")
            return

    # Initialiser pygame pour le mode graphique
    screen = initialize_graphics()

    running = True
    clock = pygame.time.Clock()
    view_x, view_y = 0, 0
    max_width = screen_width // TILE_WIDTH
    max_height = screen_height // TILE_HEIGHT
    last_update_time = time.time()
    last_save_time = time.time()
    last_network_send_time = time.time()

    while running:
        current_time = time.time()

        network.poll()

        
        # Gère les entrées utilisateur pour le scrolling de la carte
        view_x, view_y = handle_input_pygame(view_x, view_y, max_width, max_height, game_map)
        
        # Mise à jour du jeu à intervalles réguliers
        last_update_time = update_game(units, buildings, game_map, ai, strategy=current_strategy, delay=0.01, last_update_time=last_update_time)
        
        # Send periodic updates to C process (every 0.5 seconds)
        if current_time - last_network_send_time > 0.5:
            send_game_state_to_c(network, units, buildings, ai, player_side_state.player_side)
            last_network_send_time = current_time
        
        # Auto-save game state (every 5 seconds)
        # last_save_time = periodic_autosave(units, buildings, game_map, ai, current_time, last_save_time, save_interval=5.0)

        # Rendu de la carte et des unités
        render_map(screen, game_map, units, buildings, player_side_state, view_x, view_y, max_width, max_height)


        # Gérer les événements Pygame (fermeture de fenêtre, bascule de mode, menu)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F12:
                    pygame.quit()
                    curses.wrapper(game_loop_curses)
                    return
                elif event.key == pygame.K_ESCAPE:
                    escape_menu_graphics(screen)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()



def main_menu_curses():
    curses.wrapper(main_menu_curses_internal)

def main_menu_curses_internal(stdscr):
    options = ["1. Charger une partie", "2. Continuer la dernière partie", "3. Nouvelle partie", "4. Quitter"]
    selected_option = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Menu Principal:")
        for i, option in enumerate(options):
            if i == selected_option:
                stdscr.addstr(i + 1, 0, option, curses.A_REVERSE)  # Option surlignée
            else:
                stdscr.addstr(i + 1, 0, option)
        stdscr.refresh()

        key = stdscr.getch()

        match key:

            case curses.KEY_DOWN:
                selected_option = (selected_option + 1) % len(options)

            case curses.KEY_UP:
                selected_option = (selected_option - 1) % len(options)

            case SpecialCode.ENTER:  # Touche entrée

                match selected_option:
                    case 0:  # Charger une partie
                        load_existing_game_curses(stdscr)

                    case 1:  # Continuer la dernière partie
                        loaded_units, loaded_buildings, loaded_map, loaded_ai = load_game_state(DEFAULT_SAVE)
                        if loaded_units and loaded_buildings and loaded_map and loaded_ai:
                            global units, buildings, game_map, ai
                            units, buildings, game_map, loaded_ai
                            curses.wrapper(game_loop_curses)

                    case 2:  # Nouvelle partie
                        start_new_game_curses(stdscr)

                    case 3:  # Quitter
                        sys.exit(0)

def start_new_game_curses(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Réglage de la nouvelle partie:")

    # Options configurables
    input_fields = [
        ("Taille de la carte (par défaut 120x120): ", "120"),
        ("Nombre de clusters de bois (par défaut 10): ", "10"),
        ("Nombre de clusters d'or (par défaut 4): ", "4"),
        ("Vitesse du jeu (par défaut 1.0): ", "1.0"),
        ("Port réseau (par défaut 5000): ", "5000"),
        ("Port pyhton (par défaut 5001): ", "5001"),
        ("Port distant (par défaut 6000): ", "6000")
    ]
    input_values = []

    curses.echo()
    for idx, (prompt, default) in enumerate(input_fields):
        stdscr.addstr(idx + 1, 0, prompt)
        stdscr.addstr(idx + 1, len(prompt), default)  # Affiche la valeur par défaut
        stdscr.move(idx + 1, len(prompt))  # Place le curseur à la bonne position

        value = ""
        while True:
            key = stdscr.getch()

            match key: 

                case SpecialCode.ENTER :  # Touche Entrée
                    if value.strip() == "":
                        value = default  # Si aucune entrée, utilise la valeur par défaut
                    break

                case curses.KEY_BACKSPACE | 127:  # Touche Backspace
                    value = value[:-1]
                    stdscr.addstr(idx + 1, len(prompt), " " * (len(value) + 10))  # Efface la ligne précédente
                    stdscr.addstr(idx + 1, len(prompt), value)
                    stdscr.move(idx + 1, len(prompt) + len(value))

                case _ if 32 <= key <= 126:  # Caractères imprimables uniquement
                    value += chr(key)
                    stdscr.addstr(idx + 1, len(prompt), value)
                    stdscr.move(idx + 1, len(prompt) + len(value))

        input_values.append(value)

    # Récupération des valeurs
    try:
        map_size        = int(input_values[0])
        wood_clusters   = int(input_values[1])
        gold_clusters   = int(input_values[2])
        speed           = float(input_values[3])
        my_port         = int(input_values[4])
        python_port     = int(input_values[5])
        dest_port       = int(input_values[6])

    except ValueError:
        stdscr.addstr(len(input_fields) + 2, 0, "Erreur : Entrée invalide, utilisation des valeurs par défaut.")
        stdscr.refresh()
        time.sleep(2)
        map_size        = 120
        wood_clusters   = 10
        gold_clusters   = 4
        speed           = 1.0
        my_port         = 5000
        python_port     = 5001
        dest_port       = 6000

    # Initialisation de la nouvelle partie
    global units, buildings, game_map, ai, player_side_state, NETWORK_MY_PORT, NETWORK_PYTHON_PORT, NETWORK_DEST_PORT
    
    NETWORK_MY_PORT     = my_port
    NETWORK_DEST_PORT   = dest_port
    NETWORK_PYTHON_PORT = python_port

    # Ask player to choose their side (J1 or J2)
    player_side_state.player_side = choose_player_side_curses(stdscr)

    seed = int(time.time())
    
    # Synchroniser la variable globale Joueur
    import model as model_module
    model_module.Joueur = player_side_state.player_side
    
    game_map    = Map(map_size, map_size)
    game_map.generate_forest_clusters(num_clusters=wood_clusters, cluster_size=40)
    game_map.generate_gold_clusters(num_clusters=gold_clusters)


    match player_side_state.player_side:
        
        case 'J1':
            starting_x, starting_y = 10, 10
            starting_x_V1, starting_y_V1 = 9, 9
            starting_x_V2, starting_y_V2 = 12, 9
            starting_x_V3, starting_y_V3 = 9, 12

        case 'J2':
            starting_x, starting_y = map_size - 10, map_size - 10
            starting_x_V1, starting_y_V1 = map_size - 11, map_size - 11
            starting_x_V2, starting_y_V2 = map_size - 8, map_size - 11
            starting_x_V3, starting_y_V3 = map_size - 11, map_size - 8

    town_center = Building('Town Center', starting_x, starting_y)
    game_map.place_building(town_center, starting_x, starting_y)
    
    # Création des unités avant l'IA
    villager1   = Unit('Villager', starting_x_V1, starting_y_V1, None)  # Créez l'unité sans AI pour l'instant
    villager2   = Unit('Villager', starting_x_V2, starting_y_V2, None)
    villager3   = Unit('Villager', starting_x_V3, starting_y_V3, None)
    units       = [villager1, villager2, villager3]
    buildings   = [town_center]

    # Créez l'instance de l'AI après avoir créé les unités
    ai = AI(buildings, units)

    # Mettre à jour les unités avec l'instance correcte de l'IA
    for unit in units:
        unit.ai = ai
    
    # Set the player AI in game state
    player_side_state.set_player_ai(ai)

    # Initialiser la communication réseau
    NET_ME      = str(my_port)
    NET_DEST    = str(dest_port)
    PY_PORT     = str(python_port)
    GAMEP2P_EXE = "./network/GameP2P.exe"
    try:
        bridge_proc = subprocess.Popen([GAMEP2P_EXE, NET_ME, NET_DEST, PY_PORT])
        time.sleep(0.5)
        Print_Display(f"[INFO] Lancement du processus réseau C : {GAMEP2P_EXE} {NET_ME} {NET_DEST} {PY_PORT}")
    except Exception as e:
        Print_Display(f"[ERROR] Échec du lancement du processus réseau C : {e}")

    # Lancer la boucle de jeu avec curses
    curses.wrapper(game_loop_curses)


def main_menu_graphics():
    pygame.init()
    screen          = pygame.display.set_mode((screen_width, screen_height))
    font            = pygame.font.Font(None, 36)
    options         = ["1. Charger une partie", "2. Continuer la dernière partie", "3. Nouvelle partie", "4. Quitter"]
    selected_option = 0
    running     = True

    while running:
        screen.fill((0, 0, 0))
        for i, option in enumerate(options):
            color = (255, 255, 255) if i == selected_option else (100, 100, 100)
            text = font.render(option, True, color)
            screen.blit(text, (20, 50 + i * 40))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if selected_option == 0:  # Charger une partie
                        load_existing_game_graphics(screen, font)
                    elif selected_option == 1:  # Continuer la dernière partie
                        loaded_units, loaded_buildings, loaded_map, loaded_ai = load_game_state(DEFAULT_SAVE)
                        if loaded_units and loaded_buildings and loaded_map and loaded_ai:
                            global units, buildings, game_map, ai
                            units, buildings, game_map, ai = loaded_units, loaded_buildings, loaded_map, loaded_ai
                            game_loop_graphics()
                    elif selected_option == 2:  # Nouvelle partie
                        start_new_game_graphics(screen, font)
                    elif selected_option == 3:  # Quitter
                        sys.exit(0)

def start_new_game_graphics(screen, font):
    input_fields = [
        ("Taille de la carte (par défaut 120x120): ", "120"),
        ("Nombre de clusters de bois (par défaut 10): ", "10"),
        ("Nombre de clusters d'or (par défaut 4): ", "4"),
        ("Vitesse du jeu (par défaut 1.0): ", "1.0")
    ]
    input_values = []

    # Pour chaque champ de saisie
    for idx, (prompt, default) in enumerate(input_fields):
        input_text = default
        running    = True
        while running:
            screen.fill((0, 0, 0))
            prompt_surface  = font.render(prompt, True, (255, 255, 255))
            input_surface   = font.render(input_text, True, (255, 255, 255))
            screen.blit(prompt_surface, (20, 50 + idx * 60))
            screen.blit(input_surface, (20, 100 + idx * 60))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        running = False  # Terminer la saisie du champ actuel
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key in (pygame.K_ESCAPE, pygame.K_F12):
                        return  # Retourne au menu principal sans rien faire
                    elif 32 <= event.key <= 126:  # Caractères imprimables uniquement
                        input_text += event.unicode

        input_values.append(input_text)

    # Une fois les valeurs saisies, afficher le bouton "Lancer la Partie"
    launch_button_selected = True
    running = True
    while running:
        screen.fill((0, 0, 0))
        # Affiche les valeurs saisies
        for idx, (prompt, value) in enumerate(zip([f[0] for f in input_fields], input_values)):
            prompt_surface = font.render(f"{prompt} {value}", True, (255, 255, 255))
            screen.blit(prompt_surface, (20, 50 + idx * 60))

        # Affiche le bouton "Lancer la Partie"
        button_color = (255, 255, 0) if launch_button_selected else (100, 100, 100)
        button_text = font.render("Lancer la Partie", True, button_color)
        screen.blit(button_text, (20, 100 + len(input_fields) * 60))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and launch_button_selected:
                    running = False  # Lancer la partie
                elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    launch_button_selected = not launch_button_selected
                elif event.key in (pygame.K_ESCAPE, pygame.K_F12):
                    return  # Retourne au menu principal sans rien faire

    # Récupération des valeurs et lancement de la partie
    try:
        map_size = int(input_values[0])
        wood_clusters = int(input_values[1])
        gold_clusters = int(input_values[2])
        speed = float(input_values[3])
    except ValueError:
        # En cas d'erreur de saisie, utiliser les valeurs par défaut
        map_size = 120
        wood_clusters = 10
        gold_clusters = 4
        speed = 1.0

    # Initialisation de la nouvelle partie
    global units, buildings, game_map, ai, player_side_state
    
    # Ask player to choose their side (J1 or J2)
    player_side_state.player_side = choose_player_side_graphics(screen, font)
    
    # Synchroniser la variable globale Joueur
    import model as model_module
    model_module.Joueur = player_side_state.player_side
    
    seed = int(time.time())
    game_map = Map(map_size, map_size, seed)
    game_map.generate_forest_clusters(num_clusters=10, cluster_size=40)
    game_map.generate_gold_clusters(num_clusters=4)
    match player_side_state.player_side:
        case 'J1':
            starting_x, starting_y = 10, 10
            starting_x_V1, starting_y_V1 = 9, 9
            starting_x_V2, starting_y_V2 = 12, 9
            starting_x_V3, starting_y_V3 = 9, 12
        case 'J2':
            starting_x, starting_y = map_size - 10, map_size - 10
            starting_x_V1, starting_y_V1 = map_size - 11, map_size - 11
            starting_x_V2, starting_y_V2 = map_size - 8, map_size - 11
            starting_x_V3, starting_y_V3 = map_size - 11, map_size - 8

    town_center = Building('Town Center', starting_x, starting_y)
    game_map.place_building(town_center, starting_x, starting_y)
    ai = AI(buildings, units)  # Initialisation de l'objet AI
    villager = Unit('Villager', starting_x_V1, starting_y_V1, ai)
    villager2 = Unit('Villager', starting_x_V2, starting_y_V2, ai)
    villager3 = Unit('Villager', starting_x_V3, starting_y_V3, ai)
    units = [villager, villager2, villager3]
    buildings = [town_center]
    ai = AI(ai, buildings, units)  # Passage de l'objet ai à l'IA
    
    # Set the player AI in game state
    player_side_state.set_player_ai(ai)

    # Envoi du seed et des infos map au réseau si nécessaire
    try:
        import network
        network.send(game_map.to_network_message())
    except Exception:
        pass  # Le réseau peut ne pas être initialisé

    # Lancer la boucle de jeu graphique
    game_loop_graphics()

def render_text(screen, font, text, position, color=(255, 255, 255)):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)



def init_game():
    global units, buildings, game_map, ai, player_side_state
    player_side_state.player_side = 'J1'  # Set player side (default J1)
    os.makedirs(SAVE_DIR, exist_ok=True)
    loaded_units, loaded_buildings, loaded_map, loaded_ai = load_game_state(DEFAULT_SAVE)
    if loaded_units and loaded_buildings and loaded_map and loaded_ai:
        units, buildings, game_map, ai = loaded_units, loaded_buildings, loaded_map, loaded_ai
    else:
        seed        = int(time.time())  # pour générer la même map des deux côtés
        game_map    = Map(120, 120, seed)
        game_map.generate_forest_clusters(num_clusters=10, cluster_size=40)
        game_map.generate_gold_clusters(num_clusters=4)
        
        match player_side_state.player_side:

            case 'J1':
                town_center = Building('Town Center', 10, 10)
                game_map.place_building(town_center, 10, 10)
                aiJ1        = AI(buildings, units)  # Initialisation de l'objet AI
                villager    = Unit('Villager', 9, 9, aiJ1)
                villager2   = Unit('Villager', 12, 9, aiJ1)
                villager3   = Unit('Villager', 9, 12, aiJ1)
                units       = [villager, villager2, villager3]
                buildings   = [town_center]
                aiJ1        = AI(aiJ1, buildings, units)  # Passage de l'objet ai à l'IA

            case 'J2':
                town_center = Building('Town Center', 110, 110)
                game_map.place_building(town_center, 110, 110)
                aiJ2        = AI(buildings, units)  # Initialisation de l'objet AI
                villager    = Unit('Villager', 109, 109, aiJ2)
                villager2   = Unit('Villager', 112, 109, aiJ2)
                villager3   = Unit('Villager', 109, 112, aiJ2)
                units       = [villager, villager2, villager3]
                buildings   = [town_center]
                aiJ2        = AI(aiJ2, buildings, units)  # Passage de l'objet ai à l'IA

        network.send(game_map.to_network_message())
        
        # Set the player AI in game state
        #player_side_state.set_player_ai(ai)



class NetworkClient:
    def __init__(self, python_port, my_port):
        self.python_port    = python_port
        self.bridge_port    = my_port
        
        self.connected      = False
        self.inbox          = []
        self.last_msg_time  = time.time()
        
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
                msg     = data.decode().strip()
                
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
            pass # Rien à lire
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


def main():
    # Ne pas initialiser pygame à moins que le mode graphique soit spécifié
    if 'graphics' in sys.argv:
        main_menu_graphics()
    else:
        main_menu_curses()

if __name__ == "__main__":
    main()
