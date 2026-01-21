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
            cluster_size = random.randint(4, 6)
            self._create_cluster(start_x, start_y, cluster_size, 'Gold')

    def _create_cluster(self, x, y, size, resource_type):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (-1, 1), (1, -1)]
        tiles_to_fill = set([(x, y)])  # Utiliser un ensemble pour améliorer les performances

        while tiles_to_fill and size > 0:
            current_x, current_y = tiles_to_fill.pop()
            if 0 <= current_x < self.width and 0 <= current_y < self.height:
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
        self.resources = {'Wood': 0, 'Food': 0}  # Le Town Center stocke les ressources

    def deposit_resource(self, resource_type, amount):
        """ Le villageois dépose des ressources dans le Town Center """
        if resource_type in self.resources:
            self.resources[resource_type] += amount
            print(f"{amount} unités de {resource_type} déposées au {self.building_type}.")


class Unit:
    def __init__(self, unit_type, x, y):
        self.unit_type = unit_type  # Par exemple : 'Villager'
        self.x = x  # Position x sur la carte
        self.y = y  # Position y sur la carte
        self.wood_collected = 0  # Quantité de bois que l'unité a collecté
        self.max_capacity = 50  # Quantité maximale que le villageois peut porter
        self.returning_to_town_center = False  # Si le villageois retourne au Town Center pour déposer le bois

    def move(self, new_x, new_y):
        print(f"{self.unit_type} se déplace de ({self.x}, {self.y}) à ({new_x}, {new_y})")
        self.x = new_x
        self.y = new_y

    def gather_wood(self, game_map):
        """ Récolte du bois si le villageois est sur une case contenant du bois """
        if game_map.grid[self.y][self.x].resource == 'Wood':
            amount = min(20, self.max_capacity - self.wood_collected)
            self.wood_collected += amount  # Récolte 20 unités de bois (ou moins si la capacité max est atteinte)
            print(f"{self.unit_type} récolte {amount} unités de bois à ({self.x}, {self.y}).")
            if self.wood_collected >= self.max_capacity:
                print(f"{self.unit_type} a atteint sa capacité maximale en bois.")
                self.returning_to_town_center = True  # Le villageois retourne au Town Center
            game_map.grid[self.y][self.x].resource = None  # Le bois est épuisé sur cette case

    def deposit_wood(self, building):
        """ Le villageois dépose le bois au Town Center """
        if building and building.building_type == 'Town Center':
            building.deposit_resource('Wood', self.wood_collected)
            self.wood_collected = 0  # Le villageois a déposé tout le bois
            print(f"{self.unit_type} a déposé du bois au Town Center.")
            self.returning_to_town_center = False  # Le villageois reprend la collecte de bois

    def find_nearest_wood(self, game_map):
        """ Utilise une recherche de chemin pour trouver le bois le plus proche """
        return self.find_path(game_map, (self.x, self.y), 'Wood')

    def find_nearest_town_center(self, game_map, buildings):
        """ Recherche du chemin vers le Town Center le plus proche """
        town_center = buildings[0]  # Suppose qu'il n'y a qu'un seul Town Center
        return self.find_path(game_map, (self.x, self.y), 'Town Center', town_center)

    def find_path(self, game_map, start, target_type, target_building=None):
        """ Recherche un chemin vers une destination donnée (bois ou Town Center) """
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Distance Manhattan
        #   return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5  # Distance Euclidienne

        open_list = []
        heapq.heappush(open_list, (0, start))  # Ajouter la position initiale
        came_from = {}
        cost_so_far = {start: 0}

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Gauche, Droite, Haut, Bas

        while open_list:
            _, current = heapq.heappop(open_list)

            if target_type == 'Wood' and game_map.grid[current[1]][current[0]].resource == 'Wood':
                print(f"Bois trouvé à {current}")  # Log la position du bois trouvé
                return self.reconstruct_path(came_from, current)  # Retourner le chemin trouvé

            if target_type == 'Town Center' and target_building and (current[0], current[1]) == (target_building.x, target_building.y):
                print(f"Town Center trouvé à {current}")  # Log la position du Town Center trouvé
                return self.reconstruct_path(came_from, current)

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
