import pygame
import sys
import time
from model import Map, Unit, Building

# Constants for the game
tile_size = 40
screen_width = 1600
screen_height = 900

# Initialize PyGame
pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("RTS Game")

# Load images for the game
def load_images():
    wood_img = pygame.image.load('images/wood.png').convert_alpha()
    gold_img = pygame.image.load('images/gold.png').convert_alpha()
    town_center_img = pygame.image.load('images/town_center.png').convert_alpha()
    villager_img = pygame.image.load('images/villager.png').convert_alpha()
    grass_img = pygame.image.load('images/grass.png').convert_alpha()  # Load grass image

    # Resize images to match the tile size
    wood_img = pygame.transform.scale(wood_img, (tile_size, tile_size))
    gold_img = pygame.transform.scale(gold_img, (tile_size, tile_size))
    town_center_img = pygame.transform.scale(town_center_img, (tile_size, tile_size))
    villager_img = pygame.transform.scale(villager_img, (tile_size, tile_size))
    grass_img = pygame.transform.scale(grass_img, (tile_size, tile_size))  # Resize grass image

    return {
        'Wood': wood_img,
        'Gold': gold_img,
        'Town Center': town_center_img,
        'Villager': villager_img,
        'Grass': grass_img  # Include grass image in the dictionary
    }
# Render the game map on the screen
def render_map(screen, game_map, units, buildings, view_x, view_y, max_width, max_height):
    screen.fill((0, 0, 0))  # Clear screen with black color
    images = load_images()

    # Render visible portion of the map
    for y in range(view_y, min(view_y + max_height, game_map.height)):
        for x in range(view_x, min(view_x + max_width, game_map.width)):
            tile = game_map.grid[y][x]
            tile_pos = (x - view_x) * tile_size, (y - view_y) * tile_size  # Adjust position based on view

            # Display grass for empty tiles
            screen.blit(images['Grass'], tile_pos)

            # Display resources
            if tile.resource == 'Wood':
                screen.blit(images['Wood'], tile_pos)
            elif tile.resource == 'Gold':
                screen.blit(images['Gold'], tile_pos)

            # Display buildings
            if tile.building and tile.building.building_type == 'Town Center':
                screen.blit(images['Town Center'], tile_pos)

    # Render units
    for unit in units:
        if view_x <= unit.x < view_x + max_width and view_y <= unit.y < view_y + max_height:
            unit_pos = (unit.x - view_x) * tile_size, (unit.y - view_y) * tile_size
            screen.blit(images['Villager'], unit_pos)

    pygame.display.flip()  # Update the screen

# Handle user input for scrolling the map
def handle_input_pygame(view_x, view_y, max_width, max_height, game_map):
    """Gère les touches ZQSD pour le scrolling en mode Pygame."""
    keys = pygame.key.get_pressed()

    if keys[pygame.K_z]:
        view_y = max(0, view_y - 1)
        print(f"Moving up, view_y: {view_y}")
    if keys[pygame.K_s]:
        view_y = min(game_map.height - max_height, view_y + 1)
        print(f"Moving down, view_y: {view_y}")
    if keys[pygame.K_q]:
        view_x = max(0, view_x - 1)
        print(f"Moving left, view_x: {view_x}")
    if keys[pygame.K_d]:
        view_x = min(game_map.width - max_width, view_x + 1)
        print(f"Moving right, view_x: {view_x}")

    return view_x, view_y


# Main game loop for graphical mode
def game_loop(units, buildings, game_map, ai, delay=0.1):
    running = True
    clock = pygame.time.Clock()
    view_x, view_y = 0, 0  # Start with the camera at the top-left
    max_width = screen_width // tile_size
    max_height = screen_height // tile_size
    last_update_time = time.time()

    while running:
        current_time = time.time()

        # Event handling (closing the game)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Scroll the map using ZQSD
        view_x, view_y = handle_input_pygame(view_x, view_y, max_width, max_height, game_map)

        # Update units every 'delay' seconds
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

            # Let AI manage population and buildings
            ai.update_population()
            ai.build(game_map)

            last_update_time = current_time

        # Render the map and units
        render_map(screen, game_map, units, buildings, view_x, view_y, max_width, max_height)

        # Handle quitting or switching modes
        keys = pygame.key.get_pressed()
        if keys[pygame.K_F12]:  # Switch back to terminal mode
            pygame.quit()
            sys.exit()  # Exits graphical mode

        clock.tick(30)  # Limit to 30 FPS

    pygame.quit()
