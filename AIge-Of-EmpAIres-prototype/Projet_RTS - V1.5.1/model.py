import time
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


class Joueur:
    def __init__(self):
        self.resources = {
            'Wood': 200,
            'Gold': 100,
            'Food': 50
        }
        self.population = 0
        self.population_max = 5 
        self.victoire = False

    def update_resources(self, resource_type, amount):
        if resource_type in self.resources:
            self.resources[resource_type] += amount
            print(f"Ressources {resource_type} mises à jour : {self.resources[resource_type]}")

    def can_afford(self, cost):
        """Vérifie si le joueur peut se permettre de payer un coût spécifique."""
        return all(self.resources[res] >= cost.get(res, 0) for res in cost)

    def pay_resources(self, cost):
        """Déduit les ressources après un achat."""
        if self.can_afford(cost):
            for res in cost:
                self.resources[res] -= cost[res]
                print(f"Paiement de {cost[res]} unités de {res}. Restant : {self.resources[res]}")

    def update_population(self, change):
        self.population += change
        print(f"Population mise à jour : {self.population}/{self.population_max}")

    def set_victoire(self, status):
        self.victoire = status
        print(f"Victoire: {'Oui' if self.victoire else 'Non'}")



class Building:
    def __init__(self, building_type, x, y):
        self.building_type = building_type  # Par exemple, 'Town Center'
        self.x = x
        self.y = y
        self.resources = {
            'Wood': 0,
            'Gold': 0,
            'Food': 300
        }
        self.costs = {
            'Town Center': {'Wood': 200, 'Gold': 50},
            'House': {'Wood': 50, 'Gold': 0},
            'Barracks': {'Wood': 150, 'Gold': 50},
            'Farm': {'Wood': 60, 'Gold': 0}  # Coût de la ferme
        }
        self.population_capacity = 0  # Capacité maximale de population pour certains bâtiments
        self.occupied = False  # Assurez-vous que cet attribut est bien initialisé


    def get_construction_cost(self):
        """Renvoie le coût de construction pour ce type de bâtiment."""
        return self.costs.get(self.building_type, {'Wood': 0, 'Gold': 0})

    def deposit_resource(self, resource_type, amount):
        """Le villageois dépose des ressources dans le bâtiment (par exemple, un Town Center)."""
        if resource_type in self.resources:
            self.resources[resource_type] += amount
            print(f"{amount} unités de {resource_type} déposées au {self.building_type}.")

    def gather_food(self, amount):
        """Récolter une quantité spécifique de nourriture depuis la ferme."""
        if self.resources['Food'] > 0:
            gathered = min(amount, self.resources['Food'])
            self.resources['Food'] -= gathered
            return gathered
        return 0

    def is_empty(self):
        """Vérifie si la ferme est épuisée."""
        return self.resources['Food'] <= 0

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




class Unit:
    def __init__(self, unit_type, x, y, joueur):
        self.unit_type = unit_type
        self.x = x
        self.y = y
        self.joueur = joueur
        self.resource_collected = 0
        self.max_capacity = 50
        self.returning_to_town_center = False
        self.current_action = None
        self.working_farm = None
        self.current_resource = None
        self.target_path = None
        self.action_end_time = 0

    def move(self, new_x, new_y):
        self.x = new_x
        self.y = new_y

    def update(self, game_map, buildings):
        current_time = time.time()

        if self.current_action == 'moving_to_farm' and not self.target_path:
            if self.working_farm and not self.working_farm.is_empty():
                self.current_action = 'gathering_food'
                self.action_end_time = current_time + 5  # Simule la récolte pour 5 secondes
                print(f"{self.unit_type} commence la récolte de la ferme à ({self.working_farm.x}, {self.working_farm.y})")
            else:
                # La ferme est épuisée ou invalide
                print(f"Ferme à ({self.working_farm.x}, {self.working_farm.y}) est invalide ou épuisée. Réaffectation.")
                self.current_action = 'idle'
                self.working_farm = None

        elif self.current_action == 'gathering_food' and current_time >= self.action_end_time:
            if self.working_farm and not self.working_farm.is_empty():
                # Récolte de nourriture depuis la ferme
                food_gathered = self.working_farm.gather_food(min(20, self.max_capacity - self.resource_collected))
                if food_gathered > 0:
                    self.resource_collected += food_gathered
                    self.current_resource = 'Food'
                    print(f"{self.unit_type} a récolté {food_gathered} unités de nourriture à la ferme.")

                    # Vérifier s'il doit retourner ou continuer la récolte
                    if self.resource_collected >= self.max_capacity or self.working_farm.is_empty():
                        if self.working_farm.is_empty():
                            print(f"Ferme à ({self.working_farm.x}, {self.working_farm.y}) est maintenant épuisée.")
                        self.current_action = 'returning_to_town_center'
                        self.target_path = self.find_nearest_town_center(game_map, buildings)
                        self.working_farm.free()
                        self.working_farm = None
                        print(f"{self.unit_type} retourne au centre-ville pour déposer les ressources.")
                    else:
                        # Continue la récolte
                        self.action_end_time = current_time + 5
                else:
                    # Ferme épuisée
                    print(f"Ferme à ({self.working_farm.x}, {self.working_farm.y}) épuisée. Réaffectation.")
                    self.current_action = 'idle'
                    self.working_farm = None

        elif self.current_action == 'returning_to_town_center' and self.target_path:
            # Déplacement vers le Town Center
            next_step = self.target_path.pop(0)
            self.move(*next_step)

            if not self.target_path and self.position == self.target_town_center_position:
                print(f"{self.unit_type} est arrivé au Town Center pour déposer les ressources.")
                self.deposit_resource(self.target_building)
                self.current_action = 'idle'
                self.target_town_center_position = None
                self.target_building = None
                self.resource_collected = 0

        if self.current_action == 'idle':
            self.find_task(game_map)






    def gather_resource(self):
        if self.current_resource == 'Food' and self.working_farm:
            amount = min(20, self.working_farm.resources['Food'])
            self.resource_collected += amount
            self.working_farm.resources['Food'] -= amount
            print(f"{self.unit_type} a récolté {amount} unités de nourriture à la ferme à ({self.working_farm.x}, {self.working_farm.y})")
            if self.working_farm.resources['Food'] <= 0:
                print(f"La ferme à ({self.working_farm.x}, {self.working_farm.y}) est maintenant épuisée.")
                self.working_farm.free()
                self.working_farm = None
        elif self.current_resource == 'Wood':
            # Code similaire pour le bois
            pass
        elif self.current_resource == 'Gold':
            # Code similaire pour l'or
            pass


    def deposit_resource(self, building):
        if building and building.building_type == 'Town Center' and self.current_resource:
            building.deposit_resource(self.current_resource, self.resource_collected)
            self.joueur.update_resources(self.current_resource, self.resource_collected)
            self.resource_collected = 0
            print(f"{self.unit_type} a déposé des ressources au Town Center.")
            self.returning_to_town_center = False
            self.current_resource = None

    def gather_food_from_farm(self):
        """Récolte de la nourriture dans une ferme en continu jusqu'à épuisement."""
        if self.working_farm:
            if self.working_farm.is_empty():
                print(f"Ferme à ({self.working_farm.x}, {self.working_farm.y}) est épuisée.")
                self.working_farm.free()
                self.working_farm = None
                self.current_action = None
                return

            current_time = time.time()
            if current_time >= self.action_end_time:
                amount = min(20, self.max_capacity - self.resource_collected)
                food_gathered = self.working_farm.gather_food(amount)
                self.resource_collected += food_gathered
                self.current_resource = 'Food'
                print(f"{self.unit_type} récolte {food_gathered} unités de nourriture à la ferme.")

                if self.resource_collected >= self.max_capacity:
                    self.returning_to_town_center = True
                    self.working_farm.free()
                    self.working_farm = None
                else:
                    self.action_end_time = current_time + 5


    def find_nearest_farm(self, game_map, buildings):
        # Récupère toutes les fermes disponibles, non occupées
        available_farms = [building for building in buildings if building.building_type == 'Farm' and not building.is_occupied()]
        
        # Si aucune ferme n'est disponible
        if not available_farms:
            print("Aucune ferme disponible pour récolter de la nourriture.")
            return None

        # Trouver la ferme la plus proche en utilisant une distance de Manhattan
        current_position = (self.x, self.y)
        nearest_farm = min(available_farms, key=lambda farm: abs(farm.x - current_position[0]) + abs(farm.y - current_position[1]))

        # Utiliser la fonction de recherche de chemin pour trouver le chemin vers la ferme
        path = self.find_path(game_map, current_position, 'Farm', nearest_farm)

        if path:
            return path
        else:
            print(f"Aucun chemin trouvé vers la ferme à ({nearest_farm.x}, {nearest_farm.y})")
            return None







    def find_nearest_gold(self, game_map):
        """ Utilise une recherche de chemin pour trouver l'or le plus proche """
        path = self.find_path(game_map, (self.x, self.y), 'Gold')
        if path:
            pass
        else:
            print(f"Aucun chemin vers l'or trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_nearest_wood(self, game_map):
        """ Utilise une recherche de chemin pour trouver le bois le plus proche """
        path = self.find_path(game_map, (self.x, self.y), 'Wood')
        if path:
            pass
        else:
            print(f"Aucun chemin vers le bois trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_nearest_food(self, game_map):
        """ Utilise une recherche de chemin pour trouver la nourriture la plus proche """
        path = self.find_path(game_map, (self.x, self.y), 'Food')
        if path:
            pass
        else:
            print(f"Aucun chemin vers la nourriture trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_nearest_town_center(self, game_map, buildings):
        town_center = buildings[0]
        if (self.x, self.y) == (town_center.x, town_center.y):
            print(f"{self.unit_type} est déjà sur le Town Center.")
            return None

        path = self.find_path(game_map, (self.x, self.y), 'Town Center', town_center)
        if path:
            path
        else:
            print(f"Aucun chemin vers le Town Center trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_path(self, game_map, start, target_type, target_building=None):
        """
        Recherche un chemin vers une destination donnée (bois, or, ou bâtiment spécifique).
        `start`: Point de départ (coordonnée).
        `target_type`: Type de cible ('Wood', 'Gold', 'Farm', 'Town Center').
        `target_building`: Utilisé si le bâtiment spécifique est la cible (par exemple, Town Center).
        """
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Distance de Manhattan

        open_list = []
        heapq.heappush(open_list, (0, start))  # Ajouter la position initiale
        came_from = {}
        cost_so_far = {start: 0}

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Gauche, Droite, Haut, Bas

        while open_list:
            _, current = heapq.heappop(open_list)

            # Vérification pour le type de cible
            if target_type == 'Wood' and game_map.grid[current[1]][current[0]].resource == 'Wood':
                print(f"Bois trouvé à {current}")  # Log la position du bois trouvé
                return self.reconstruct_path(came_from, current)

            if target_type == 'Gold' and game_map.grid[current[1]][current[0]].resource == 'Gold':
                print(f"Or trouvé à {current}")  # Log la position de l'or trouvé
                return self.reconstruct_path(came_from, current)

            if target_type == 'Farm' and game_map.grid[current[1]][current[0]].building and game_map.grid[current[1]][current[0]].building.building_type == 'Farm':
                print(f"Ferme trouvée à {current}")  # Log la position de la ferme trouvée
                return self.reconstruct_path(came_from, current)

            if target_type == 'Town Center' and target_building and (current[0], current[1]) == (target_building.x, target_building.y):
                print(f"Town Center trouvé à {current}")  # Log la position du Town Center trouvé
                return self.reconstruct_path(came_from, current)

            # Exploration des voisins
            for dx, dy in directions:
                next_node = (current[0] + dx, current[1] + dy)
                if 0 <= next_node[0] < game_map.width and 0 <= next_node[1] < game_map.height:
                    new_cost = cost_so_far[current] + 1
                    if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                        cost_so_far[next_node] = new_cost
                        priority = new_cost + heuristic(next_node, start)
                        heapq.heappush(open_list, (priority, next_node))
                        came_from[next_node] = current

        # Si aucun chemin n'a été trouvé
        print(f"Aucun chemin trouvé pour {target_type} à partir de {start}")
        return []  # Retourner une liste vide au lieu de None pour signaler l'absence de chemin


    def reconstruct_path(self, came_from, current):
        """ Recrée le chemin à partir de la position courante """
        path = []
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.reverse()  # On inverse le chemin pour partir de la position de départ
        return path
