# ai_strategies/economic_ai.py
from ai_strategies.base_strategies import BaseAI

class EconomicAI(BaseAI):
    
    def update_population(self):
        # Logique pour maximiser la population tout en conservant les ressources
        print("Economic AI: Maintenir une croissance modérée de la population.")

    def build(self):
        # Construire des bâtiments économiques en priorité
        print("Economic AI: Construire des centres de stockage et des fermes.")

    def harvest(self):
        # Maximiser la récolte de ressources pour la construction et le développement
        print("Economic AI: Récolte prioritaire pour accumuler des ressources.")

    def attack(self):
        # Stratégie défensive, ne pas attaquer sauf si attaqué
        print("Economic AI: Ne pas attaquer. Se défendre uniquement.")
