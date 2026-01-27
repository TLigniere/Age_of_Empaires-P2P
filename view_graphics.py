import pygame
import os
import sys
from enum import Enum
import random

# Constants for screen dimensions and tile sizes
screen_width = 1920  # Increased screen width for better view
screen_height = 1080  # Increased screen height for better view
TILE_WIDTH = 64
TILE_HEIGHT = 32

# UI Constants
UI_HEIGHT = 150  # Height for UI panel at bottom
INFO_PANEL_WIDTH = 300  # Width for side info panel
FPS = 30

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (128, 128, 128)
COLOR_DARK_GRAY = (64, 64, 64)
COLOR_GREEN = (0, 200, 0)
COLOR_GOLD = (255, 215, 0)
COLOR_BROWN = (139, 69, 19)
COLOR_LIGHT_BLUE = (100, 149, 237)
COLOR_RED = (255, 0, 0)
COLOR_SELECTION = (255, 255, 0)
COLOR_PLAYER_J1 = (50, 100, 200)  # Bleu pour Joueur 1
COLOR_PLAYER_J2 = (200, 50, 50)   # Rouge pour Joueur 2

# Dictionary to hold loaded images
images = {}
selected_unit = None
selected_building = None


def load_or_create_placeholder(asset_path, size, color=COLOR_GRAY):
    """             
    Charge une image ou crée un placeholder coloré si le fichier n'existe pas.
    """
    try:
        if os.path.exists(asset_path):
            return pygame.transform.scale(pygame.image.load(asset_path).convert_alpha(), size)
    except pygame.error as e:
        print(f"Attention: Impossible de charger {asset_path}: {e}")
    
    # Créer un placeholder coloré
    surface = pygame.Surface(size)
    surface.fill(color)
    return surface


def create_tile_sprite(tile_type, size=(TILE_WIDTH, TILE_HEIGHT), color=COLOR_GRAY):
    """Crée un sprite de tuile simple en cas d'absence d'image."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    
    if tile_type == 'grass':
        pygame.draw.polygon(surface, COLOR_GREEN, [
            (size[0]//2, 0),
            (size[0], size[1]//2),
            (size[0]//2, size[1]),
            (0, size[1]//2)
        ])
    elif tile_type == 'wood':
        pygame.draw.circle(surface, COLOR_BROWN, (size[0]//2, size[1]//2), size[0]//4)
        pygame.draw.circle(surface, COLOR_GREEN, (size[0]//2, size[1]//2), size[0]//6)
    elif tile_type == 'gold':
        pygame.draw.circle(surface, COLOR_GOLD, (size[0]//2, size[1]//2), size[0]//4)
    
    return surface


def initialize_graphics():
    """Initialise Pygame et charge les ressources."""
    global images
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("AIge of EmpAIres - P2P Strategy Game")
    clock = pygame.time.Clock()
    
    # Charger ou créer les sprites
    images['grass'] = create_tile_sprite('grass')
    images['tree'] = create_tile_sprite('wood')
    images['gold'] = create_tile_sprite('gold')
    
    # Créer des placeholders pour les bâtiments et unités
    images['town_center'] = load_or_create_placeholder('assets/town_center.png', (TILE_WIDTH, TILE_HEIGHT*2), COLOR_LIGHT_BLUE)
    images['farm'] = load_or_create_placeholder('assets/farm.png', (TILE_WIDTH, TILE_HEIGHT*2), COLOR_BROWN)
    images['barracks'] = load_or_create_placeholder('assets/barracks.png', (TILE_WIDTH, TILE_HEIGHT*2), COLOR_RED)
    images['villager'] = load_or_create_placeholder('assets/villager.png', (TILE_WIDTH//2, TILE_HEIGHT), COLOR_LIGHT_BLUE)
    
    return screen


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
    # Créer un masque pour appliquer la couleur
    mask = pygame.Surface(colored_image.get_size())
    mask.fill(color)
    colored_image.blit(mask, (0, 0), special_flags=pygame.BLEND_MULT)
    return colored_image


def world_to_screen(x, y, view_x, view_y):
    """Convertit les coordonnées du monde en coordonnées d'écran (isométrique)."""
    screen_x = (x - y) * (TILE_WIDTH // 2) + (screen_width // 2) - (view_x - view_y) * (TILE_WIDTH // 2)
    screen_y = (x + y) * (TILE_HEIGHT // 2) - (view_x + view_y) * (TILE_HEIGHT // 2)
    return screen_x, screen_y


def render_map(screen, game_map, units, buildings, game_state, view_x, view_y, max_width, max_height):
    """
    Affiche la carte complète avec les tiles, ressources, bâtiments et unités.
    """
    if not isinstance(screen, pygame.Surface):
        raise TypeError(f"Expected screen to be a pygame.Surface, but got {type(screen)}")

    # Effacer l'écran
    screen.fill(COLOR_BLACK)

    # Afficher les tuiles de la carte
    render_height = min(max_height * 2, game_map.height)
    render_width = min(max_width * 2, game_map.width)
    
    for y in range(max(0, view_y - max_height), min(view_y + render_height, game_map.height)):
        for x in range(max(0, view_x - max_width), min(view_x + render_width, game_map.width)):
            screen_x, screen_y = world_to_screen(x, y, view_x, view_y)
            
            tile = game_map.grid[y][x]
            
            # Afficher la tuile de base
            screen.blit(images['grass'], (screen_x, screen_y))
            
            # Afficher les ressources
            if tile.resource == 'Wood':
                screen.blit(images['tree'], (screen_x, screen_y - TILE_HEIGHT // 2))
            elif tile.resource == 'Gold':
                screen.blit(images['gold'], (screen_x, screen_y))

    # Afficher les bâtiments
    for building in buildings:
        screen_x, screen_y = world_to_screen(building.x, building.y, view_x, view_y)
        
        # Déterminer la couleur selon le propriétaire
        if building.owner == 'J1':
            color = COLOR_PLAYER_J1  # Blue for Player 1
        else:
            color = COLOR_PLAYER_J2  # Red for Player 2
        
        if building.building_type == 'Town Center':
            colored_building = colorize_image(images['town_center'], color)
            screen.blit(colored_building, (screen_x - TILE_WIDTH//2, screen_y - TILE_HEIGHT))
        elif building.building_type == 'Farm':
            colored_building = colorize_image(images['farm'], color)
            screen.blit(colored_building, (screen_x - TILE_WIDTH//2, screen_y - TILE_HEIGHT))
        elif building.building_type == 'Barracks':
            colored_building = colorize_image(images['barracks'], color)
            screen.blit(colored_building, (screen_x - TILE_WIDTH//2, screen_y - TILE_HEIGHT))

    # Afficher les unités
    for unit in units:
        screen_x, screen_y = world_to_screen(unit.x, unit.y, view_x, view_y)
        
        # Déterminer la couleur selon le propriétaire
        if unit.owner == 'J1':
            color = COLOR_PLAYER_J1  # Blue for Player 1
        else:
            color = COLOR_PLAYER_J2  # Red for Player 2
        
        if unit.unit_type == 'Villager':
            colored_villager = colorize_image(images['villager'], color)
            screen.blit(colored_villager, (screen_x - TILE_WIDTH//4, screen_y - TILE_HEIGHT // 2))

    # Afficher les ressources du joueur
    render_ui(screen, game_state)
    
    # Mettre à jour l'affichage
    pygame.display.flip()


def render_ui(screen, game_state):
    """Affiche l'interface utilisateur (ressources, info joueur)."""
    font_large = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 24)
    
    # Afficher les ressources
    if game_state.player_ai:
        resources_info = (f"Bois: {game_state.player_ai.resources['Wood']} | "
                         f"Or: {game_state.player_ai.resources['Gold']} | "
                         f"Nourriture: {game_state.player_ai.resources['Food']} | "
                         f"Population: {game_state.player_ai.population}/{game_state.player_ai.population_max}")
        resources_text = font_large.render(resources_info, True, COLOR_WHITE)
        screen.blit(resources_text, (20, 20))
    
    # Afficher le camp du joueur
    player_info = f"Vous jouez : {game_state.player_side}"
    player_text = font_large.render(player_info, True, COLOR_PLAYER_J1 if game_state.player_side == 'J1' else COLOR_PLAYER_J2)
    screen.blit(player_text, (20, 60))
    
    # Afficher les contrôles
    controls = "ZQSD/Flèches: Déplacer | F12: Mode Terminal | Echap: Menu"
    controls_text = font_small.render(controls, True, COLOR_GRAY)
    screen.blit(controls_text, (20, screen_height - 40))


def handle_input_pygame(view_x, view_y, max_width, max_height, game_map):
    """
    Gère les entrées utilisateur pour naviguer sur la carte (isométrique).
    """
    keys = pygame.key.get_pressed()
    step = 1  # Distance de déplacement
    
    # Déplacements avec ZQSD ou flèches
    if keys[pygame.K_z] or keys[pygame.K_UP]:  # Avant
        view_y = max(0, view_y - step)
        view_x = max(0, view_x - step)
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:  # Arrière
        view_y = min(game_map.height - max_height, view_y + step)
        view_x = min(game_map.width - max_width, view_x + step)
    if keys[pygame.K_q] or keys[pygame.K_LEFT]:  # Gauche
        view_x = max(0, view_x - step)
        view_y = min(game_map.height - max_height, view_y + step)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:  # Droite
        view_x = min(game_map.width - max_width, view_x + step)
        view_y = max(0, view_y - step)
    
    return view_x, view_y
