import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model import Building, Unit, Tile, Map, Joueur



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
    def __init__(self, joueur, buildings, units):
        self.joueur = joueur
        self.buildings = buildings
        self.units = units
        self.population = len(units)
        self.population_max = 4
        self.town_center = buildings[0]
        self.last_build_time = time.time()  # Ajout d'un timer pour contrôler la fréquence des constructions


    def build(self, game_map):
        current_time = time.time()
        # Ne construire qu'après un délai minimum de 10 secondes entre chaque construction
        if current_time - self.last_build_time > 10:
            if self.should_build_house() and self.joueur.resources['Wood'] >= 50:
                self.construct_building('House', game_map)
                self.last_build_time = current_time
            elif self.should_build_farm() and self.joueur.resources['Wood'] >= 60:
                self.construct_building('Farm', game_map)
                self.last_build_time = current_time
            elif self.should_build_barracks() and self.joueur.resources['Wood'] >= 100:
                self.construct_building('Barracks', game_map)
                self.last_build_time = current_time


    def update_population(self):
        """Met à jour la population maximale en fonction des maisons construites."""
        self.population_max = 5  # Réinitialiser pour recalculer
        for building in self.buildings:
            self.population_max += building.population_capacity
