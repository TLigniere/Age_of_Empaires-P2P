import curses
#from controller import mapDisplay, printDisplay, connexionDisplay, infoDisplay

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
    
def define_boxes(stdscr, game_map):
    """Définit les différentes boîtes pour l'affichage."""
    global mapDisplay, printDisplay, connexionDisplay, infoDisplay

    global max_clm, max_row, modu_X, modu_Y, row_num, clm_num
    
    stdscr.clear() 
    stdscr.refresh()

    max_height, max_width = stdscr.getmaxyx()
    
    init_max_row,init_max_clm=stdscr.getmaxyx()
    max_clm=int(init_max_clm/2-3)
    max_row=init_max_row-7

    row_num=len(game_map.grid)   #Row correspond à X coordonnées
    clm_num=len(game_map.grid[0])


    modu_X = max_width % max_clm
    modu_Y = max_height % max_row
    
    mapDisplay = curses.newwin(max_height - 5, int(max_width / 2), 0, 0)
    printDisplay = curses.newwin(5, max_width, max_height - 5, 0)
    connexionDisplay = curses.newwin(5, int(max_width / 2), 0, int(max_width / 2))
    infoDisplay = curses.newwin(max_height - 5, int(max_width / 2), 5, int(max_width / 2))

    mapDisplay.border( 0 )

    connexionDisplay.border( 0 )
    infoDisplay.border( 0 )


def display_with_curses(stdscr, game_map, units, buildings, ai, view_x, view_y, max_height, max_width):
    
 # Efface l'écran pour éviter les résidus
    try:
        mapDisplay.clear()
    except NameError:
        define_boxes(stdscr, game_map)

    X_start_of_cage = 1 + (max_clm * ( view_x - 1) )
    X_end_of_cage = ( modu_X if view_x == max_clm and modu_X != 0 else max_clm ) + 1 + ( max_clm * ( view_x - 1 ) )
    Y_start_of_cage =  1 + (max_row * ( view_y - 1) )
    Y_end_of_cage = ( modu_Y if view_y == max_row and modu_Y != 0 else max_row ) + 1 + ( max_row * ( view_y - 1 ) )


    unit_positions = {(unit.x, unit.y): unit.unit_type[0] for unit in units}  # 'V' pour villageois
    #stdscr.border( 0 )
    mapDisplay.border( 0 )

    # Affiche la portion visible de la carte en fonction de view_x et view_y
#    for y in range(view_y, min(view_y + max_height, game_map.height)):
#        for x in range(view_x, min(view_x + max_width, game_map.width)):
    end_view_y = view_y + max_row
    end_view_x = view_x + int(max_clm / 2)

    for y in range(view_y , end_view_y):
        for x in range(view_x , end_view_x ):
            try:
                tile = game_map.grid[y][x]
                tile_char, color_pair = define_characters(tile)
                Case= tile_char if (x,y) not in unit_positions else unit_positions[(x, y)] 
                if Case == 'V':
                    color_pair = 4 
            except IndexError:
                Case, color_pair = ('?', 4)


            
 # Couleur pour le villageois
            Y = ( y - view_y + 1)
            X = ( x - view_x + 1)*2

            #print( Case )
            try:
                mapDisplay.addstr(Y , X, Case, curses.color_pair(color_pair))  # Affiche l'unité ou la tuile
                #mapDisplay.addstr(Y, X, Case, curses.color_pair(color_pair))  # Affiche l'unité ou la tuile
            except:
                #mapDisplay.addstr(Y , X, '?', curses.color_pair(3))
                #mapDisplay.addstr(0, 0, "Erreur d'affichage aux coordonnées : ")
                #mapDisplay.addstr(1, 0, f"X_start_of_cage: {X_start_of_cage}, X_end_of_cage: {X_end_of_cage}")
                #mapDisplay.addstr(2, 0, f"Y_start_of_cage: {Y_start_of_cage}, Y_end_of_cage: {Y_end_of_cage}")
                break
            #stdscr.addch(y - view_y, x - view_x, Case, curses.color_pair(color_pair))  # Tuile vide représentée par un point
    mapDisplay.refresh()

    #Print_Display(f"Position: {view_x}, {view_y}")

    # Afficher les ressources dans le Town Center
    if buildings:
        town_center = buildings[0]  # Supposons qu'il n'y a qu'un Town Center
        resources_info = (f"Bois: {ai.resources['Wood']} Or: {ai.resources['Gold']} "
                          f"Nourriture: {ai.resources['Food']} "
                          f"Population: {ai.population}/{ai.population_max}")
        #stdscr.addstr(0, 0, resources_info)  # Affiche les ressources en haut de l'écran

    #stdscr.refresh()
    Info_Display([ai])
    Connexion_Display("")


def Connexion_Display(Text):
    connexionDisplay.erase()
    connexionDisplay.border( 0 ) 
    Text_to_display = Text if Text != "" else "Aucune connexion au pairs."

    connexion_info = (f"Statut de la connexion: {Text_to_display}")   

    connexionDisplay.addstr(1, 1, str(connexion_info))
    connexionDisplay.refresh()

def Print_Display(Text):
    printDisplay.erase()
    printDisplay.border( 0 )    
    printDisplay.addstr(1, 1, str(Text))
    printDisplay.refresh()


def Info_Display(players):
    infoDisplay.addstr(1,1,"Informations:")
    infoDisplay.border( 0 )
    joueur_x = 0
    for ai in players:
        joueur_x += 1
        resources_info = (f"Bois: {ai.resources['Wood']} Or: {ai.resources['Gold']} "
                            f"Nourriture: {ai.resources['Food']} "
                            f"Population: {ai.population}/{ai.population_max}")
        infoDisplay.addstr(2 * joueur_x,1,resources_info)

    infoDisplay.refresh()
    """
    infoDisplay.erase()
    x=1
    for faction in Factions:
        for ressources in faction.inventory:
            variable = faction.inventory[ressources]
            infoDisplay.addstr(x,1,f"{faction.name} {ressources}:{variable}") 
            x=x+1

    key = f"{p_position[0]},{p_position[1]}"
    infoCase = M[p_position[1]-1][p_position[0]-1] if units_in_cage.get(key) == None else units_in_cage.get(key)
    j=x+1
    for i in vars(infoCase) :
        variable = vars(infoCase)[i] if i!="path" else None
        infoDisplay.addstr(j,1,f"{i}:{variable}")
        j=j+1
    infoDisplay.refresh()
    """



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
