import curses

class SpecialCode:
    ENTER   = ord('\n')
    UP      = ord('z')
    DOWN    = ord('s')
    LEFT    = ord('q')
    RIGHT   = ord('d')

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



def define_characters(tile,game_state):
    """Définit le caractère à afficher en fonction du type de tuile."""
    if tile.building:
        if tile.building.owner == game_state.player_side:
            building_color = 10  # Bleu pour J1
        else:
            building_color = 11  # Rouge pour J2
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
    global mapDisplay, printDisplay, connexionDisplay, infoDisplay

    global max_clm, max_row
    
    stdscr.clear() 
    stdscr.refresh()

    max_height, max_width = stdscr.getmaxyx()
    
    max_clm=int(max_width/2-3)
    max_row=max_height-7

    sizeMap =           (int(max_height)                                    , int(max_width / 2))
    sizeInfo =          (int(max_height/4)                                  , int(max_width / 2))
    sizeConnexion =     (int(max_height/8)                                  , int(max_width / 2))
    sizePrint =         (int(max_height - sizeConnexion[0] - sizeInfo[0])   , int(max_width / 2))

    # Xdisplay =        curses.newwin(height            , width             , position_y                        , position_x )
    
    mapDisplay =        curses.newwin(sizeMap[0]        , sizeMap[1]        , 0                                 , 0         )
    infoDisplay =       curses.newwin(sizeInfo[0]       , sizeInfo[1]       , sizeConnexion[0]                  , sizeMap[1])
    connexionDisplay =  curses.newwin(sizeConnexion[0]  , sizeConnexion[1]  , 0                                 , sizeMap[1])
    printDisplay =      curses.newwin(sizePrint[0]      , sizePrint[1]      , sizeConnexion[0] + sizeInfo[0]    , sizeMap[1])

    # Xdisplay = curses.newwin( height, width, position_y, position_x )

    max_row,max_height = mapDisplay.getmaxyx()

    max_clm=int(max_width/2-3)
    max_row=max_row - 2

    Print_Display("Affichage initialisé.")

def display_with_curses(stdscr, game_map, units, game_state, ai, view_x, view_y):
    
 # Efface l'écran pour éviter les résidus
    try:
        mapDisplay.clear()
    except NameError:
        define_boxes(stdscr)

    #unit_positions = {(unit.x, unit.y): unit.unit_type[0] for unit in units}  # 'V' pour villageois

    unit_positions = {}
    Print_Display(f"[DEBUG] Nombre d'unités à afficher : {len(units)}")
    for unit in units:
        # Détermine la couleur selon le propriétaire
        if unit.owner == "J1":
            color_pair = 10  # Bleu pour J1
        else:
            color_pair = 11  # Rouge pour J2
        unit_positions[(unit.x, unit.y)] = (unit.unit_type[0], color_pair)
        Print_Display(f"[DEBUG] Unité {unit.unit_type} à la position ({unit.x}, {unit.y}) avec couleur {color_pair}")

    mapDisplay.border( 0 )

    end_view_y = view_y + max_row
    end_view_x = view_x + int(max_clm / 2)

    for y in range(view_y , end_view_y):
        for x in range(view_x , end_view_x ):
            try:
                tile = game_map.grid[y][x]
                tile_char, color_pair = define_characters(tile,game_state)
                Case= tile_char if (x,y) not in unit_positions else unit_positions[(x, y)] 
                if isinstance(Case, tuple):
                    Case, color_pair = Case
            except IndexError:
                Case, color_pair = ('?', 4)

            Y = ( y - view_y + 1)
            X = ( x - view_x + 1)*2
            
            mapDisplay.addstr(Y , X, Case, curses.color_pair(color_pair))  # Affiche l'unité ou la tuile
    mapDisplay.refresh()

    Info_Display([ai],game_state)
    Connexion_Display("")


def Connexion_Display(Text):
    connexionDisplay.erase()
    connexionDisplay.border( 0 ) 
    Text_to_display = Text if Text != "" else "Aucune connexion au pairs."

    connexion_info = (f"Statut de la connexion: {Text_to_display}")   

    connexionDisplay.addstr(1, 1, str(connexion_info))
    connexionDisplay.refresh()

Queue = [] 

def Print_Display(Text,Color=3):
    try:
        printDisplay.erase()
        printDisplay.border( 0 )

        Text=str(Text)

        Display_Height, Display_Width = printDisplay.getmaxyx()

        Queue.insert(0, [Text,Color])
        
        if len(Queue) > Display_Height -2 :
            Queue.pop()

        for i in range(0, Display_Height -2):
            Text_to_display = Queue[i][0] if len(Queue) > i else ""
            Color           = Queue[i][1] if len(Queue) > i else False
            try :
                printDisplay.addstr(i+1, 1, Text_to_display,curses.color_pair(Color)) 
            except curses.error:
                pass

        printDisplay.refresh()
        
    except NameError:
        print(Text)


def Info_Display(players, game_state):
    player_color = 10 if game_state.player_side == 'J1' else 11

    infoDisplay.addstr(1,1,f"Vous jouez: {game_state.player_side}", curses.color_pair(player_color))
    infoDisplay.addstr(2,1,"Informations:")
    infoDisplay.border( 0 )
    joueur_x = 0

    ####################################################


    ####################################################

    for player in players:

        joueur_x += 1
        resources_info = (f"Bois: {player.resources['Wood']} Or: {player.resources['Gold']} "
                            f"Nourriture: {player.resources['Food']} "
                            f"Population: {player.population}/{player.population_max}")
        infoDisplay.addstr(2 * joueur_x,1,resources_info)

    infoDisplay.refresh()



def handle_input(stdscr, view_x, view_y, max_height, max_width, game_map):
    """Gère les touches pour le scrolling ZQSD et les touches fléchées."""
    key = stdscr.getch()

    match key:
        case SpecialCode.UP | curses.KEY_UP:
            view_y = max(0, view_y - 1)
        case SpecialCode.DOWN | curses.KEY_DOWN:
            view_y = min(game_map.height - max_height, view_y + 1)
        case SpecialCode.LEFT | curses.KEY_LEFT:
            view_x = max(0, view_x - 1)
        case SpecialCode.RIGHT | curses.KEY_RIGHT:
            view_x = min(game_map.width - max_width, view_x + 1)

    return view_x, view_y