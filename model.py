import random
import heapq  # Pour la recherche de chemin
import time
from view import Print_Display
import network

Joueur = "J1"  # Variable globale pour le joueur actuel


class GameElement:
    """Represents a game element with network control capabilities"""

    def __init__(self, id, owner=None):
        self.id = id
        self.owner = owner  # Logical owner
        self.network_owner = owner  # Network control owner
        self.state = {}  # Element state

    def can_modify(self, player):
        return self.network_owner == player

    def modify(self, player, changes):
        if self.can_modify(player):
            self.state.update(changes)
            return True
        return False


class Tile:
    def __init__(self):
        self.resource = None  # Peut être une ressource comme 'Wood', 'Gold', etc.
        self.building = None  # Référence à un objet Building s'il y en a un
        self.unit = None  # Référence à un objet Unit s'il y en a une
    
    def send_to_network(self, x, y):
        return f"type:'MAP_UPDATE',action:'PLACE_TILE',x:{x},y:{y},resource:{self.resource},building:{self.building},unit:{self.unit}"
    
    def delete_ressource_network(self, x, y):
        self.resource = None
        #Print_Display(str(network.client))
        try:
            network.send_simple_message_to_c(network.client, "UPDATE_MAP", f"action:'DELETE_RESOURCE',x:{x},y:{y}")
        except Exception as e:
            Print_Display(f"[ERROR] Failed to send DELETE_RESOURCE message: {e}")
    
    



class Map:
    def __init__(self, width, height, seed=4173):
        self.width = width
        self.height = height
        self.grid = [
            [Tile() for _ in range(width)] for _ in range(height)
        ]  # Assume qu'une classe Tile est définie
        self.seed = seed
        self.rng = random.Random(seed)

    # Nouvelle méthode is_empty
    def is_empty(self, x, y):
        """Vérifie si une position donnée est libre (sans bâtiment, ressource ou unité)."""
        # Vérifier que les coordonnées sont dans les limites de la carte
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False  # La position est hors de la carte

        tile = self.grid[y][x]

        # Vérifie si la case ne contient ni ressource ni bâtiment
        return not tile.resource and not tile.building and not tile.unit

    def generate_forest_clusters(self, num_clusters, cluster_size):
        for _ in range(num_clusters):
            start_x = self.rng.randint(0, self.width - 1)
            start_y = self.rng.randint(0, self.height - 1)
            self._create_cluster(start_x, start_y, cluster_size, "Wood")

    def generate_gold_clusters(self, num_clusters):
        for _ in range(num_clusters):
            start_x = self.rng.randint(0, self.width - 1)
            start_y = self.rng.randint(0, self.height - 1)
            cluster_size = self.rng.randint(3, 10)
            self._create_cluster(start_x, start_y, cluster_size, "Gold")

    def _create_cluster(self, x, y, size, resource_type):
        directions = [
            (0, 1),
            (1, 0),
            (0, -1),
            (-1, 0),
            (1, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
        ]
        tiles_to_fill = set(
            [(x, y)]
        )  # Utiliser un ensemble pour améliorer les performances

        while tiles_to_fill and size > 0:
            current_x, current_y = tiles_to_fill.pop()
            if (
                0 <= current_x < self.width and 0 <= current_y < self.height
            ):  # passer en assert
                if (
                    self.grid[current_y][current_x].resource is None
                    and self.grid[current_y][current_x].building is None
                ):
                    self.grid[current_y][current_x].resource = resource_type
                    size -= 1

                    self.rng.shuffle(
                        directions
                    )  # Mélanger les directions pour rendre la forme plus organique
                    for dx, dy in directions:
                        new_x, new_y = current_x + dx, current_y + dy
                        if (
                            (new_x, new_y) not in tiles_to_fill
                            and 0 <= new_x < self.width
                            and 0 <= new_y < self.height
                        ):
                            tiles_to_fill.add((new_x, new_y))

    def place_building(self, building, x, y):
        """Place un bâtiment sur une tuile donnée"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x].building = building
            if building.building_type == "Farm":
                self.grid[y][x].resource = "Food"

    def to_network_message(self):
        return (
            f"type:'MAP_INIT',seed:{self.seed},width:{self.width},height:{self.height}"
        )

    def place_tile(self, tile, x, y):
        """Place une tuile personnalisée à une position donnée"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = tile


class Building:
    def __init__(self, building_type, x, y, owner=None):
        self.building_type = building_type  # Par exemple, 'Town Center'
        self.x = x
        self.y = y
        self.owner = (
            owner if owner is not None else Joueur
        )  # Utilise Joueur si owner n'est pas fourni
        self.resources = {"Wood": 0, "Gold": 0, "Food": 0}
        self.costs = {
            "Town Center": {"Wood": 200, "Gold": 50},
            "House": {"Wood": 50, "Gold": 0},
            "Barracks": {"Wood": 150, "Gold": 50},
            "Farm": {"Wood": 60, "Gold": 0},  # Coût de la ferme
        }
        self.population_capacity = (
            0  # Capacité maximale de population pour certains bâtiments
        )
        self.occupied = False  # Assurez-vous que cet attribut est bien initialisé

        # Ajuster la capacité selon le type de bâtiment
        if self.building_type == "House":
            self.population_capacity = 5  # Chaque maison ajoute de la population
        if self.building_type == "Farm":
            self.food_capacity = 300  # Chaque ferme contient 300 unités de nourriture

    def get_construction_cost(self):
        """Renvoie le coût de construction pour ce type de bâtiment."""
        return self.costs.get(self.building_type, {"Wood": 0, "Gold": 0})

    def gather_food(self, amount):
        """Récolte la nourriture de la ferme jusqu'à épuisement."""
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

    def to_network_message(self):
        return f"type:{self.building_type},x:{self.x},y:{self.y},owner:{self.owner}"


class Unit:
    _NEXT_NETWORK_ID = 1

    def __init__(
        self, unit_type, x, y, ai, owner=None, network_id=None, is_remote=False
    ):
        if network_id is None:
            self.network_id = Unit._NEXT_NETWORK_ID
            Unit._NEXT_NETWORK_ID += 1
        else:
            self.network_id = network_id
        self.is_remote = is_remote  # True si l'unité est synchronisée depuis le réseau (joueur distant)
        self.unit_type = unit_type  # Par exemple : 'Villager'
        self.x = x  # Position x sur la carte
        self.y = y  # Position y sur la carte
        self.ai = ai
        self.owner = (
            owner if owner is not None else Joueur
        )  # Utilise Joueur si owner n'est pas fourni
        self.resource_collected = 0  # Quantité de ressources que l'unité a collectée
        self.max_capacity = 20  # Quantité maximale que le villageois peut porter
        self.returning_to_town_center = False  # Si le villageois retourne au Town Center pour déposer les ressources
        self.current_resource = None  # Type de ressource en train d'être collectée
        self.working_farm = (
            None  # Référence à la ferme sur laquelle le villageois travaille
        )

    def move(self, new_x, new_y):
        self.x = new_x
        self.y = new_y
        # Network message would be sent from controller level
    


    def gather_resource(self, game_map):
        """Récolte une ressource si le villageois est sur une case contenant une ressource"""
        tile = game_map.grid[self.y][self.x]
        if tile.resource:
            if not hasattr(tile, "element"):
                tile.element = GameElement(tile.resource, owner=self.ai)

            element = tile.element
            element.network_owner = self.ai

            amount_to_gather = min(20, self.max_capacity - self.resource_collected)
            success = element.modify(
                self.ai,
                {"amount": min(20, self.max_capacity - self.resource_collected)},
            )
            if success:
                gathered_amount = min(20, self.max_capacity - self.resource_collected)
                self.resource_collected += gathered_amount
                self.current_resource = element.id
                # Network message would be sent from controller level
                if self.resource_collected >= self.max_capacity:
                    self.returning_to_town_center = True
                tile.delete_ressource_network(self.x, self.y)
                #tile.resource = None
            else:
                pass
            # Print_Display(f"{self.unit_type} ne peut pas récolter {element.id}, réseau occupé par un autre joueur.")

            element.network_owner = (
                element.owner
            )  # Remet le network_owner à l'owner réel

    def gather_food_from_farm(self):
        """Récolte la nourriture de la ferme en continu jusqu'à épuisement."""

        if not self.working_farm:
            return

        farm = self.working_farm
        if self.working_farm.is_empty():
            # Print_Display(f"Ferme à ({self.working_farm.x}, {self.working_farm.y}) est épuisée.")
            self.working_farm = None
            return

        # Essaye de prendre le contrôle du réseau
        if not hasattr(farm, "network_owner"):
            farm.network_owner = farm  # On met le propriétaire initial
        farm.network_owner = self.ai

        # Print_Display(f"Vérification de la ferme : {self.working_farm}")
        # Print_Display(f"Methodes disponibles : {dir(self.working_farm)}")
        # Print_Display(f"Type of object, farm: {type(self.working_farm)}")
        # time.sleep(10)

        # Occupation pendant la récolte
        if not self.working_farm.is_occupied():
            self.working_farm.occupy()
        # Print_Display(f"{self.unit_type} commence à récolter dans la ferme à ({self.working_farm.x}, {self.working_farm.y}).")

        current_time = time.time()
        if not hasattr(self, "action_end_time"):
            self.action_end_time = current_time + 5  # Timer initial pour la récolte

        if current_time >= self.action_end_time:
            amount = min(20, self.max_capacity - self.resource_collected)
            food_gathered = self.working_farm.gather_food(amount)
            self.resource_collected += food_gathered
            self.current_resource = "Food"
            # Network message would be sent from controller level

            if self.resource_collected >= self.max_capacity:
                # Print_Display(f"{self.unit_type} a atteint sa capacité maximale en nourriture.")
                self.returning_to_town_center = True
                self.working_farm.free()
                self.working_farm = None
            else:
                self.action_end_time = current_time + 5  # Prochaine récolte

            farm.network_owner = farm  # Libère la ferme pour d'autres unités
            # Occupation pendant la récolte
            """             #if not self.working_farm.is_occupied():
            #    self.working_farm.occupy()
                #Print_Display(f"{self.unit_type} commence à récolter dans la ferme à ({self.working_farm.x}, {self.working_farm.y}).")

            current_time = time.time()
            if not hasattr(self, 'action_end_time'):
                self.action_end_time = current_time + 5  # Timer initial pour la récolte

            if current_time >= self.action_end_time:
                amount = min(20, self.max_capacity - self.resource_collected)
                food_gathered = self.working_farm.gather_food(amount)
                self.resource_collected += food_gathered
                self.current_resource = 'Food'
                #Print_Display(f"{self.unit_type} récolte {food_gathered} unités de nourriture.")

                if self.resource_collected >= self.max_capacity:
                    #Print_Display(f"{self.unit_type} a atteint sa capacité maximale en nourriture.")
                    self.returning_to_town_center = True
                    self.working_farm.free()
                    self.working_farm = None
                else:
                    self.action_end_time = current_time + 5  # Prochaine récolte """

    def deposit_resource(self, building):
        if (
            building
            and building.building_type == "Town Center"
            and self.current_resource
        ):
            # Appelle directement AI pour gérer les ressources
            # Network message would be sent from controller level
            # Print_Display(f"{self.unit_type} dépose {self.resource_collected} unités de {self.current_resource} au Town Center.")
            self.ai.update_resources(self.current_resource, self.resource_collected)
            self.resource_collected = 0
            self.returning_to_town_center = False
            self.current_resource = None

    def find_nearest_farm(self, game_map):
        """Recherche la ferme la plus proche qui contient de la nourriture et qui n'est pas occupée."""
        path = self.find_path(game_map, (self.x, self.y), "Farm")
        if path:
            # Récupération de la tuile et du bâtiment sur cette tuile
            farm_tile = game_map.grid[path[-1][1]][path[-1][0]]
            if (
                farm_tile.building
                and not farm_tile.building.is_occupied()
                and not farm_tile.building.is_empty()
            ):
                ##Print_Display(f"Chemin trouvé vers la ferme à ({path[-1][0]}, {path[-1][1]})")
                return path
            else:
                ##Print_Display(f"La ferme à ({path[-1][0]}, {path[-1][1]}) est occupée ou épuisée.")
                return None
        else:
            ##Print_Display(f"Aucun chemin vers une ferme trouvé pour {self.unit_type} à ({self.x}, {self.y})")
            return None

    def find_nearest_gold(self, game_map):
        """Utilise une recherche de chemin pour trouver l'or le plus proche"""
        path = self.find_path(game_map, (self.x, self.y), "Gold")
        # if path:
        ##Print_Display(f"Chemin trouvé vers l'or : ") #{path}
        # else:
        ##Print_Display(f"Aucun chemin vers l'or trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_nearest_wood(self, game_map):
        """Utilise une recherche de chemin pour trouver le bois le plus proche"""
        path = self.find_path(game_map, (self.x, self.y), "Wood")
        # if path:
        ##Print_Display(f"Chemin trouvé vers le bois : ") #{path}
        # else:
        ##Print_Display(f"Aucun chemin vers le bois trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_nearest_town_center(self, game_map, buildings):
        """Recherche du chemin vers le Town Center le plus proche"""
        town_center = buildings[0]
        # Si le villageois est déjà sur la même tuile que le Town Center
        if (self.x, self.y) == (town_center.x, town_center.y):
            ##Print_Display(f"{self.unit_type} est déjà sur le Town Center.")
            return None  # Pas besoin de trouver un chemin

        path = self.find_path(game_map, (self.x, self.y), "Town Center", town_center)
        # if path:
        ##Print_Display(f"Chemin trouvé vers le Town Center : {path}")
        # else:
        ##Print_Display(f"Aucun chemin vers le Town Center trouvé pour {self.unit_type} à ({self.x}, {self.y})")
        return path

    def find_path(self, game_map, start, target_type, target_building=None):
        """Recherche un chemin vers une destination donnée avec déplacements diagonaux"""

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Distance de Manhattan

        open_list = []
        heapq.heappush(open_list, (0, start))
        came_from = {}
        cost_so_far = {start: 0}

        # Ajout des déplacements diagonaux
        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (1, 1),
            (-1, 1),
            (1, -1),
        ]

        while open_list:
            _, current = heapq.heappop(open_list)

            # Vérification pour le bois
            if (
                target_type == "Wood"
                and game_map.grid[current[1]][current[0]].resource == "Wood"
            ):
                ##Print_Display(f"Bois trouvé à {current}")  # Log la position du bois trouvé
                return self.reconstruct_path(
                    came_from, current
                )  # Retourner le chemin trouvé

            # Vérification pour l'or
            if (
                target_type == "Gold"
                and game_map.grid[current[1]][current[0]].resource == "Gold"
            ):
                ##Print_Display(f"Or trouvé à {current}")  # Log la position de l'or trouvé
                return self.reconstruct_path(
                    came_from, current
                )  # Retourner le chemin trouvé

            # Vérification pour le Town Center
            if (
                target_type == "Town Center"
                and target_building
                and (current[0], current[1]) == (target_building.x, target_building.y)
            ):
                ##Print_Display(f"Town Center trouvé à {current}")  # Log la position du Town Center trouvé
                return self.reconstruct_path(came_from, current)

            # Vérification pour une ferme
            if (
                target_type == "Farm"
                and isinstance(game_map.grid[current[1]][current[0]].building, Building)
                and game_map.grid[current[1]][current[0]].building.building_type
                == "Farm"
            ):
                ##Print_Display(f"Ferme trouvée à {current}")  # Log la position de la ferme trouvée
                return self.reconstruct_path(came_from, current)

            # Exploration des voisins
            for dx, dy in directions:
                next_node = (current[0] + dx, current[1] + dy)
                if (
                    0 <= next_node[0] < game_map.width
                    and 0 <= next_node[1] < game_map.height
                ):
                    new_cost = cost_so_far[current] + 1
                    if (
                        next_node not in cost_so_far
                        or new_cost < cost_so_far[next_node]
                    ):
                        cost_so_far[next_node] = new_cost
                        priority = new_cost + heuristic(next_node, (self.x, self.y))
                        heapq.heappush(open_list, (priority, next_node))
                        came_from[next_node] = current

        ##Print_Display(f"Aucun chemin trouvé pour {target_type}")
        return None

    def reconstruct_path(self, came_from, current):
        """Recrée le chemin à partir de la position courante"""
        path = []
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.reverse()  # On inverse le chemin pour partir de la position de départ
        return path

    def to_network_message(self):
        return f"id:{self.id},type:{self.unit_type},x:{self.x},y:{self.y},owner:{self.owner}"

