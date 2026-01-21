# ai_strategies/aggressive_ai.py
from ai_strategies.base_strategies import BaseAI

class AggressiveAI(BaseAI):
    
    def update_population(self):
        # Logique pour augmenter la population pour l'attaque
        print("Aggressive AI: Augmenter la population pour attaquer.")

    def build(self):
        # Construire des bâtiments nécessaires à une stratégie offensive
        print("Aggressive AI: Construire des casernes et des tours.")

    def harvest(self):
        # La collecte est orientée vers la maximisation de ressources à court terme pour les unités militaires
        print("Aggressive AI: Récolte prioritaire pour la guerre.")

    def attack(self):
        # Déclencher une attaque contre l'adversaire
        print("Aggressive AI: Attaque l'ennemi.")
