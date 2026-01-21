import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model import Building, Unit, Tile, Map



class AIStrategy:
    def execute(self, units, buildings, game_map, ai):
        """
        Exécute la stratégie pour une mise à jour du jeu.

        Args:
            units (list): Liste des unités du jeu.
            buildings (list): Liste des bâtiments du jeu.
            game_map (Map): Carte du jeu.
            ai (AI): L'objet représentant l'IA du joueur.
        """
        raise NotImplementedError("Cette méthode doit être implémentée par chaque stratégie.")


#-------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------
#---------Classe pour les comportements communs à chaque stratégie IA
#-------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------
class AI:
    def __init__(self, buildings, units):
        self.buildings = buildings
        self.units = units
        self.population = len(units)
        self.population_max = 4  # Commence avec un Town Center et une limite de 5
        self.town_center = buildings[0]  # Suppose qu'il n'y a qu'un seul Town Center

    def should_build_farm(self):
        """Vérifie si l'IA doit construire une ferme."""
        # Vérifie le nombre de fermes déjà construites
        farm_count = sum(1 for building in self.buildings if building.building_type == 'Farm')
        return farm_count < self.max_farms and self.town_center.resources['Wood'] >= 60  # Exemple : 60 bois pour une ferme

    def is_food_low(self):
        """Vérifie si la nourriture disponible est faible."""
        return self.town_center.resources['Food'] < 100  # Si la nourriture est inférieure à 100, c'est considéré comme faible

    def construct_building(self, building_type, game_map):
        """Construire un bâtiment si les ressources le permettent."""
        building = Building(building_type, 0, 0)  # Position temporaire
        construction_cost = building.get_construction_cost()

        # Vérifier les ressources dans le Town Center
        if (self.town_center.resources['Wood'] >= construction_cost['Wood'] and
            self.town_center.resources['Gold'] >= construction_cost['Gold']):

            # Trouver un emplacement libre pour construire le bâtiment
            build_x, build_y = self.find_free_tile_near_town_center(game_map)

            if build_x is not None and build_y is not None:
                # Déduire les ressources
                self.town_center.resources['Wood'] -= construction_cost['Wood']
                self.town_center.resources['Gold'] -= construction_cost['Gold']

                # Ajouter le bâtiment à l'emplacement trouvé
                new_building = Building(building_type, build_x, build_y)
                game_map.place_building(new_building, build_x, build_y)
                self.buildings.append(new_building)
                print(f"IA construit {building_type} à ({build_x}, {build_y})")
            else:
                print("Pas d'emplacement libre pour construire.")

    def should_build_farm(self):
        """Vérifie si l'IA doit construire une ferme."""
        return self.town_center.resources['Wood'] >= 60  # Exemple : il faut 60 de bois pour construire une ferme

    def build(self, game_map):
        """L'IA décide automatiquement quel bâtiment construire en fonction des besoins."""
        if self.should_build_house():
            self.construct_building('House', game_map)
        elif self.should_build_farm():
            self.construct_building('Farm', game_map)

    def find_free_tile_near_town_center(self, game_map):
        """Trouve une tuile vide à 2 cases autour du Town Center où placer un bâtiment."""
        directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]  # 2 cases autour du Town Center
        for dx, dy in directions:
            new_x, new_y = self.town_center.x + dx, self.town_center.y + dy
            if 0 <= new_x < game_map.width and 0 <= new_y < game_map.height: #si limite a 4 fermes + bord de map, bien verifier Ia contruct farm
                tile = game_map.grid[new_y][new_x]
                if tile.building is None and tile.resource is None:
                    return new_x, new_y
        return None, None

    def update_population(self):
        """Met à jour la population maximale en fonction des maisons construites."""
        self.population_max = 5  # Réinitialiser pour recalculer
        for building in self.buildings:
            self.population_max += building.population_capacity

    def should_build_house(self):
        """Vérifie si l'IA doit construire une maison pour augmenter la population."""
        return self.population >= self.population_max

    def should_build_barracks(self):
        """Vérifie si l'IA doit construire une caserne."""
        return not any(b.building_type == 'Barracks' for b in self.buildings)