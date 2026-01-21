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

from ai_strategies.strategie_No1_dev_ai import StrategieNo1  # Importer la stratégie spécifique
# Création de la stratégie choisie
current_strategy = StrategieNo1()

# Utilisation de la stratégie dans update_game
last_update_time = 0  # Initialiser last_update_time avant la boucle principale du jeu




# Constants
SAVE_DIR = "saves"
DEFAULT_SAVE = os.path.join(SAVE_DIR, "default_game.pkl")

# Global Variables
units, buildings, game_map, ai, ai = None, None, None, None, None

def list_saves():
    saves = [f for f in os.listdir(SAVE_DIR) if f.endswith(".pkl")]
    return saves

def load_existing_game(filename):
    global units, buildings, game_map, ai, ai
    loaded_units, loaded_buildings, loaded_map, loaded_ai = load_game_state(filename)
    if loaded_units and loaded_buildings and loaded_map and loaded_ai:
        units, buildings, game_map, ai = loaded_units, loaded_buildings, loaded_map, loaded_ai
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
                    game_loop_graphics()
                    return  # Quitte la fonction après avoir lancé la boucle de jeu

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
    global units, buildings, game_map, ai   

    max_height, max_width = stdscr.getmaxyx()
    max_height -= max_height - 10
    max_width -= int(max_width/2-20)
    view_x, view_y = 0, 0

    stdscr.nodelay(True)
    stdscr.timeout(100)

    mapDisplay = curses.newwin( int(max_height + 2 ), int(max_width *2+2), 1, 1 )
    mapDisplay.box()

    printDisplay = curses.newwin(5,max_width*2 + 2 ,int(max_height + 5),1)
    printDisplay.box()

    positionDisplay = curses.newwin(2,max_width*2,int(max_height+3),1)
    positionDisplay.box()

    infoDisplay = curses.newwin(max_height,36,1,max_width*2+3)
    infoDisplay.box()



    last_update_time = time.time()

    init_colors()

    while True:
        current_time = time.time()

        # Gère les entrées utilisateur et affiche la carte en curses
        view_x, view_y = handle_input(stdscr, view_x, view_y, max_height, max_width, game_map)
        display_with_curses(stdscr, game_map, units, buildings, ai, view_x, view_y, max_height, max_width)
        last_update_time = update_game(units, buildings, game_map, ai, strategy=current_strategy, delay=0.01, last_update_time=last_update_time)

        key = stdscr.getch()
        if key == curses.KEY_F12:
            reset_curses()
            game_loop_graphics()
            break
        elif key == 27:  # Touche Échap pour ouvrir le menu
            escape_menu_curses(stdscr)

# Correction dans la fonction game_loop_graphics
def game_loop_graphics():
    global units, buildings, game_map, ai

    # Initialiser pygame pour le mode graphique
    screen = initialize_graphics()

    running = True
    clock = pygame.time.Clock()
    view_x, view_y = 0, 0
    max_width = screen_width // TILE_WIDTH
    max_height = screen_height // TILE_HEIGHT
    last_update_time = time.time()

    while running:
        current_time = time.time()
        
        # Gère les entrées utilisateur pour le scrolling de la carte
        view_x, view_y = handle_input_pygame(view_x, view_y, max_width, max_height, game_map)
        
        # Mise à jour du jeu à intervalles réguliers
        last_update_time = update_game(units, buildings, game_map, ai, strategy=current_strategy, delay=0.01, last_update_time=last_update_time)

        # Rendu de la carte et des unités
        render_map(screen, game_map, units, buildings, ai, view_x, view_y, max_width, max_height)


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
    stdscr.clear()
    stdscr.addstr(0, 0, "Réglage de la nouvelle partie:")

    # Options configurables
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
        stdscr.addstr(idx + 1, len(prompt), default)  # Affiche la valeur par défaut
        stdscr.move(idx + 1, len(prompt))  # Place le curseur à la bonne position

        value = ""
        while True:
            key = stdscr.getch()

            if key == ord('\n'):  # Touche Entrée
                if value.strip() == "":
                    value = default  # Si aucune entrée, utilise la valeur par défaut
                break
            elif key in [curses.KEY_BACKSPACE, 127]:  # Touche Backspace
                value = value[:-1]
                stdscr.addstr(idx + 1, len(prompt), " " * (len(value) + 10))  # Efface la ligne précédente
                stdscr.addstr(idx + 1, len(prompt), value)
                stdscr.move(idx + 1, len(prompt) + len(value))
            elif 32 <= key <= 126:  # Caractères imprimables uniquement
                value += chr(key)
                stdscr.addstr(idx + 1, len(prompt), value)
                stdscr.move(idx + 1, len(prompt) + len(value))

        input_values.append(value)

    # Récupération des valeurs
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

    # Initialisation de la nouvelle partie
    global units, buildings, game_map, ai
    game_map = Map(map_size, map_size)
    game_map.generate_forest_clusters(num_clusters=wood_clusters, cluster_size=40)
    game_map.generate_gold_clusters(num_clusters=gold_clusters)
    town_center = Building('Town Center', 10, 10)
    game_map.place_building(town_center, 10, 10)
    
    # Création des unités avant l'IA
    villager1 = Unit('Villager', 9, 9, None)  # Créez l'unité sans AI pour l'instant
    villager2 = Unit('Villager', 12, 9, None)
    villager3 = Unit('Villager', 9, 12, None)
    units = [villager1, villager2, villager3]
    buildings = [town_center]

    # Créez l'instance de l'AI après avoir créé les unités
    ai = AI(buildings, units)

    # Mettre à jour les unités avec l'instance correcte de l'IA
    for unit in units:
        unit.ai = ai

    # Lancer la boucle de jeu avec curses
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
    global units, buildings, game_map, ai, ai
    game_map = Map(120, 120)
    game_map.generate_forest_clusters(num_clusters=10, cluster_size=40)
    game_map.generate_gold_clusters(num_clusters=4)
    town_center = Building('Town Center', 10, 10)
    game_map.place_building(town_center, 10, 10)
    ai = AI(buildings, units)  # Initialisation de l'objet AI
    villager = Unit('Villager', 9, 9, ai)
    villager2 = Unit('Villager', 12, 9, ai)
    villager3 = Unit('Villager', 9, 12, ai)
    units = [villager, villager2, villager3]
    buildings = [town_center]
    ai = AI(ai, buildings, units)  # Passage de l'objet ai à l'IA

    # Lancer la boucle de jeu graphique
    game_loop_graphics()

def render_text(screen, font, text, position, color=(255, 255, 255)):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)



def init_game():
    global units, buildings, game_map, ai, ai
    os.makedirs(SAVE_DIR, exist_ok=True)
    loaded_units, loaded_buildings, loaded_map, loaded_ai = load_game_state(DEFAULT_SAVE)
    if loaded_units and loaded_buildings and loaded_map and loaded_ai:
        units, buildings, game_map, ai = loaded_units, loaded_buildings, loaded_map, loaded_ai
    else:
        game_map = Map(120, 120)
        game_map.generate_forest_clusters(num_clusters=10, cluster_size=40)
        game_map.generate_gold_clusters(num_clusters=4)
        town_center = Building('Town Center', 10, 10)
        game_map.place_building(town_center, 10, 10)
        ai = AI(buildings, units)  # Initialisation de l'objet AI
        villager = Unit('Villager', 9, 9, ai)
        villager2 = Unit('Villager', 12, 9, ai)
        villager3 = Unit('Villager', 9, 12, ai)
        units = [villager, villager2, villager3]
        buildings = [town_center]
        ai = AI(ai, buildings, units)  # Passage de l'objet ai à l'IA

def main():
    # Ne pas initialiser pygame à moins que le mode graphique soit spécifié
    if 'graphics' in sys.argv:
        main_menu_graphics()
    else:
        main_menu_curses()

if __name__ == "__main__":
    main()
