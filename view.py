import curses
#from controller import mapDisplay, printDisplay, positionDisplay, infoDisplay

def init_colors():
    """Initialise les couleurs pour l'affichage."""
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Vert pour le bois
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Jaune pour l'or
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Blanc pour les tuiles vides
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Cyan pour le villageois
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)  # Rouge pour le Town Center
    curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Magenta pour les fermes
    curses.init_pair(7, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Bleu pour d'autres bâtiments (ex: Casernes)

def define_characters(tile):
    """Définit le caractère à afficher en fonction du type de tuile."""
    if tile.building:
        if tile.building.building_type == 'Town Center':
            return ('T', 5)  # Town Center
        elif tile.building.building_type == 'Farm':
            return ('F', 6)  # Ferme
        elif tile.building.building_type == 'Barracks':
            return ('B', 7)  # Casernes
        
    if tile.resource == 'Wood':
        return ('W', 1)  # Bois
    elif tile.resource == 'Gold':
        return ('G', 2)  # Or
    else:
        return ('.', 3)  # Tuile vide représentée par un point
    
def define_boxes(stdscr):
    """Définit les différentes boîtes pour l'affichage."""
    global mapDisplay, printDisplay, positionDisplay, infoDisplay
    
    max_height, max_width = stdscr.getmaxyx()
    
    
    
    mapDisplay = curses.newwin(max_height - 5, int(max_width / 2), 0, 0)
    printDisplay = curses.newwin(5, max_width, max_height - 5, 0)
    positionDisplay = curses.newwin(5, int(max_width / 2), 0, int(max_width / 2))
    infoDisplay = curses.newwin(max_height - 5, int(max_width / 2), 5, int(max_width / 2))


def display_with_curses(stdscr, game_map, units, buildings, ai, view_x, view_y, max_height, max_width):
    
    #stdscr.clear()  # Efface l'écran pour éviter les résidus
    try:
        mapDisplay.clear()
    except NameError:
        define_boxes(stdscr)


    unit_positions = {(unit.x, unit.y): unit.unit_type[0] for unit in units}  # 'V' pour villageois
    mapDisplay.border( 0 )
    # Affiche la portion visible de la carte en fonction de view_x et view_y
    for y in range(view_y, min(view_y + max_height, game_map.height)):
        for x in range(view_x, min(view_x + max_width, game_map.width)):
            tile = game_map.grid[y][x]
            tile_char, color_pair = define_characters(tile)
            Case= tile_char if (x,y) in unit_positions else unit_positions[(x, y)]
            
            mapDisplay.addch(y - view_y +1, x - view_x +1, Case, curses.color_pair(color_pair))  # Affiche l'unité ou la tuile
            #stdscr.addch(y - view_y, x - view_x, Case, curses.color_pair(color_pair))  # Tuile vide représentée par un point

    # Afficher les ressources dans le Town Center
    if buildings:
        town_center = buildings[0]  # Supposons qu'il n'y a qu'un Town Center
        resources_info = (f"Bois: {ai.resources['Wood']} Or: {ai.resources['Gold']} "
                          f"Nourriture: {ai.resources['Food']} "
                          f"Population: {ai.population}/{ai.population_max}")
        #stdscr.addstr(0, 0, resources_info)  # Affiche les ressources en haut de l'écran

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
