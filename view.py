import curses

def init_colors():
    """Initialise les couleurs pour l'affichage."""
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Vert pour le bois
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Jaune pour l'or
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Blanc pour les tuiles vides
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Cyan pour le villageois (ancienne version)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)  # Rouge (ancienne version)
    curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Magenta pour les fermes
    curses.init_pair(7, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Bleu (ancienne version)
    # ========== NOUVEAU : Couleurs pour J1 et J2 ==========
    curses.init_pair(10, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Bleu pour Joueur 1
    curses.init_pair(11, curses.COLOR_RED, curses.COLOR_BLACK)    # Rouge pour Joueur 2
    # =======================================================

def display_with_curses(stdscr, game_map, units, buildings, game_state, view_x, view_y, max_height, max_width):
    """
    MODIFIÉ : Prend maintenant game_state au lieu de ai pour accéder aux couleurs
    """
    stdscr.clear()  # Efface l'écran pour éviter les résidus
    
    # ========== MODIFIÉ : Crée un dictionnaire avec unités et leurs couleurs ==========
    unit_positions = {}
    for unit in units:
        # Détermine la couleur selon le propriétaire
        if unit.owner == game_state.player_side:
            color_pair = 10  # Bleu pour J1
        else:
            color_pair = 11  # Rouge pour J2
        unit_positions[(unit.x, unit.y)] = (unit.unit_type[0], color_pair)
    # ==================================================================================

    # Affiche la portion visible de la carte en fonction de view_x et view_y
    for y in range(view_y, min(view_y + max_height, game_map.height)):
        for x in range(view_x, min(view_x + max_width, game_map.width)):
            tile = game_map.grid[y][x]
            
            # ========== MODIFIÉ : Affiche unités avec leurs couleurs ==========
            if (x, y) in unit_positions:
                char, color = unit_positions[(x, y)]
                stdscr.addch(y - view_y, x - view_x, char, curses.color_pair(color))
            # ==================================================================
            
            # ========== MODIFIÉ : Affiche bâtiments avec leurs couleurs ==========
            elif tile.building:
                # Détermine la couleur selon le propriétaire du bâtiment
                if tile.building.owner == game_state.player_side:
                    building_color = 10  # Bleu pour J1
                else:
                    building_color = 11  # Rouge pour J2
                
                if tile.building.building_type == 'Town Center':
                    stdscr.addch(y - view_y, x - view_x, 'T', curses.color_pair(building_color))
                elif tile.building.building_type == 'Farm':
                    stdscr.addch(y - view_y, x - view_x, 'F', curses.color_pair(6))  # Ferme en magenta (neutre)
                elif tile.building.building_type == 'Barracks':
                    stdscr.addch(y - view_y, x - view_x, 'B', curses.color_pair(building_color))
            # =====================================================================
            
            elif tile.resource == 'Wood':
                stdscr.addch(y - view_y, x - view_x, 'W', curses.color_pair(1))  # Bois en vert
            elif tile.resource == 'Gold':
                stdscr.addch(y - view_y, x - view_x, 'G', curses.color_pair(2))  # Or en jaune
            else:
                stdscr.addch(y - view_y, x - view_x, '.', curses.color_pair(3))  # Tuile vide représentée par un point

    # ========== MODIFIÉ : Afficher les ressources du joueur ==========
    if buildings:
        resources_info = (f"Bois: {game_state.player_ai.resources['Wood']} Or: {game_state.player_ai.resources['Gold']} "
                          f"Nourriture: {game_state.player_ai.resources['Food']} "
                          f"Population: {game_state.player_ai.population}/{game_state.player_ai.population_max}")
        stdscr.addstr(0, 0, resources_info)  # Affiche les ressources en haut de l'écran
        
        # ========== NOUVEAU : Afficher le camp du joueur ==========
        player_color = 10 if game_state.player_side == 'J1' else 11
        player_info = f"Vous jouez : {game_state.player_side}"
        stdscr.addstr(1, 0, player_info, curses.color_pair(player_color))
        # ===========================================================
    # ==================================================================

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