import curses

def init_colors():
    """Initialise les couleurs pour l'affichage."""
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Vert pour le bois
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Jaune pour l'or
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Blanc pour les tuiles vides
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Cyan pour le villageois
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)  # Rouge pour le Town Center

def display_with_curses(stdscr, game_map, units, buildings, view_x, view_y, max_height, max_width):
    stdscr.clear()  # Efface l'écran pour éviter les résidus
    unit_positions = {(unit.x, unit.y): unit.unit_type[0] for unit in units}  # 'V' pour villageois

    # Affiche la portion visible de la carte en fonction de view_x et view_y
    for y in range(view_y, min(view_y + max_height, game_map.height)):
        for x in range(view_x, min(view_x + max_width, game_map.width)):
            tile = game_map.grid[y][x]
            if (x, y) in unit_positions:
                stdscr.addch(y - view_y, x - view_x, unit_positions[(x, y)], curses.color_pair(4))  # Villageois en cyan
            elif tile.building and tile.building.building_type == 'Town Center':
                stdscr.addch(y - view_y, x - view_x, 'T', curses.color_pair(5))  # Town Center en rouge
            elif tile.resource == 'Wood':
                stdscr.addch(y - view_y, x - view_x, 'W', curses.color_pair(1))  # Bois en vert
            elif tile.resource == 'Gold':
                stdscr.addch(y - view_y, x - view_x, 'G', curses.color_pair(2))  # Or en jaune
            else:
                stdscr.addch(y - view_y, x - view_x, '.', curses.color_pair(3))  # Tuile vide représentée par un point

    # Afficher les ressources dans le Town Center
    if buildings:
        town_center = buildings[0]  # Supposons qu'il n'y a qu'un Town Center
        resources_info = f"Bois: {town_center.resources['Wood']} Or: {town_center.resources['Gold']}"
        stdscr.addstr(0, 0, resources_info)  # Affiche les ressources en haut de l'écran

    stdscr.refresh()


def handle_input(stdscr, view_x, view_y, max_height, max_width, game_map):
    """Gère les touches pour le scrolling ZQSD et les touches fléchées."""
    key = stdscr.getch()

    if key == ord('z') or key == curses.KEY_UP:  # Touche Z ou flèche haut pour monter
        view_y = max(0, view_y - 1)  # Limite supérieure
    elif key == ord('s') or key == curses.KEY_DOWN:  # Touche S ou flèche bas pour descendre
        view_y = min(game_map.height - max_height, view_y + 1)  # Limite inférieure
    elif key == ord('q') or key == curses.KEY_LEFT:  # Touche Q ou flèche gauche pour aller à gauche
        view_x = max(0, view_x - 1)  # Limite gauche
    elif key == ord('d') or key == curses.KEY_RIGHT:  # Touche D ou flèche droite pour aller à droite
        view_x = min(game_map.width - max_width, view_x + 1)  # Limite droite

    return view_x, view_y
