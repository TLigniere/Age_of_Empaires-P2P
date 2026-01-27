import curses
import time
import os
import pygame
import subprocess
import sys
import signal
from model import Map, Unit, Building
from view import display_with_curses, handle_input, init_colors, Print_Display
from view_graphics import handle_input_pygame, render_map, screen_width, screen_height, TILE_WIDTH, TILE_HEIGHT, initialize_graphics
from game_utils import save_game_state, load_game_state
import socket
import time
from datetime import datetime

import select
import json 


from ai_strategies.base_strategies import AI

from ai_strategies.strategie_No1_dev_ai import StrategieNo1  # Importer la stratégie spécifique
# Création de la stratégie choisie
current_strategy = StrategieNo1()

# Utilisation de la stratégie dans update_game
last_update_time = 0  # Initialiser last_update_time avant la boucle principale du jeu



# ========== EVENT LOGGING SYSTEM ==========
class EventLogger:
    """Centralized event logging for P2P synchronization"""
    def __init__(self, player_side):
        self.player_side = player_side
        self.events = []
    
    def log_event(self, event_type, data):
        """Log a game event with timestamp"""
        timestamp = datetime.now().isoformat()
        event = {
            'type': event_type,
            'player': self.player_side,
            'timestamp': timestamp,
            'data': data
        }
        self.events.append(event)
        return event
    
    def log_unit_movement(self, unit_id, x, y):
        return self.log_event('UNIT_MOVE', {'unit_id': unit_id, 'x': x, 'y': y})
    
    def log_building_construction(self, building_type, x, y):
        return self.log_event('BUILDING_CONSTRUCT', {'type': building_type, 'x': x, 'y': y})
    
    def log_resource_gathering(self, resource_type, amount):
        return self.log_event('RESOURCE_GATHER', {'resource': resource_type, 'amount': amount})
    
    def log_unit_creation(self, unit_type, x, y):
        return self.log_event('UNIT_CREATE', {'type': unit_type, 'x': x, 'y': y})
    
    def log_attack(self, attacker_id, target_id):
        return self.log_event('ATTACK', {'attacker': attacker_id, 'target': target_id})
    
    def get_events(self):
        """Get all logged events"""
        return self.events
    
    def clear_events(self):
        """Clear logged events"""
        self.events = []

# ========== ENHANCED NETWORK CLIENT FOR P2P (via C process) ==========
class P2PNetworkClient:
    """P2P Network Client that routes events through C process"""
    def __init__(self, network_client, player_side='J1'):
        """
        Initialize P2P client using existing C process connection
        
        Args:
            network_client: Existing NetworkClient instance connected to C process
            player_side: 'J1' or 'J2'
        """
        self.network_client = network_client
        self.player_side = player_side
        self.event_logger = EventLogger(player_side)
        self.inbox = []
        
        Print_Display(f"[P2P] Client {player_side} configured to route through C process", Color=2)
    
    def poll(self):
        """Poll for messages from C process"""
        if not self.network_client:
            return
        
        # Poll the underlying network client
        self.network_client.poll()
        
        # Get messages from C process
        messages = self.network_client.consume_messages()
        
        for msg_type, payload in messages:
            # Check if this is an event from the opponent
            if msg_type in ['UNIT_MOVE', 'BUILDING_CONSTRUCT', 'UNIT_CREATE', 'RESOURCE_GATHER', 'ATTACK']:
                try:
                    # Parse the event from C process
                    event_data = json.loads(payload) if isinstance(payload, str) else payload
                    
                    # Only add if it's from the other player
                    if event_data.get('player') != self.player_side:
                        self.inbox.append(event_data)
                except (json.JSONDecodeError, TypeError):
                    pass
    
    def send_event(self, event):
        """Send an event through C process to opponent"""
        if not self.network_client or not self.network_client.connected:
            Print_Display(f"[P2P] ⚠️  Not connected to C process", Color=1)
            return
        
        try:
            msg = json.dumps(event)
            # Send to C process as JSON
            event_type = event.get('type', 'EVENT')
            self.network_client.send(event_type, msg)
        except Exception as e:
            Print_Display(f"[P2P] Erreur d'envoi via C: {e}", Color=1)
    
    def consume_events(self):
        """Get all received events from opponent"""
        events = self.inbox[:]
        self.inbox.clear()
        return events
    
    def log_and_send(self, event_type, data):
        """Log an event locally and send through C process"""
        event = self.event_logger.log_event(event_type, data)
        self.send_event(event)
        return event


# Constants

SAVE_DIR = "saves"
DEFAULT_SAVE = os.path.join(SAVE_DIR, "default_game.pkl")
GAME_PLAYING = "PLAYING"
GAME_PAUSED = "PAUSED"

# ========== NETWORK CONFIGURATION ==========
# Set to True when you have the C process running
# Set to False for local testing without C process
ENABLE_NETWORK = False
ENABLE_P2P = False  # Set to True for P2P multiplayer mode

# P2P Configuration Variables
P2P_MY_PORT = 5000
P2P_OPPONENT_PORT = 5001
P2P_OPPONENT_HOST = '127.0.0.1'
P2P_PLAYER_SIDE = 'J1'  # Will be overridden by command line args

# Legacy Network Configuration Variables
NETWORK_PYTHON_PORT = 5001
NETWORK_MY_PORT = 5000
NETWORK_DEST_PORT = 6000

# Parse command line arguments for P2P mode
def parse_p2p_arguments():
    """Parse command line arguments for P2P multiplayer"""
    global ENABLE_P2P, P2P_PLAYER_SIDE, P2P_MY_PORT, P2P_OPPONENT_PORT
    
    for i, arg in enumerate(sys.argv[1:]):
        if arg == '--p2p':
            ENABLE_P2P = True
        elif arg == '--player' and i + 1 < len(sys.argv):
            player = sys.argv[i + 2]
            if player in ['J1', 'J2']:
                P2P_PLAYER_SIDE = player
        elif arg == '--my-port' and i + 1 < len(sys.argv):
            try:
                P2P_MY_PORT = int(sys.argv[i + 2])
            except ValueError:
                pass
        elif arg == '--opponent-port' and i + 1 < len(sys.argv):
            try:
                P2P_OPPONENT_PORT = int(sys.argv[i + 2])
            except ValueError:
                pass
        elif arg == '--opponent-host' and i + 1 < len(sys.argv):
            P2P_OPPONENT_HOST = sys.argv[i + 2]

# Parse arguments at startup
parse_p2p_arguments()
# ==========================================

# Simple GameState object to track player_side and AI resources
class GameState:
    def __init__(self):
        self.player_side = 'J1'  # Default to J1
        self.player_ai = None  # Will be set later
        
    def set_player_ai(self, ai_obj):
        self.player_ai = ai_obj

# Global game variables - Player 1
player_side_state = GameState()
units = []
buildings = []
game_map = None
ai = None

# Global game variables - Player 2 (Enemy)
enemy_units = []
enemy_buildings = []
enemy_ai = None

# Global Variables
units, buildings, game_map, ai = None, None, None, None
game_state = GAME_PLAYING
player_side_state = GameState()  # Track player side

# Network Configuration Variables
NETWORK_PYTHON_PORT = 5001
NETWORK_MY_PORT = 5000
NETWORK_DEST_PORT = 6000

class GameElement:
    def __init__(self, id, owner=None):
        self.id = id
        self.owner = owner        # Joueur qui possède cet élément (propriété métier)
        self.network_owner = owner  # Joueur qui contrôle cet élément pour le réseau
        self.state = {}           # État de l’élément (ex: mur endommagé, ressources)

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
        if key == curses.KEY_DOWN:
            selected_option = (selected_option + 1) % len(saves)
        elif key == curses.KEY_UP:
            selected_option = (selected_option - 1) % len(saves)
        elif key == ord('\n'):  # Touche entrée
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
                    game_loop_graphics(player_side_state.player_side)
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
        if key == curses.KEY_DOWN:
            selected = (selected + 1) % 2
        elif key == curses.KEY_UP:
            selected = (selected - 1) % 2
        elif key == ord('\n'):
            return 'J1' if selected == 0 else 'J2'


def choose_player_side_graphics(screen, font):
    """Menu de sélection du camp (J1 ou J2) en mode graphique"""
    options = ["Jouer en tant que Joueur 1 (Bleu)", "Jouer en tant que Joueur 2 (Rouge)"]
    selected = 0
    running = True
    
    while running:
        screen.fill((0, 0, 0))
        title = font.render("=== Choisissez votre camp ===", True, (255, 255, 255))
        screen.blit(title, (20, 50))
        
        for i, option in enumerate(options):
            color = (255, 255, 255) if i == selected else (100, 100, 100)
            text = font.render(option, True, color)
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
        game_loop_graphics(player_side_state.player_side)
    elif new_mode == 'terminal':
        reset_graphics()
        curses.wrapper(game_loop_curses)
        pygame.quit()  # Assure que Pygame est complètement fermé



#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------
#------Boucle de MAJ des events et des IA
#-------------------------------------------------------------------------------------
def update_game(units, buildings, game_map, ai, enemy_units, enemy_buildings, enemy_ai, strategy, delay, last_update_time):
    """
    Met à jour le jeu en utilisant la stratégie spécifiée pour les actions IA.

    Args:
        units (list): Liste des unités du joueur.
        buildings (list): Liste des bâtiments du joueur.
        game_map (Map): Carte du jeu.
        ai (AI): L'objet représentant l'IA du joueur.
        enemy_units (list): Liste des unités de l'ennemi.
        enemy_buildings (list): Liste des bâtiments de l'ennemi.
        enemy_ai (AI): L'IA de l'ennemi.
        strategy (AIStrategy): Stratégie actuellement utilisée pour l'IA.
        delay (float): Délai minimum entre les mises à jour.
        last_update_time (float): Temps de la dernière mise à jour.
    
    Returns:
        float: Temps de la dernière mise à jour (actualisé si nécessaire).
    """
    current_time = time.time()
    if current_time - last_update_time > delay:
        # Update player 1 AI
        strategy.execute(units, buildings, game_map, ai)
        # Update enemy AI only if it exists (not in P2P mode where enemy is real player)
        if enemy_ai is not None:
            strategy.execute(enemy_units, enemy_buildings, game_map, enemy_ai)
        return current_time
    return last_update_time

def send_game_state_to_c(network, units, buildings, ai, player_side):
    """Send current game state to C process"""
    if not network.connected:
        return
    
    try:
        # Send unit positions
        for unit in units:
            msg = f"UNIT_UPDATE|id:{id(unit)},type:{unit.unit_type},x:{unit.x},y:{unit.y},owner:{unit.owner}"
            network.send_to_c("UNIT_STATE", msg)
        
        # Send resource information
        if ai and ai.resources:
            res_msg = f"wood:{ai.resources.get('Wood', 0)},gold:{ai.resources.get('Gold', 0)},food:{ai.resources.get('Food', 0)}"
            network.send_to_c("RESOURCES", res_msg)
        
        # Send building information
        for building in buildings:
            bld_msg = f"type:{building.building_type},x:{building.x},y:{building.y},owner:{building.owner}"
            network.send_to_c("BUILDING_STATE", bld_msg)
    except Exception as e:
        Print_Display(f"[WARNING] Error sending game state to C: {str(e)}")


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
        if key == curses.KEY_DOWN:
            selected_option = (selected_option + 1) % len(options)
        elif key == curses.KEY_UP:
            selected_option = (selected_option - 1) % len(options)
        elif key == ord('\n'):  # Touche entrée
            if selected_option == 0:  # Sauvegarder
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

            elif selected_option == 1:  # Charger
                load_existing_game_curses(stdscr)
                return  # Après chargement, lancez la boucle de jeu

            elif selected_option == 2:  # Reprendre
                return  # Quitte le menu et reprend la partie

            elif selected_option == 3:  # Retour au Menu Principal
                curses.wrapper(main_menu_curses_internal)
                return

            elif selected_option == 4:  # Quitter
                sys.exit(0)

        elif key == 27:  # Touche Échap pour quitter le menu
            return  # Quitte le menu pour reprendre la partie



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
    global units, buildings, game_map, ai, game_state, NETWORK_PYTHON_PORT, NETWORK_MY_PORT, enemy_units, enemy_buildings, enemy_ai

    # Initialize network (C process) - required for both ENABLE_NETWORK and ENABLE_P2P
    network = None
    if ENABLE_NETWORK or ENABLE_P2P:
        network = NetworkClient(python_port=NETWORK_PYTHON_PORT, my_port=NETWORK_MY_PORT)
        # Passer la référence du network à la stratégie
        if ENABLE_NETWORK:
            current_strategy.set_network(network)
    
    # Initialize P2P network if enabled (using C process)
    p2p_network = None
    if ENABLE_P2P:
        if not network:
            Print_Display("[P2P] Erreur: C process non connecté. Activez ENABLE_NETWORK", Color=1)
        p2p_network = P2PNetworkClient(network_client=network, player_side=P2P_PLAYER_SIDE)

    max_height, max_width = stdscr.getmaxyx()
    max_height = max_height - 10
    max_width = int(max_width/2-20)
    view_x, view_y = 0, 0

    stdscr.nodelay(True)
    stdscr.timeout(100)

    last_update_time = time.time()
    last_network_send_time = time.time()

    init_colors()

    while True:

        # Handle P2P network if enabled
        if ENABLE_P2P and p2p_network:
            p2p_network.poll()
            received_events = p2p_network.consume_events()
            for event in received_events:
                Print_Display(f"[{event.get('player')}] {event.get('type')}: {event.get('data')}", Color=3)

        # Handle network polling if enabled
        if ENABLE_NETWORK and network:
            network.poll()
            # Traiter et afficher les messages reçus du réseau
            messages = network.consume_messages()
            for msg_type, payload in messages:
                if msg_type == "PING":
                    Print_Display(f"[PING REÇU] {payload}", Color=2)
                else:
                    Print_Display(f"[{msg_type}] {payload}", Color=3)

        current_time = time.time()

        # Gère les entrées utilisateur et affiche la carte en curses
        view_x, view_y = handle_input(stdscr, view_x, view_y, max_height, max_width, game_map)
        display_with_curses(stdscr, game_map, units, player_side_state, ai, view_x, view_y)
        # Update both player 1 and enemy AI
        last_update_time = update_game(units, buildings, game_map, ai, enemy_units, enemy_buildings, enemy_ai, strategy=current_strategy, delay=0.01, last_update_time=last_update_time)
        
        # Send periodic updates to C process (every 0.5 seconds)
        current_time = time.time()
        if ENABLE_NETWORK and network and current_time - last_network_send_time > 0.5:
            send_game_state_to_c(network, units, buildings, ai, player_side_state.player_side)
            last_network_send_time = current_time

        key = stdscr.getch()
        if key == curses.KEY_F12:
            # ← REMOVED nested call - just exit loop and return
            break
        elif key == 27:  # Touche Échap pour ouvrir le menu
            escape_menu_curses(stdscr)

# Correction dans la fonction game_loop_graphics
def game_loop_graphics(player_side=None):
    global units, buildings, game_map, ai, game_state, enemy_units, enemy_buildings, enemy_ai, player_side_state

    # Initialize network connection (C process)
    network = NetworkClient(python_port=NETWORK_PYTHON_PORT, my_port=NETWORK_MY_PORT) if ENABLE_NETWORK or ENABLE_P2P else None
    
    # Initialize P2P network if enabled (using C process)
    p2p_network = None
    received_events = []
    if ENABLE_P2P:
        if not network:
            Print_Display("[P2P] Erreur: C process non connecté. Activez ENABLE_NETWORK", Color=1)
        p2p_network = P2PNetworkClient(network_client=network, player_side=P2P_PLAYER_SIDE)
        player_side_state.player_side = P2P_PLAYER_SIDE
        player_side = P2P_PLAYER_SIDE
    
    # Passer la référence du network à la stratégie
    if ENABLE_NETWORK and network:
        current_strategy.set_network(network)

    # Initialiser pygame pour le mode graphique
    screen = initialize_graphics()

    running = True
    clock = pygame.time.Clock()
    
    # Set initial camera position based on player side
    if player_side == 'J1':
        # Focus on Player 1's town center at (10, 10)
        view_x, view_y = 10, 10
    elif player_side == 'J2':
        # Focus on Player 2's town center at (110, 110)
        view_x, view_y = 110, 110
    else:
        # Default to top-left if no player side specified
        view_x, view_y = 0, 0
    
    max_width = screen_width // TILE_WIDTH
    max_height = screen_height // TILE_HEIGHT
    last_update_time = time.time()
    last_network_send_time = time.time()

    while running:
        current_time = time.time()

        # Handle P2P network if enabled
        if ENABLE_P2P and p2p_network:
            p2p_network.poll()
            received_events = p2p_network.consume_events()
            for event in received_events:
                Print_Display(f"[{event.get('player')}] {event.get('type')}: {event.get('data')}", Color=3)

        # Handle network if enabled
        if ENABLE_NETWORK and network:
            network.poll()
            # Traiter et afficher les messages reçus du réseau
            messages = network.consume_messages()
            for msg_type, payload in messages:
                if msg_type == "PING":
                    Print_Display(f"[PING REÇU] {payload}", Color=2)
                else:
                    Print_Display(f"[{msg_type}] {payload}", Color=3)
        
        # Gère les entrées utilisateur pour le scrolling de la carte
        view_x, view_y = handle_input_pygame(view_x, view_y, max_width, max_height, game_map)
        
        # Mise à jour du jeu à intervalles réguliers - update both players
        last_update_time = update_game(units, buildings, game_map, ai, enemy_units, enemy_buildings, enemy_ai, strategy=current_strategy, delay=0.01, last_update_time=last_update_time)
        
        # Send periodic updates to C process (every 0.5 seconds)
        if ENABLE_NETWORK and network and current_time - last_network_send_time > 0.5:
            send_game_state_to_c(network, units, buildings, ai, player_side_state.player_side)
            last_network_send_time = current_time

        # Rendu de la carte et des unités - render both players' entities
        render_map(screen, game_map, units + enemy_units, buildings + enemy_buildings, player_side_state, view_x, view_y, max_width, max_height)

        # Gérer les événements Pygame (fermeture de fenêtre, bascule de mode, menu)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F12:
                    # ← FIXED: Just exit loop, don't call curses.wrapper again
                    running = False
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
        if key == curses.KEY_DOWN:
            selected_option = (selected_option + 1) % len(options)
        elif key == curses.KEY_UP:
            selected_option = (selected_option - 1) % len(options)
        elif key == ord('\n'):  # Touche entrée
            if selected_option == 0:  # Charger une partie
                load_existing_game_curses(stdscr)
            elif selected_option == 1:  # Continuer la dernière partie
                loaded_units, loaded_buildings, loaded_map, loaded_ai = load_game_state(DEFAULT_SAVE)
                if loaded_units and loaded_buildings and loaded_map and loaded_ai:
                    global units, buildings, game_map, ai
                    units, buildings, game_map, loaded_ai
                    curses.wrapper(game_loop_curses)
            elif selected_option == 2:  # Nouvelle partie
                start_new_game_curses(stdscr)
            elif selected_option == 3:  # Quitter
                sys.exit(0)

def start_new_game_curses(stdscr):
    """Démarre une nouvelle partie avec les paramètres par défaut"""
    # Utiliser les valeurs par défaut
    map_size = 120
    wood_clusters = 10
    gold_clusters = 4
    speed = 1.0
    my_port = NETWORK_MY_PORT
    python_port = NETWORK_PYTHON_PORT
    dest_port = NETWORK_DEST_PORT

    # Initialisation de la nouvelle partie
    global units, buildings, game_map, ai, player_side_state, enemy_units, enemy_buildings, enemy_ai
    
    # Ask player to choose their side (J1 or J2)
    player_side_state.player_side = choose_player_side_curses(stdscr)
    
    game_map = Map(map_size, map_size)
    game_map.generate_forest_clusters(num_clusters=wood_clusters, cluster_size=40)
    game_map.generate_gold_clusters(num_clusters=gold_clusters)
    
    # ===== PLAYER 1 (Human) =====
    town_center_p1 = Building('Town Center', 10, 10, owner='J1')
    game_map.place_building(town_center_p1, 10, 10)
    
    # Création des unités du joueur avant l'IA
    villager1_p1 = Unit('Villager', 9, 9, None, owner='J1')
    villager2_p1 = Unit('Villager', 12, 9, None, owner='J1')
    villager3_p1 = Unit('Villager', 9, 12, None, owner='J1')
    units = [villager1_p1, villager2_p1, villager3_p1]
    buildings = [town_center_p1]

    # Créez l'instance de l'AI pour le joueur après avoir créé les unités
    ai = AI(buildings, units)

    # Mettre à jour les unités avec l'instance correcte de l'IA
    for unit in units:
        unit.ai = ai
    
    # Set the player AI in game state
    player_side_state.set_player_ai(ai)
    
    # ===== PLAYER 2 (Enemy/AI) =====
    # Place enemy town center on the opposite side of the map
    town_center_p2 = Building('Town Center', map_size - 10, map_size - 10, owner='J2')
    game_map.place_building(town_center_p2, map_size - 10, map_size - 10)
    
    # Create enemy units
    villager1_p2 = Unit('Villager', map_size - 11, map_size - 11, None, owner='J2')
    villager2_p2 = Unit('Villager', map_size - 8, map_size - 11, None, owner='J2')
    villager3_p2 = Unit('Villager', map_size - 11, map_size - 8, None, owner='J2')
    enemy_units = [villager1_p2, villager2_p2, villager3_p2]
    enemy_buildings = [town_center_p2]
    
    # Create enemy AI
    enemy_ai = AI(enemy_buildings, enemy_units)
    
    # Update enemy units with enemy AI
    for unit in enemy_units:
        unit.ai = enemy_ai

    Print_Display("[INFO] Nouvelle partie créée avec succès")
    time.sleep(1)
    
    # Launch network subprocess if enabled (optional for local testing)
    if ENABLE_NETWORK:
        PY_PORT = str(python_port)
        GAMEP2P_EXE = "./network/GameP2P.exe"
        try:
            bridge_proc = subprocess.Popen([GAMEP2P_EXE, str(my_port), str(dest_port), PY_PORT])
            time.sleep(0.5)
            print(f"[INFO] Lancement du processus réseau C : {GAMEP2P_EXE} {my_port} {dest_port} {PY_PORT}")
        except Exception as e:
            Print_Display(f"[WARNING] Impossible de lancer le réseau: {e}")

    # Lancer la boucle de jeu avec gestion du basculement terminal/graphique
    game_loop_with_mode_switching()


def game_loop_with_mode_switching():
    """
    Manages the game loop with proper view switching between terminal and graphics modes.
    Uses a single curses session that persists across mode switches.
    """
    global units, buildings, game_map, ai, player_side_state, enemy_units, enemy_buildings, enemy_ai
    
    # Initialize curses once for the entire session
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    
    try:
        current_mode = 'terminal'  # Start in terminal mode
        
        while True:
            if current_mode == 'terminal':
                # Run terminal mode with existing curses session
                try:
                    game_loop_curses(stdscr)
                    # After terminal loop exits, switch to graphics if F12 was pressed
                    current_mode = 'graphics'
                except Exception as e:
                    Print_Display(f"[ERROR] Terminal mode error: {e}", Color=1)
                    break
            elif current_mode == 'graphics':
                # Run graphics mode (temporarily leaves curses)
                try:
                    game_loop_graphics(player_side_state.player_side)
                    # After graphics loop exits, switch back to terminal
                    current_mode = 'terminal'
                except Exception as e:
                    Print_Display(f"[ERROR] Graphics mode error: {e}", Color=1)
                    break
            else:
                break
    finally:
        # Clean up curses on exit
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()


def main_menu_graphics():
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    font = pygame.font.Font(None, 36)
    options = ["1. Charger une partie", "2. Continuer la dernière partie", "3. Nouvelle partie", "4. Quitter"]
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
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if selected_option == 0:  # Charger une partie
                        load_existing_game_graphics(screen, font)
                    elif selected_option == 1:  # Continuer la dernière partie
                        loaded_units, loaded_buildings, loaded_map, loaded_ai = load_game_state(DEFAULT_SAVE)
                        if loaded_units and loaded_buildings and loaded_map and loaded_ai:
                            global units, buildings, game_map, ai
                            units, buildings, game_map, ai = loaded_units, loaded_buildings, loaded_map, loaded_ai
                            game_loop_graphics(player_side_state.player_side)
                    elif selected_option == 2:  # Nouvelle partie
                        start_new_game_graphics(screen, font)
                    elif selected_option == 3:  # Quitter
                        sys.exit(0)

def start_new_game_graphics(screen, font):
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

    # Pour chaque champ de saisie
    for idx, (prompt, default) in enumerate(input_fields):
        input_text = default
        running = True
        while running:
            screen.fill((0, 0, 0))
            prompt_surface = font.render(prompt, True, (255, 255, 255))
            input_surface = font.render(input_text, True, (255, 255, 255))
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
    global units, buildings, game_map, ai, player_side_state, enemy_units, enemy_buildings, enemy_ai
    
    # Ask player to choose their side (J1 or J2)
    player_side_state.player_side = choose_player_side_graphics(screen, font)
    
    game_map = Map(120, 120)
    game_map.generate_forest_clusters(num_clusters=10, cluster_size=40)
    game_map.generate_gold_clusters(num_clusters=4)
    
    # ===== PLAYER 1 (Human) =====
    town_center_p1 = Building('Town Center', 10, 10, owner='J1')
    game_map.place_building(town_center_p1, 10, 10)
    
    villager_p1 = Unit('Villager', 9, 9, None, owner='J1')
    villager2_p1 = Unit('Villager', 12, 9, None, owner='J1')
    villager3_p1 = Unit('Villager', 9, 12, None, owner='J1')
    units = [villager_p1, villager2_p1, villager3_p1]
    buildings = [town_center_p1]
    
    ai = AI(buildings, units)
    # Update units with AI reference
    for unit in units:
        unit.ai = ai
    
    # Set the player AI in game state
    player_side_state.set_player_ai(ai)
    
    # ===== PLAYER 2 (Enemy/AI) =====
    # Place enemy town center on the opposite side of the map
    town_center_p2 = Building('Town Center', 110, 110, owner='J2')
    game_map.place_building(town_center_p2, 110, 110)
    
    # Create enemy units
    villager_p2 = Unit('Villager', 109, 109, None, owner='J2')
    villager2_p2 = Unit('Villager', 112, 109, None, owner='J2')
    villager3_p2 = Unit('Villager', 109, 112, None, owner='J2')
    enemy_units = [villager_p2, villager2_p2, villager3_p2]
    enemy_buildings = [town_center_p2]
    
    # Create enemy AI
    enemy_ai = AI(enemy_buildings, enemy_units)
    
    # Update enemy units with enemy AI
    for unit in enemy_units:
        unit.ai = enemy_ai

    # Lancer la boucle de jeu graphique
    game_loop_graphics(player_side_state.player_side)

def render_text(screen, font, text, position, color=(255, 255, 255)):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)



def init_game():
    global units, buildings, game_map, ai, player_side_state, enemy_units, enemy_buildings, enemy_ai
    player_side_state.player_side = 'J1'  # Set player side (default J1)
    os.makedirs(SAVE_DIR, exist_ok=True)
    loaded_units, loaded_buildings, loaded_map, loaded_ai = load_game_state(DEFAULT_SAVE)
    if loaded_units and loaded_buildings and loaded_map and loaded_ai:
        units, buildings, game_map, ai = loaded_units, loaded_buildings, loaded_map, loaded_ai
    else:
        game_map = Map(120, 120)
        game_map.generate_forest_clusters(num_clusters=10, cluster_size=40)
        game_map.generate_gold_clusters(num_clusters=4)
        
        # ===== PLAYER 1 (Human) =====
        town_center_p1 = Building('Town Center', 10, 10, owner='J1')
        game_map.place_building(town_center_p1, 10, 10)
        
        villager_p1 = Unit('Villager', 9, 9, None, owner='J1')
        villager2_p1 = Unit('Villager', 12, 9, None, owner='J1')
        villager3_p1 = Unit('Villager', 9, 12, None, owner='J1')
        units = [villager_p1, villager2_p1, villager3_p1]
        buildings = [town_center_p1]
        
        ai = AI(buildings, units)
        for unit in units:
            unit.ai = ai
        
        # Set the player AI in game state
        player_side_state.set_player_ai(ai)
        
        # ===== PLAYER 2 (Enemy/AI) =====
        town_center_p2 = Building('Town Center', 110, 110, owner='J2')
        game_map.place_building(town_center_p2, 110, 110)
        
        villager_p2 = Unit('Villager', 109, 109, None, owner='J2')
        villager2_p2 = Unit('Villager', 112, 109, None, owner='J2')
        villager3_p2 = Unit('Villager', 109, 112, None, owner='J2')
        enemy_units = [villager_p2, villager2_p2, villager3_p2]
        enemy_buildings = [town_center_p2]
        
        enemy_ai = AI(enemy_buildings, enemy_units)
        for unit in enemy_units:
            unit.ai = enemy_ai



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

    def send_ping(self, unit_id, x, y):
        """Envoie un ping pour notifier un mouvement de villager"""
        payload = f"unit_id:{unit_id},x:{x},y:{y}"
        self.send("PING", payload)

    def consume_messages(self):
        msgs = self.inbox[:]
        self.inbox.clear()
        return msgs


def main():
    """Main entry point - handles normal or P2P mode"""
    # If P2P mode is enabled, skip menu and start game directly
    if ENABLE_P2P:
        Print_Display(f"[P2P] Démarrage en mode P2P - Joueur: {P2P_PLAYER_SIDE}", Color=2)
        Print_Display(f"[P2P] Port local: {P2P_MY_PORT}, Opponent: {P2P_OPPONENT_HOST}:{P2P_OPPONENT_PORT}", Color=2)
        
        # Initialize game for P2P
        init_p2p_game()
        
        # Run appropriate game loop
        if 'graphics' in sys.argv:
            game_loop_graphics(P2P_PLAYER_SIDE)
        else:
            curses.wrapper(game_loop_curses)
    else:
        # Normal mode - show menu
        if 'graphics' in sys.argv:
            main_menu_graphics()
        else:
            main_menu_curses()

def init_p2p_game():
    """Initialize a game for P2P multiplayer mode"""
    global units, buildings, game_map, ai, player_side_state, enemy_units, enemy_buildings, enemy_ai
    
    # Set player side from P2P config
    player_side_state.player_side = P2P_PLAYER_SIDE
    
    # Create game map
    game_map = Map(120, 120)
    game_map.generate_forest_clusters(num_clusters=10, cluster_size=40)
    game_map.generate_gold_clusters(num_clusters=4)
    
    if P2P_PLAYER_SIDE == 'J1':
        # Setup Player 1 (J1)
        town_center = Building('Town Center', 10, 10, owner='J1')
        game_map.place_building(town_center, 10, 10)
        
        villager1 = Unit('Villager', 9, 9, None, owner='J1')
        villager2 = Unit('Villager', 12, 9, None, owner='J1')
        villager3 = Unit('Villager', 9, 12, None, owner='J1')
        
        units = [villager1, villager2, villager3]
        buildings = [town_center]
        
        # Setup Enemy (J2) - will be controlled by opponent
        enemy_town_center = Building('Town Center', 110, 110, owner='J2')
        game_map.place_building(enemy_town_center, 110, 110)
        
        enemy_villager1 = Unit('Villager', 109, 109, None, owner='J2')
        enemy_villager2 = Unit('Villager', 112, 109, None, owner='J2')
        enemy_villager3 = Unit('Villager', 109, 112, None, owner='J2')
        
        enemy_units = [enemy_villager1, enemy_villager2, enemy_villager3]
        enemy_buildings = [enemy_town_center]
        
    else:  # J2
        # Setup Player 2 (J2)
        town_center = Building('Town Center', 110, 110, owner='J2')
        game_map.place_building(town_center, 110, 110)
        
        villager1 = Unit('Villager', 109, 109, None, owner='J2')
        villager2 = Unit('Villager', 112, 109, None, owner='J2')
        villager3 = Unit('Villager', 109, 112, None, owner='J2')
        
        units = [villager1, villager2, villager3]
        buildings = [town_center]
        
        # Setup Enemy (J1) - will be controlled by opponent
        enemy_town_center = Building('Town Center', 10, 10, owner='J1')
        game_map.place_building(enemy_town_center, 10, 10)
        
        enemy_villager1 = Unit('Villager', 9, 9, None, owner='J1')
        enemy_villager2 = Unit('Villager', 12, 9, None, owner='J1')
        enemy_villager3 = Unit('Villager', 9, 12, None, owner='J1')
        
        enemy_units = [enemy_villager1, enemy_villager2, enemy_villager3]
        enemy_buildings = [enemy_town_center]
    
    # Create AI for player
    ai = AI(buildings, units)
    for unit in units:
        unit.ai = ai
    
    player_side_state.set_player_ai(ai)
    
    # Don't create AI for enemy in P2P mode - they're controlled by real player
    enemy_ai = None
    
    Print_Display("[P2P] Jeu initialisé - en attente du début", Color=2)

if __name__ == "__main__":
    main()