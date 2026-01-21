import curses
import time
from model import Map, Unit, Building
from view import display_with_curses, handle_input, init_colors

def game_loop(stdscr, units, buildings, game_map, delay=0.04):
    max_height, max_width = stdscr.getmaxyx()  # Obtenir les dimensions de la fenêtre curses
    max_height -= 1  # Ajustement pour les bordures
    max_width -= 1
    view_x, view_y = 0, 0  # Position de la vue actuelle

    stdscr.nodelay(True)  # Ne pas bloquer sur getch()
    stdscr.timeout(100)  # Timeout pour éviter de bloquer

    last_update_time = time.time()  # Dernière fois que les unités ont été mises à jour

    while True:
        current_time = time.time()

        # Gestion du scrolling avec ZQSD sans bloquer la boucle principale
        view_x, view_y = handle_input(stdscr, view_x, view_y, max_height, max_width, game_map)

        # Afficher la portion visible de la carte
        display_with_curses(stdscr, game_map, units, view_x, view_y, max_height, max_width)

        # Mettre à jour les unités à chaque "delay" secondes sans bloquer le scroll
        if current_time - last_update_time > delay:
            for unit in units:
                if unit.returning_to_town_center:
                    # Si le villageois retourne au Town Center
                    path = unit.find_nearest_town_center(game_map, buildings)
                    if path:
                        next_step = path.pop(0)  # Déplacement étape par étape
                        unit.move(*next_step)
                        display_with_curses(stdscr, game_map, units, view_x, view_y, max_height, max_width)

                        # Si le villageois est arrivé au Town Center, il dépose le bois
                        if (unit.x, unit.y) == (buildings[0].x, buildings[0].y):
                            unit.deposit_wood(buildings[0])

                else:
                    # Utilisation de la recherche de bois
                    path = unit.find_nearest_wood(game_map)
                    if path:
                        next_step = path.pop(0)  # Déplacement étape par étape
                        unit.move(*next_step)
                        display_with_curses(stdscr, game_map, units, view_x, view_y, max_height, max_width)

                        # Si le villageois est sur une case avec du bois, il le récolte
                        unit.gather_wood(game_map)

            last_update_time = current_time  # Mettre à jour le temps du dernier déplacement

        # Pause légère pour ne pas surcharger le CPU
        curses.napms(10)  # Petite pause pour éviter que la boucle ne tourne trop vite

def main(stdscr):
    curses.curs_set(0)  # Masquer le curseur
    init_colors()  # Initialiser les couleurs avant le début du jeu

    # Créer une carte de 120x120 avec des forêts et des mines d'or
    game_map = Map(120, 120)
    game_map.generate_forest_clusters(num_clusters=10, cluster_size=40)
    game_map.generate_gold_clusters(num_clusters=4)

    # Placer un Town Center sur la carte
    town_center = Building('Town Center', 10, 10)
    game_map.place_building(town_center, 10, 10)

    # Créer un villageois à côté du Town Center
    villager = Unit('Villager', 9, 9)
    units = [villager]

    # Ajouter le Town Center à la liste des bâtiments
    buildings = [town_center]

    # Démarrer la boucle de jeu
    game_loop(stdscr, units, buildings, game_map)

# Lancer le programme avec curses
curses.wrapper(main)
