import curses
import time
import os
import pygame
import sys
import signal
from model import Map, Unit, Building
from view import display_with_curses, handle_input, init_colors
from view_graphics import handle_input_pygame, render_map, screen_width, screen_height, TILE_WIDTH, TILE_HEIGHT, initialize_graphics
from game_utils import save_game_state, load_game_state

from ai_strategies.base_strategies import AI
from ai_strategies.strategie_No1_dev_ai import StrategieNo1

# ========== NOUVEAU : Classe GameState ==========
class GameState:
    """Encapsule tout l'état du jeu"""
    def __init__(self):
        self.player_side = None  # 'J1' ou 'J2'
        self.units = []
        self.buildings = []
        self.game_map = None
        self.player_ai = None
        self.enemy_ai = None
        
    def set_player(self, player_id):
        """Définit le camp du joueur ('J1' ou 'J2')"""
        self.player_side = player_id
        
    def get_player_color(self):
        """Retourne la couleur RGB du joueur"""
        if self.player_side == 'J1':
            return (0, 100, 255)  # Bleu
        else:
            return (255, 50, 50)  # Rouge
            
    def get_enemy_color(self):
        """Retourne la couleur RGB de l'ennemi"""
        if self.player_side == 'J1':
            return (255, 50, 50)  # Rouge
        else:
            return (0, 100, 255)  # Bleu
            
    def get_enemy_side(self):
        """Retourne le camp ennemi"""
        return 'J2' if self.player_side == 'J1' else 'J1'

# ========================================

current_strategy = StrategieNo1()
last_update_time = 0

# Constants
SAVE_DIR = "saves"
DEFAULT_SAVE = os.path.join(SAVE_DIR, "default_game.pkl")

# Global Variables - MODIFIÉ
game_state = None  # Remplace units, buildings, game_map, ai

def list_saves():
    saves = [f for f in os.listdir(SAVE_DIR) if f.endswith(".pkl")]
    return saves

def load_existing_game(filename):
    global game_state
    loaded_data = load_game_state(filename)
    if loaded_data:
        game_state = loaded_data
        print(f"[INFO] Chargé : {filename}")
    else:
        print("[ERROR] Chargement échoué. Le fichier est corrompu ou n'existe pas.")

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
        elif key == ord('\n'):
            load_existing_game(os.path.join(SAVE_DIR, saves[selected_option]))
            game_loop_curses(stdscr)
            return

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
                    load_existing_game(os.path.join(SAVE_DIR, saves[selected_option]))
                    game_loop_graphics()
                    return

def clear_input_buffer(stdscr):
    stdscr.nodelay(True)
    while True:
        key = stdscr.getch()
        if key == -1:
            break
    stdscr.nodelay(False)

def signal_handler(sig, frame):
    print("[INFO] Exiting due to CTRL+C")
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
    save_game_state(game_state)
    if new_mode == 'graphics':
        reset_curses()
        game_loop_graphics()
    elif new_mode == 'terminal':
        reset_graphics()
        curses.wrapper(game_loop_curses)
        pygame.quit()

def update_game(game_state, strategy, delay, last_update_time):
    """Met à jour le jeu - MODIFIÉ pour utiliser game_state"""
    current_time = time.time()
    if current_time - last_update_time > delay:
        strategy.execute(game_state.units, game_state.buildings, game_state.game_map, game_state.player_ai)
        return current_time
    return last_update_time

def escape_menu_curses(stdscr):
    options = ["1. Sauvegarder", "2. Charger", "3. Reprendre", "4. Retour au Menu Principal", "5. Quitter"]
    selected_option = 0

    while True:
        stdscr.clear()
        for i, option in enumerate(options):
            if i == selected_option:
                stdscr.addstr(i, 0, option, curses.A_REVERSE)
            else:
                stdscr.addstr(i, 0, option)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_DOWN:
            selected_option = (selected_option + 1) % len(options)
        elif key == curses.KEY_UP:
            selected_option = (selected_option - 1) % len(options)
        elif key == ord('\n'):
            if selected_option == 0:
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
                        stdscr.addstr(6, 0, " " * 20)
                        stdscr.addstr(6, 0, save_name)
                        stdscr.refresh()
                    elif 32 <= key <= 126:
                        save_name += chr(key)
                        stdscr.addstr(6, 0, save_name)
                        stdscr.refresh()

                try:
                    save_game_state(game_state, os.path.join(SAVE_DIR, f"{save_name}.pkl"))
                except Exception as e:
                    stdscr.addstr(7, 0, f"Erreur : {str(e)}")
                    stdscr.refresh()
                    time.sleep(2)

            elif selected_option == 1:
                load_existing_game_curses(stdscr)
                return

            elif selected_option == 2:
                return

            elif selected_option == 3:
                curses.wrapper(main_menu_curses_internal)
                return

            elif selected_option == 4:
                sys.exit(0)

        elif key == 27:
            return

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
                elif event.key in (pygame.K_ESCAPE, pygame.K_F12):
                    return None
                elif 32 <= event.key <= 126:
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
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if selected_option == 0:
                        save_name = input_text_pygame(screen, font, "Nom de la sauvegarde :")
                        if save_name:
                            save_game_state(game_state, os.path.join(SAVE_DIR, f"{save_name}.pkl"))
                    elif selected_option == 1:
                        load_existing_game_graphics(screen, font)
                        return

                    elif selected_option == 2:
                        running = False

                    elif selected_option == 3:
                        main_menu_graphics()
                        return

                    elif selected_option == 4:
                        sys.exit(0)

# ========== NOUVEAU : Choix du joueur ==========
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
# ================================================

def game_loop_curses(stdscr):
    global game_state

    max_height, max_width = stdscr.getmaxyx()
    max_height -= 1
    max_width -= 1
    view_x, view_y = 0, 0

    stdscr.nodelay(True)
    stdscr.timeout(100)

    last_update_time = time.time()

    init_colors()

    while True:
        current_time = time.time()

        view_x, view_y = handle_input(stdscr, view_x, view_y, max_height, max_width, game_state.game_map)
        display_with_curses(stdscr, game_state.game_map, game_state.units, game_state.buildings, game_state, view_x, view_y, max_height, max_width)
        last_update_time = update_game(game_state, strategy=current_strategy, delay=0.01, last_update_time=last_update_time)

        key = stdscr.getch()
        if key == curses.KEY_F12:
            reset_curses()
            game_loop_graphics()
            break
        elif key == 27:
            escape_menu_curses(stdscr)

def game_loop_graphics():
    global game_state

    screen = initialize_graphics()

    running = True
    clock = pygame.time.Clock()
    view_x, view_y = 0, 0
    max_width = screen_width // TILE_WIDTH
    max_height = screen_height // TILE_HEIGHT
    last_update_time = time.time()

    while running:
        current_time = time.time()
        
        view_x, view_y = handle_input_pygame(view_x, view_y, max_width, max_height, game_state.game_map)
        
        last_update_time = update_game(game_state, strategy=current_strategy, delay=0.01, last_update_time=last_update_time)

        render_map(screen, game_state.game_map, game_state.units, game_state.buildings, game_state, view_x, view_y, max_width, max_height)

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
                stdscr.addstr(i + 1, 0, option, curses.A_REVERSE)
            else:
                stdscr.addstr(i + 1, 0, option)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_DOWN:
            selected_option = (selected_option + 1) % len(options)
        elif key == curses.KEY_UP:
            selected_option = (selected_option - 1) % len(options)
        elif key == ord('\n'):
            if selected_option == 0:
                load_existing_game_curses(stdscr)
            elif selected_option == 1:
                loaded_data = load_game_state(DEFAULT_SAVE)
                if loaded_data:
                    global game_state
                    game_state = loaded_data
                    curses.wrapper(game_loop_curses)
            elif selected_option == 2:
                start_new_game_curses(stdscr)
            elif selected_option == 3:
                sys.exit(0)

def start_new_game_curses(stdscr):
    global game_state
    
    stdscr.clear()
    stdscr.addstr(0, 0, "Réglage de la nouvelle partie:")

    input_fields = [
        ("Taille de la carte (par défaut 120x120): ", "120"),
        ("Nombre de clusters de bois (par défaut 10): ", "10"),
        ("Nombre de clusters d'or (par défaut 4): ", "4"),
        ("Vitesse du jeu (par défaut 1.0): ", "1.0")
    ]
    input_values = []

    curses.echo()
    for idx, (prompt, default) in enumerate(input_fields):
        stdscr.addstr(idx + 1, 0, prompt)
        stdscr.addstr(idx + 1, len(prompt), default)
        stdscr.move(idx + 1, len(prompt))

        value = ""
        while True:
            key = stdscr.getch()

            if key == ord('\n'):
                if value.strip() == "":
                    value = default
                break
            elif key in [curses.KEY_BACKSPACE, 127]:
                value = value[:-1]
                stdscr.addstr(idx + 1, len(prompt), " " * (len(value) + 10))
                stdscr.addstr(idx + 1, len(prompt), value)
                stdscr.move(idx + 1, len(prompt) + len(value))
            elif 32 <= key <= 126:
                value += chr(key)
                stdscr.addstr(idx + 1, len(prompt), value)
                stdscr.move(idx + 1, len(prompt) + len(value))

        input_values.append(value)

    try:
        map_size = int(input_values[0])
        wood_clusters = int(input_values[1])
        gold_clusters = int(input_values[2])
        speed = float(input_values[3])
    except ValueError:
        stdscr.addstr(len(input_fields) + 2, 0, "Erreur : Entrée invalide, utilisation des valeurs par défaut.")
        stdscr.refresh()
        time.sleep(2)
        map_size = 120
        wood_clusters = 10
        gold_clusters = 4
        speed = 1.0

    # ========== NOUVEAU : Choix du joueur ==========
    player_side = choose_player_side_curses(stdscr)
    enemy_side = 'J2' if player_side == 'J1' else 'J1'
    # ================================================

    # Initialisation avec GameState
    game_state = GameState()
    game_state.set_player(player_side)
    game_state.game_map = Map(map_size, map_size)
    game_state.game_map.generate_forest_clusters(num_clusters=wood_clusters, cluster_size=40)
    game_state.game_map.generate_gold_clusters(num_clusters=gold_clusters)
    
    # Créer le Town Center avec le bon propriétaire
    town_center = Building('Town Center', 10, 10, owner=player_side)
    game_state.game_map.place_building(town_center, 10, 10)
    game_state.buildings = [town_center]
    
    # Créer l'IA du joueur APRÈS avoir créé les bâtiments
    game_state.player_ai = AI(game_state.buildings, [])
    
    # Unités du joueur - MODIFIÉ avec owner
    villager1 = Unit('Villager', 9, 9, game_state.player_ai, owner=player_side)
    villager2 = Unit('Villager', 12, 9, game_state.player_ai, owner=player_side)
    villager3 = Unit('Villager', 9, 12, game_state.player_ai, owner=player_side)
    
    # ========== NOUVEAU : Unités ennemies ==========
    # Créer un Town Center ennemi
    enemy_town_center = Building('Town Center', 110, 110, owner=enemy_side)
    game_state.game_map.place_building(enemy_town_center, 110, 110)
    game_state.buildings.append(enemy_town_center)
    
    game_state.enemy_ai = AI([enemy_town_center], [])
    enemy1 = Unit('Villager', 108, 108, game_state.enemy_ai, owner=enemy_side)
    enemy2 = Unit('Villager', 112, 108, game_state.enemy_ai, owner=enemy_side)
    # ================================================
    
    game_state.units = [villager1, villager2, villager3, enemy1, enemy2]
    
    # Mise à jour des références AI
    game_state.player_ai.units = [u for u in game_state.units if u.owner == player_side]
    game_state.enemy_ai.units = [u for u in game_state.units if u.owner == enemy_side]
    
    # Séparer les bâtiments par propriétaire
    game_state.player_ai.buildings = [b for b in game_state.buildings if b.owner == player_side]
    game_state.enemy_ai.buildings = [b for b in game_state.buildings if b.owner == enemy_side]
    # Mettre à jour le town_center pour chaque IA
    game_state.player_ai.town_center = game_state.player_ai.buildings[0] if game_state.player_ai.buildings else None
    game_state.enemy_ai.town_center = game_state.enemy_ai.buildings[0] if game_state.enemy_ai.buildings else None

    curses.wrapper(game_loop_curses)

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
                    if selected_option == 0:
                        load_existing_game_graphics(screen, font)
                    elif selected_option == 1:
                        loaded_data = load_game_state(DEFAULT_SAVE)
                        if loaded_data:
                            global game_state
                            game_state = loaded_data
                            game_loop_graphics()
                    elif selected_option == 2:
                        start_new_game_graphics(screen, font)
                    elif selected_option == 3:
                        sys.exit(0)

def start_new_game_graphics(screen, font):
    global game_state
    
    input_fields = [
        ("Taille de la carte (par défaut 120x120): ", "120"),
        ("Nombre de clusters de bois (par défaut 10): ", "10"),
        ("Nombre de clusters d'or (par défaut 4): ", "4"),
        ("Vitesse du jeu (par défaut 1.0): ", "1.0")
    ]
    input_values = []

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
                        running = False
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key in (pygame.K_ESCAPE, pygame.K_F12):
                        return
                    elif 32 <= event.key <= 126:
                        input_text += event.unicode

        input_values.append(input_text)

    launch_button_selected = True
    running = True
    while running:
        screen.fill((0, 0, 0))
        for idx, (prompt, value) in enumerate(zip([f[0] for f in input_fields], input_values)):
            prompt_surface = font.render(f"{prompt} {value}", True, (255, 255, 255))
            screen.blit(prompt_surface, (20, 50 + idx * 60))

        button_color = (255, 255, 0) if launch_button_selected else (100, 100, 100)
        button_text = font.render("Lancer la Partie", True, button_color)
        screen.blit(button_text, (20, 100 + len(input_fields) * 60))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and launch_button_selected:
                    running = False
                elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    launch_button_selected = not launch_button_selected
                elif event.key in (pygame.K_ESCAPE, pygame.K_F12):
                    return

    try:
        map_size = int(input_values[0])
        wood_clusters = int(input_values[1])
        gold_clusters = int(input_values[2])
        speed = float(input_values[3])
    except ValueError:
        map_size = 120
        wood_clusters = 10
        gold_clusters = 4
        speed = 1.0

    # ========== NOUVEAU : Choix du joueur ==========
    player_side = choose_player_side_graphics(screen, font)
    enemy_side = 'J2' if player_side == 'J1' else 'J1'
    # ================================================

# Initialisation avec GameState
    game_state = GameState()
    game_state.set_player(player_side)
    game_state.game_map = Map(map_size, map_size)
    game_state.game_map.generate_forest_clusters(num_clusters=wood_clusters, cluster_size=40)
    game_state.game_map.generate_gold_clusters(num_clusters=gold_clusters)
    
    town_center = Building('Town Center', 10, 10)
    game_state.game_map.place_building(town_center, 10, 10)
    
    game_state.player_ai = AI([], [])
    
    villager1 = Unit('Villager', 9, 9, game_state.player_ai)
    villager1.owner = player_side
    villager2 = Unit('Villager', 12, 9, game_state.player_ai)
    villager2.owner = player_side
    villager3 = Unit