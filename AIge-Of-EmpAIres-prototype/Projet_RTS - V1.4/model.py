import random
import heapq  # Pour la recherche de chemin

class Tile:
    def __init__(self, resource=None, building=None):
        self.resource = resource  # Peut être 'Wood', 'Gold', ou None pour une tuile vide
        self.building = building  # Peut contenir un bâtiment comme un Town Center

class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[Tile() for _ in range(width)] for _ in range(height)]

    def generate_forest_clusters(self, num_clusters, cluster_size):
        for _ in range(num_clusters):
            start_x = random.randint(0, self.width - 1)
            start_y = random.randint(0, self.height - 1)
            self._create_cluster(start_x, start_y, cluster_size, 'Wood')

    def generate_gold_clusters(self, num_clusters):
        for _ in range(num_clusters):
            start_x = random.randint(0, self.width - 1)
            start_y = random.randint(0, self.height - 1)
            cluster_size = random.randint(3, 10)
            self._create_cluster(start_x, start_y, cluster_size, 'Gold')

    def _create_cluster(self, x, y, size, resource_type):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (-1, 1), (1, -1)]
        tiles_to_fill = set([(x, y)])  # Utiliser un ensemble pour améliorer les performances

        while tiles_to_fill and size > 0:
            current_x, current_y = tiles_to_fill.pop()
            if 0 <= current_x < self.width and 0 <= current_y < self.height:  #passer en assert
                if self.grid[current_y][current_x].resource is None and self.grid[current_y][current_x].building is None:
                    self.grid[current_y][current_x].resource = resource_type
                    size -= 1

                    random.shuffle(directions)  # Mélanger les directions pour rendre la forme plus organique
                    for dx, dy in directions:
                        new_x, new_y = current_x + dx, current_y + dy
                        if (new_x, new_y) not in tiles_to_fill and 0 <= new_x < self.width and 0 <= new_y < self.height:
                            tiles_to_fill.add((new_x, new_y))

    def place_building(self, building, x, y):
        """ Place un bâtiment sur une tuile donnée """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x].building = building
            print(f"Bâtiment {building.building_type} placé à ({x}, {y})")

class Building:
    def __init__(self, building_type, x, y):
        self.building_type = building_type  # Par exemple, 'Town Center'
        self.x = x
        self.y = y
        self.resources = {
            'Wood': 0,
            'Gold': 0,
            'Food': 0
        }
        self.costs = {
            'Town Center': {'Wood': 200, 'Gold': 50},
            'House': {'Wood': 50, 'Gold': 0},
            'Barracks': {'Wood': 150, 'Gold': 50},
            'Farm': {'Wood': 60, 'Gold': 0}  # Coût de la ferme
        }
        self.population_capacity = 0  # Capacité maximale de population pour certains bâtiments
        self.occupied = False  # Assurez-vous que cet attribut est bien initialisé

        # Ajuster la capacité selon le type de bâtiment
        if self.building_type == 'House':
            self.population_capacity = 5  # Chaque maison ajoute de la population
        if self.building_type == 'Farm':
            self.food_capacity = 300  # Chaque ferme contient 300 unités de nourriture

    def get_construction_cost(self):
        """Renvoie le coût de construction pour ce type de bâtiment."""
        return self.costs.get(self.building_type, {'Wood': 0, 'Gold': 0})

    def deposit_resource(self, resource_type, amount):
        """Le villageois dépose des ressources dans le bâtiment (par exemple, un Town Center)."""
        if resource_type in self.resources:
            self.resources[resource_type] += amount
            print(f"{amount} unités de {resource_type} déposées au {self.building_type}.")

    def gather_food(self, amount):
        if self.food_capacity > 0:
            gathered = min(amount, self.food_capacity)
            self.food_capacity -= gathered
            return gathered
        return 0

    def is_empty(self):
        return self.food_capacity <= 0

    def is_occupied(self):
        """Vérifie si la ferme est occupée par un villageois."""
        return self.occupied

    def occupy(self):
        """Marque la ferme comme étant occupée."""
        self.occupied = True

    def free(self):
        """Libère la ferme pour qu'un autre villageois puisse l'utiliser."""
        self.occupied = False

    def __repr__(self):
        return f"<{self.building_type} at ({self.x}, {self.y})>"


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

class Unit:
    def __init__(self, unit_type, x, y):
        self.unit_type = unit_type  # Par exemple : 'Villager'
        self.x = x  # Position x sur la carte
        self.y = y  # Position y sur la carte
        self.resource_collected = 0  # Quantité de ressources que l'unité a collectée
        self.max_capacity = 50  # Quantité maximale que le villageois peut porter
        self.returning_to_town_center = False  # Si le villageois retourne au Town Center pour déposer les ressources
        self.current_resource = None  # Type de ressource en train d'être collectée
        self.working_farm = None  # Référence à la ferme sur laquelle le villageois travaille

    def move(self, new_x, new_y):
        self.x = new_x
        self.y = new_y

    def gather_resource(self, game_map):
        """ Récolte une ressource si le villageois est sur une case contenant une ressource """
        tile = game_map.grid[self.y][self.x]
        if tile.resource:
            resource_type = tile.resource
            amount = min(20, self.max_capacity - self.resource_collected)
            self.resource_collected += amount  # Récolte 20 unités de ressource (ou moins si la capacité max est atteinte)
            print(f"{self.unit_type} récolte {amount} unités de {resource_type} à ({self.x}, {self.y}).")
            self.current_resource = resource_type  # Stocke le type de ressource
            if self.resource_collected >= self.max_capacity:
                print(f"{self.unit_type} a atteint sa capacité maximale en {resource_type}.")
                self.returning_to_town_center = True  # Le villageois retourne au Town Center
            tile.resource = None  # La ressource est épuisée sur cette case

    def gather_food_from_farm(self):
        """Récolte de la nourriture dans une ferme."""
        if self.working_farm:
            if self.working_farm.is_empty():
                print(f"Ferme à ({self.working_farm.x}, {self.working_farm.y}) est épuisée.")
                self.working_farm.free()  # Libérer la ferme lorsqu'elle est épuisée
                self.working_farm = None  # Ne plus travailler dans cette ferme
                return  # Arrêter immédiatement la récolte

            # Si la ferme n'est pas occupée, le villageois commence à travailler
            if not self.working_farm.is_occupied():
                self.working_farm.occupy()  # Marquer la ferme comme occupée
                amount = min(20, self.max_capacity - self.resource_collected)
                food_gathered = self.working_farm.gather_food(amount)
                self.resource_collected += food_gathered
                self.current_resource = 'Food'
                print(f"{self.unit_type} récolte {food_gathered} unités de nourriture à la ferme.")

                if self.resource_collected >= self.max_capacity:
                    print(f"{self.unit_type} a atteint sa capacité maximale en nourriture.")
                    self.returning_to_town_center = True
                    self.working_farm.free()  # Libérer la ferme après avoir atteint la capacité maximale
                    self.working_farm = None  # Ne plus travailler dans cette ferme

    def deposit_resource(self, building):
        """Le villageois dépose les ressources au Town Center."""
        if building and building.building_type == 'Town Center' and self.current_resource:
            building.deposit_resource(self.current_resource, self.resource_collected)
            self.resource_collected = 0  # Le villageois a déposé toutes les ressources
            print(f"{self.unit_type} a déposé des ressources au Town Center.")
            self.returning_to_town_center = False  # Le villageois reprend la collecte
            self.current_resource = None  # Réinitialiser la ressource collectée

    def find_nearest_farm(self, game_map):
        """Recherche la ferme la plus proche qui contient de la nourriture et qui n'est pas occupée."""
        path = self.find_path(game_map, (self.x, self.y), 'Farm')
        if path:
            # Récupération de la tuile et du bâtiment sur cette tuile
            farm_tile = game_map.grid[path[-1][1]][path[-1][0]]
            if farm_tile.building and not farm_tile.building.is_occupied() and not farm_tile.building.is_empty():
                print(f"Chemin trouvé vers la ferme à ({path[-1][0]}, {path[-1][1]})")
                return path
            else:
                print(f"La ferme à ({path[-1][0]}, {path[-1][1]}) est occupée ou épuisée.")
                return None
        else:
            print(f"Aucun chemin vers une ferme trouvé pour {self.unit_type} à ({self.x}, {self.y})")
            return None


    def find_nearest_gold(self, game_map):
        """ Utilise une recherche de chemin pour trouver l'or le plus proche """
        path = self.find_path(game_map, (self.x, self.y), 'Gold')
        if path:
            print(f"Chemin trouvé vers l'or : ") #{path}
        else:
            print(f"Aucun chemin vers l'or trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_nearest_wood(self, game_map):
        """ Utilise une recherche de chemin pour trouver le bois le plus proche """
        path = self.find_path(game_map, (self.x, self.y), 'Wood')
        if path:
            print(f"Chemin trouvé vers le bois : ") #{path}
        else:
            print(f"Aucun chemin vers le bois trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_nearest_food(self, game_map):
        """ Utilise une recherche de chemin pour trouver la nourriture la plus proche """
        path = self.find_path(game_map, (self.x, self.y), 'Food')
        if path:
            print(f"Chemin trouvé vers la nourriture : ") #{path}
        else:
            print(f"Aucun chemin vers la nourriture trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_nearest_town_center(self, game_map, buildings):
        """ Recherche du chemin vers le Town Center le plus proche """
        town_center = buildings[0]
        # Si le villageois est déjà sur la même tuile que le Town Center
        if (self.x, self.y) == (town_center.x, town_center.y):
            print(f"{self.unit_type} est déjà sur le Town Center.")
            return None  # Pas besoin de trouver un chemin

        path = self.find_path(game_map, (self.x, self.y), 'Town Center', town_center)
        if path:
            print(f"Chemin trouvé vers le Town Center : {path}")
        else:
            print(f"Aucun chemin vers le Town Center trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_path(self, game_map, start, target_type, target_building=None):
        """ Recherche un chemin vers une destination donnée (bois, or, ou bâtiment spécifique) """
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Distance Manhattan

        open_list = []
        heapq.heappush(open_list, (0, start))  # Ajouter la position initiale
        came_from = {}
        cost_so_far = {start: 0}

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Gauche, Droite, Haut, Bas

        while open_list:
            _, current = heapq.heappop(open_list)

            # Vérification pour le bois
            if target_type == 'Wood' and game_map.grid[current[1]][current[0]].resource == 'Wood':
                print(f"Bois trouvé à {current}")  # Log la position du bois trouvé
                return self.reconstruct_path(came_from, current)  # Retourner le chemin trouvé

            # Vérification pour l'or
            if target_type == 'Gold' and game_map.grid[current[1]][current[0]].resource == 'Gold':
                print(f"Or trouvé à {current}")  # Log la position de l'or trouvé
                return self.reconstruct_path(came_from, current)  # Retourner le chemin trouvé

            # Vérification pour le Town Center
            if target_type == 'Town Center' and target_building and (current[0], current[1]) == (target_building.x, target_building.y):
                print(f"Town Center trouvé à {current}")  # Log la position du Town Center trouvé
                return self.reconstruct_path(came_from, current)

            # Vérification pour une ferme
            if target_type == 'Farm' and isinstance(game_map.grid[current[1]][current[0]].building, Building) and game_map.grid[current[1]][current[0]].building.building_type == 'Farm':
                print(f"Ferme trouvée à {current}")  # Log la position de la ferme trouvée
                return self.reconstruct_path(came_from, current)

            # Exploration des voisins
            for dx, dy in directions:
                next_node = (current[0] + dx, current[1] + dy)
                if 0 <= next_node[0] < game_map.width and 0 <= next_node[1] < game_map.height:
                    new_cost = cost_so_far[current] + 1
                    if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                        cost_so_far[next_node] = new_cost
                        priority = new_cost + heuristic(next_node, (self.x, self.y))
                        heapq.heappush(open_list, (priority, next_node))
                        came_from[next_node] = current

        print(f"Aucun chemin trouvé pour {target_type}")
        return None

    def reconstruct_path(self, came_from, current):
        """ Recrée le chemin à partir de la position courante """
        path = []
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.reverse()  # On inverse le chemin pour partir de la position de départ
        return path
