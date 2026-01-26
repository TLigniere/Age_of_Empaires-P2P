import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model import Building, Unit, Tile, Map



class AIStrategy:
    def __init__(self):
        self.network = None
    
    def set_network(self, network):
        """Définit la référence au client réseau pour communiquer"""
        self.network = network
    
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
        self.resources = {
            'Wood': 200,
            'Gold': 100,
            'Food': 50
        }
        self.population = len(units)
        self.population_max = 5
        self.victoire = False
        self.buildings = buildings
        self.units = units
        self.town_center = buildings[0]

    # Autres méthodes de la classe AI

    def build(self, game_map):
        """Méthode pour construire un bâtiment si les ressources sont disponibles."""
        # Exemple : Construire une ferme si assez de bois et d'or
        cost = {'Wood': 50, 'Gold': 30}
        if self.can_afford(cost):
            # Trouver une position valide pour construire le bâtiment
            x, y = self.find_valid_build_location(game_map)
            if x is not None and y is not None:
                # Construire une ferme
                new_building = Building('Farm', x, y)
                game_map.place_building(new_building, x, y)
                self.buildings.append(new_building)
                self.pay_resources(cost)
               #print(f"Bâtiment {new_building.building_type} construit à ({x}, {y})")
        #else:
           #print("Pas assez de ressources pour construire.")


    def find_valid_build_location(self, game_map):
        """Trouver une position libre à proximité immédiate du Town Center pour construire une ferme."""
        # Centre du Town Center
        center_x, center_y = self.town_center.x, self.town_center.y

        # Limite la recherche à un rayon de 3 cases autour du Town Center
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                x, y = center_x + dx, center_y + dy
                # Vérifie si la case est libre et dans les limites de la carte
                if game_map.is_empty(x, y):
                    return x, y

        # Aucun emplacement disponible trouvé dans la zone de recherche
       #print("Aucun emplacement libre trouvé dans la zone de 3 cases autour du Town Center pour la ferme.")
        return None, None



    def update_resources(self, resource_type, amount):
        if resource_type in self.resources:
            self.resources[resource_type] += amount
           #print(f"[AI] Ressources {resource_type} mises à jour : {self.resources[resource_type]} unités.")

    def can_afford(self, cost):
        """Vérifie si l'IA peut se permettre de payer un coût spécifique."""
        return all(self.resources[res] >= cost.get(res, 0) for res in cost)

    def pay_resources(self, cost):
        """Déduit les ressources après un achat."""
        if self.can_afford(cost):
            for res in cost:
                self.resources[res] -= cost[res]
               #print(f"Paiement de {cost[res]} unités de {res}. Restant : {self.resources[res]}")

    def update_population(self, change):
        self.population += change
       #print(f"Population mise à jour : {self.population}/{self.population_max}")


    def set_victoire(self, status):
        self.victoire = status
       #print(f"Victoire: {'Oui' if self.victoire else 'Non'}")
