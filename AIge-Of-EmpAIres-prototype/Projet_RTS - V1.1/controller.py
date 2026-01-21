import curses
import time
import os
import sys
import subprocess
import signal
from model import Map, Unit, Building, AI
from view import display_with_curses, handle_input, init_colors
from game_utils import save_game_state, load_game_state

# Supprimer l'importation des constantes Pygame pour éviter l'ouverture de la fenêtre noire
# Nous initialiserons ces constantes dynamiquement dans la partie graphique

def signal_handler(sig, frame):
    """Handle CTRL+C to exit cleanly."""
    print("[INFO] Exiting due to CTRL+C")
    curses.endwin()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def reset_curses():
    """Ensures curses is fully reset before switching modes."""
    curses.endwin()
    time.sleep(0.1)  # Small delay to ensure reset
    sys.stdout.flush()

def clear_input_buffer(stdscr):
    """Clear any lingering input in the buffer."""
    try:
        while True:
            key = stdscr.getch()
            if key != -1:
                print(f"[DEBUG] Key pressed: {key}")
            break
    except:
        pass

def reset_graphics():
    """Réinitialise Pygame avant de retourner au terminal"""
    try:
        import pygame
        pygame.quit()
    except ImportError:
        pass  # Si pygame n'est pas disponible, il n'y a rien à nettoyer
    time.sleep(0.1)  # Petite pause pour être sûr que tout est réinitialisé

def switch_mode(new_mode, units, buildings, game_map, ai):
    """Bascule entre mode terminal et mode graphique"""
    save_game_state(units, buildings, game_map, ai)  # Sauvegarde de l'état
    if new_mode == 'graphics':
        reset_curses()  # Nettoie curses proprement
        game_loop_graphics_wrapper(units, buildings, game_map, ai)
    elif new_mode == 'terminal':
        reset_graphics()  # Nettoie pygame proprement avant de repasser au terminal
        curses.wrapper(main)

def game_loop_curses(stdscr, units, buildings, game_map, ai, delay=0.1):
    """Boucle principale du jeu pour la version terminal avec Curses."""
    max_height, max_width = stdscr.getmaxyx()  # Obtenir les dimensions de la fenêtre curses
    max_height -= 1  # Ajustement pour les bordures
    max_width -= 1
    view_x, view_y = 0, 0  # Position de la vue actuelle

    stdscr.nodelay(True)  # Ne pas bloquer sur getch()
    stdscr.timeout(100)  # Timeout pour éviter de bloquer

    last_update_time = time.time()  # Dernière fois que les unités ont été mises à jour

    clear_input_buffer(stdscr)  # Clear input buffer after switching back

    print("[INFO] Starting terminal game loop")

    while True:
        current_time = time.time()

        # Gestion du scrolling avec ZQSD sans bloquer la boucle principale
        view_x, view_y = handle_input(stdscr, view_x, view_y, max_height, max_width, game_map)

        # Afficher la portion visible de la carte
        display_with_curses(stdscr, game_map, units, buildings, view_x, view_y, max_height, max_width)

        # Mettre à jour les unités à chaque "delay" secondes sans bloquer le scroll
        if current_time - last_update_time > delay:
            for unit in units:
                if unit.returning_to_town_center:
                    path = unit.find_nearest_town_center(game_map, buildings)
                    if path:
                        next_step = path.pop(0)  # Déplacement étape par étape
                        unit.move(*next_step)

                        # Si le villageois est arrivé au Town Center, il dépose les ressources
                        if (unit.x, unit.y) == (buildings[0].x, buildings[0].y):
                            unit.deposit_resource(buildings[0])

                else:
                    # Utilisation de la recherche de bois
                    path = unit.find_nearest_wood(game_map)
                    if path:
                        next_step = path.pop(0)  # Déplacement étape par étape
                        unit.move(*next_step)
                        # Si le villageois est sur une case avec du bois, il le récolte
                        unit.gather_resource(game_map)

            # Gestion de la construction de bâtiments par l'IA
            ai.update_population()
            ai.build(game_map)

            last_update_time = current_time  # Mettre à jour le temps du dernier déplacement

        # Gestion de la bascule entre mode graphique et terminal avec F12
        key = stdscr.getch()
        if key != -1:
            print(f"[DEBUG] Key pressed: {key}")

        if key == curses.KEY_F12:
            print("[INFO] Switching to graphics mode")
            switch_mode('graphics', units, buildings, game_map, ai)
            break  # Quitter la boucle pour arrêter le mode curses

        curses.napms(10)  # Petite pause pour éviter que la boucle ne tourne trop vite


def game_loop_graphics_wrapper(units, buildings, game_map, ai, delay=0.1):
    """Boucle principale pour gérer la partie en mode graphique."""
    import pygame
    pygame.init()  # Réinitialise Pygame avant de commencer le mode graphique

    # Import dynamique des fonctions spécifiques à Pygame
    from view_graphics import handle_input_pygame, render_map

    # Initialiser dynamiquement les constantes Pygame
    from view_graphics import screen_width, screen_height, tile_size

    # Réinitialise l'affichage à chaque retour en mode graphique
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("RTS Game")  # Assure que la fenêtre a bien un titre

    def game_loop_graphics():
        running = True
        clock = pygame.time.Clock()
        view_x, view_y = 0, 0  # Position de la caméra
        max_width = screen_width // tile_size
        max_height = screen_height // tile_size
        last_update_time = time.time()

        print("[INFO] Starting graphics game loop")

        while running:
            current_time = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_F12]:  # Basculer vers le mode terminal
                print("[INFO] Switching to terminal mode")
                switch_mode('terminal', units, buildings, game_map, ai)
                break  # Quitter la boucle pour arrêter le mode graphique

            # Appel de la logique de jeu existante et affichage
            view_x, view_y = handle_input_pygame(view_x, view_y, max_width, max_height, game_map)
            render_map(screen, game_map, units, buildings, view_x, view_y, max_width, max_height)

            # Logique de mise à jour des unités
            if current_time - last_update_time > delay:
                for unit in units:
                    if unit.returning_to_town_center:
                        path = unit.find_nearest_town_center(game_map, buildings)
                        if path:
                            next_step = path.pop(0)
                            unit.move(*next_step)

                            if (unit.x, unit.y) == (buildings[0].x, buildings[0].y):
                                unit.deposit_resource(buildings[0])
                    else:
                        path = unit.find_nearest_wood(game_map)
                        if path:
                            next_step = path.pop(0)
                            unit.move(*next_step)
                            unit.gather_resource(game_map)

                ai.update_population()
                ai.build(game_map)

                last_update_time = current_time

            clock.tick(30)

        pygame.quit()

    game_loop_graphics()


def init_game():
    """Initialiser les unités, bâtiments et carte si cela n'a pas déjà été fait."""
    global units, buildings, game_map, ai

    # Charger l'état du jeu s'il existe, sinon initialiser une nouvelle partie
    loaded_units, loaded_buildings, loaded_map, loaded_ai = load_game_state()
    if loaded_units and loaded_buildings and loaded_map and loaded_ai:
        units, buildings, game_map, ai = loaded_units, loaded_buildings, loaded_map, loaded_ai
    else:
        # Initialiser une nouvelle partie
        game_map = Map(120, 120)
        game_map.generate_forest_clusters(num_clusters=10, cluster_size=40)
        game_map.generate_gold_clusters(num_clusters=4)

        town_center = Building('Town Center', 10, 10)
        game_map.place_building(town_center, 10, 10)

        villager = Unit('Villager', 9, 9)
        units = [villager]

        buildings = [town_center]
        ai = AI(buildings, units)


def main(stdscr=None):
    """Fonction principale pour démarrer le jeu en mode terminal ou graphique."""
    init_game()

    if stdscr is None:
        game_loop_graphics_wrapper(units, buildings, game_map, ai)
    else:
        curses.curs_set(0)  # Masquer le curseur
        init_colors()  # Initialiser les couleurs avant le début du jeu
        game_loop_curses(stdscr, units, buildings, game_map, ai)


# Lancer le programme avec curses ou pygame selon l'argument
if 'graphics' not in sys.argv:
    curses.wrapper(main)
else:
    main()
