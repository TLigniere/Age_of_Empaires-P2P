import pygame
import os

# Constants for screen dimensions and tile sizes
screen_width = 1920  # Increased screen width for better view
screen_height = 1080  # Increased screen height for better view
TILE_WIDTH = 64
TILE_HEIGHT = 32

# Dictionary to hold loaded images
images = {}

def initialize_graphics():
    # Initialise Pygame et retourne la surface principale
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("AIge of EmpAIres")
    
    # Charger les images nécessaires
    try:
        images['grass'] = pygame.transform.scale(pygame.image.load("assets/grass.png").convert_alpha(), (TILE_WIDTH, TILE_HEIGHT))
        images['tree'] = pygame.transform.scale(pygame.image.load("assets/tree.png").convert_alpha(), (TILE_WIDTH, TILE_HEIGHT * 2))  # Adjusted size for better fit
        images['gold'] = pygame.transform.scale(pygame.image.load("assets/gold.png").convert_alpha(), (TILE_WIDTH, TILE_HEIGHT))
        images['town_center'] = pygame.transform.scale(pygame.image.load("assets/town_center.png").convert_alpha(), (TILE_WIDTH * 2, TILE_HEIGHT * 2))  # Adjusted size to match scale
        images['villager'] = pygame.transform.scale(pygame.image.load("assets/villager.png").convert_alpha(), (TILE_WIDTH // 2, TILE_HEIGHT))  # Adjusted size to be smaller
        images['farm'] = pygame.transform.scale(pygame.image.load("assets/farm.png").convert_alpha(), (TILE_WIDTH * 2, TILE_HEIGHT * 2))  # Nouvelle ligne pour la ferme
    except pygame.error as e:
        print(f"Erreur de chargement de l'image : {e}")
        sys.exit(1)
    
    return screen

# ========== NOUVEAU : Fonction pour coloriser une image ==========
def colorize_image(image, color):
    """
    Applique une teinte de couleur à une image tout en préservant la transparence.
    
    Args:
        image: Surface pygame à coloriser
        color: Tuple RGB (r, g, b)
    
    Returns:
        Surface pygame colorisée
    """
    colored_image = image.copy()
    colored_image.fill(color + (0,), special_flags=pygame.BLEND_RGBA_MULT)
    return colored_image
# ==================================================================

def render_map(screen, game_map, units, buildings, game_state, view_x, view_y, max_width, max_height):
    """
    MODIFIÉ : Prend maintenant game_state au lieu de ai pour accéder aux couleurs
    """
    if not isinstance(screen, pygame.Surface):
        raise TypeError(f"Expected screen to be a pygame.Surface, but got {type(screen)}")

    # Clear the screen
    screen.fill((0, 0, 0))

    # Render map tiles
    for y in range(max(0, view_y - max_height), min(view_y + max_height * 2, game_map.height)):
        for x in range(max(0, view_x - max_width), min(view_x + max_width * 2, game_map.width)):
            # Calcul des coordonnées isométriques
            iso_x = (x - y) * (TILE_WIDTH // 2) + (screen_width // 2) - TILE_WIDTH // 2 - (view_x - view_y) * (TILE_WIDTH // 2)
            iso_y = (x + y) * (TILE_HEIGHT // 2) - (view_x + view_y) * (TILE_HEIGHT // 2)

            tile = game_map.grid[y][x]
            if tile.resource == 'Wood':
                screen.blit(images['tree'], (iso_x, iso_y - TILE_HEIGHT))  # Décalage pour arbre
            elif tile.resource == 'Gold':
                screen.blit(images['gold'], (iso_x, iso_y))
            else:
                screen.blit(images['grass'], (iso_x, iso_y))

    # ========== MODIFIÉ : Render buildings avec couleurs ==========
    for building in buildings:
        screen_x = (building.x - building.y) * (TILE_WIDTH // 2) + (screen_width // 2) - TILE_WIDTH // 2 - (view_x - view_y) * (TILE_WIDTH // 2)
        screen_y = (building.x + building.y) * (TILE_HEIGHT // 2) - (view_x + view_y) * (TILE_HEIGHT // 2)
        
        # Déterminer la couleur selon le propriétaire
        if building.owner == game_state.player_side:
            color = game_state.get_player_color()
        else:
            color = game_state.get_enemy_color()
        
        if building.building_type == 'Town Center':
            colored_building = colorize_image(images['town_center'], color)
            screen.blit(colored_building, (screen_x, screen_y - TILE_HEIGHT))
        elif building.building_type == 'Farm':
            colored_building = colorize_image(images['farm'], color)
            screen.blit(colored_building, (screen_x, screen_y - TILE_HEIGHT))
    # ==============================================================

    # ========== MODIFIÉ : Render units avec couleurs ==========
    for unit in units:
        screen_x = (unit.x - unit.y) * (TILE_WIDTH // 2) + (screen_width // 2) - TILE_WIDTH // 2 - (view_x - view_y) * (TILE_WIDTH // 2)
        screen_y = (unit.x + unit.y) * (TILE_HEIGHT // 2) - (view_x + view_y) * (TILE_HEIGHT // 2)
        
        # Déterminer la couleur selon le propriétaire
        if unit.owner == game_state.player_side:
            color = game_state.get_player_color()
        else:
            color = game_state.get_enemy_color()
        
        if unit.unit_type == 'Villager':
            colored_villager = colorize_image(images['villager'], color)
            screen.blit(colored_villager, (screen_x, screen_y - TILE_HEIGHT // 2))
    # ==========================================================

    # Afficher les ressources du joueur en haut de l'écran
    font = pygame.font.Font(None, 36)
    resources_info = (f"Bois: {game_state.player_ai.resources['Wood']} Or: {game_state.player_ai.resources['Gold']} "
                      f"Nourriture: {game_state.player_ai.resources['Food']} "
                      f"Population: {game_state.player_ai.population}/{game_state.player_ai.population_max}")
    resources_text = font.render(resources_info, True, (255, 255, 255))
    screen.blit(resources_text, (20, 20))
    
    # ========== NOUVEAU : Afficher le camp du joueur ==========
    player_info = f"Vous jouez : {game_state.player_side}"
    player_text = font.render(player_info, True, game_state.get_player_color())
    screen.blit(player_text, (20, 60))
    # ===========================================================

    # Update the display
    pygame.display.flip()


# Fonction de gestion des entrées utilisateur
def handle_input_pygame(view_x, view_y, max_width, max_height, game_map):
    """
    Gère les entrées utilisateur pour se déplacer sur la carte.
    """
    keys = pygame.key.get_pressed()
    if keys[pygame.K_z] or keys[pygame.K_UP]:  # Z ou Flèche Haut - Se déplacer en avant
        view_y = max(0, view_y - 1)
        view_x = max(0, view_x - 1)
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:  # S ou Flèche Bas - Se déplacer en arrière
        view_y = min(game_map.height - max_height, view_y + 1)
        view_x = min(game_map.width - max_width, view_x + 1)
    if keys[pygame.K_q] or keys[pygame.K_LEFT]:  # Q ou Flèche Gauche - Se déplacer à gauche
        view_x = max(0, view_x - 1)
        view_y = min(game_map.height - max_height, view_y + 1)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:  # D ou Flèche Droite - Se déplacer à droite
        view_x = min(game_map.width - max_width, view_x + 1)
        view_y = max(0, view_y - 1)
    return view_x, view_y