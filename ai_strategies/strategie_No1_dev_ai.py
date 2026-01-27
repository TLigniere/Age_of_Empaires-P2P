import time
from ai_strategies.base_strategies import AIStrategy
from view import Print_Display

class StrategieNo1(AIStrategy):
    def execute(self, units, buildings, game_map, ai):
        for unit in units:
            # Gestion du dépôt des ressources
            if unit.returning_to_town_center:
                path = unit.find_nearest_town_center(game_map, buildings)
                if path:
                    next_step = path.pop(0)
                    unit.move(*next_step)
                    if (unit.x, unit.y) == (buildings[0].x, buildings[0].y):
                        unit.deposit_resource(buildings[0])
                        unit.returning_to_town_center = False  # Réinitialisation
                       #print(f"{unit.unit_type} retourne à la sélection de ressources après dépôt.")

            else:
                # Recherche et choix de la ressource la plus proche disponible
                food_path = unit.find_nearest_farm(game_map)
                wood_path = unit.find_nearest_wood(game_map)
                gold_path = unit.find_nearest_gold(game_map)

                paths = {
                    'Food': (food_path, len(food_path) if food_path else float('inf')),
                    'Wood': (wood_path, len(wood_path) if wood_path else float('inf')),
                    'Gold': (gold_path, len(gold_path) if gold_path else float('inf'))
                }

                # Sélection de la ressource la plus proche
                nearest_resource = min(paths.items(), key=lambda x: x[1][1])
               #print(f"{unit.unit_type} sélectionne la ressource la plus proche : {nearest_resource[0]}")

                if nearest_resource[1][0]:  # Si un chemin est trouvé
                    next_step = nearest_resource[1][0].pop(0)
                    unit.move(*next_step)

                    # Action de récolte en fonction de la ressource choisie
                    if nearest_resource[0] == 'Food':
                        farm_tile = game_map.grid[unit.y][unit.x]
                        if farm_tile.building and farm_tile.building.building_type == 'Farm':
                            unit.working_farm = farm_tile.building
                            unit.gather_food_from_farm()
                    elif nearest_resource[0] == 'Wood':
                        unit.gather_resource(game_map)
                    elif nearest_resource[0] == 'Gold':
                        unit.gather_resource(game_map)

        # Mise à jour pour l'IA
        ai.update_population(0)
        ai.build(game_map)

