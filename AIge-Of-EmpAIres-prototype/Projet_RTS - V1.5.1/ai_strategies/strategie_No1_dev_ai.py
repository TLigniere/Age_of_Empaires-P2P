import time
from ai_strategies.base_strategies import AIStrategy
from model import Building

class StrategieNo1(AIStrategy):
    def execute(self, units, buildings, game_map, ai):
        current_time = time.time()

        # 1. Mise à jour des unités
        for unit in units:
            # Si l'unité est en train de retourner au centre-ville
            if unit.returning_to_town_center:
                path = unit.find_nearest_town_center(game_map, buildings)
                if path:
                    next_step = path.pop(0)
                    unit.move(*next_step)
                    # Si l'unité est arrivée au centre-ville
                    if (unit.x, unit.y) == (buildings[0].x, buildings[0].y):
                        unit.deposit_resource(buildings[0])
                        unit.returning_to_town_center = False
                        unit.resource_collected = 0
                        if unit.working_farm:
                            unit.working_farm.free()  # Libérer la ferme une fois les ressources déposées
                            unit.working_farm = None
                        unit.current_action = None  # L'unité est maintenant disponible
                        self.assign_next_task(unit, game_map, buildings)

            # Si l'unité est disponible, assigne une nouvelle tâche
            elif unit.current_action is None:
                self.assign_next_task(unit, game_map, buildings)

            # Gérer la récolte en cours
            elif unit.current_action in ['gathering_food', 'gathering_wood', 'gathering_gold']:
                if current_time - unit.gathering_start_time >= unit.gathering_duration:
                    unit.gather_resource()  # Utilise gather_resource pour récolter les ressources
                    unit.current_action = 'returning_to_town_center'
                    unit.returning_to_town_center = True
                    print(f"{unit.unit_type} retourne au Town Center avec {unit.resource_collected} unités de {unit.current_resource}")

            # Gérer le déplacement
            elif unit.current_action in ['moving_to_wood', 'moving_to_farm', 'moving_to_gold']:
                if unit.target_path:
                    next_step = unit.target_path.pop(0)
                    unit.move(*next_step)
                else:
                    # Si arrivé à destination
                    if unit.current_action == 'moving_to_wood':
                        unit.current_action = 'gathering_wood'
                        unit.gathering_start_time = current_time
                        unit.gathering_duration = 5  # Temps de récolte de bois (5 secondes)
                        print(f"{unit.unit_type} commence à récolter du bois à ({unit.x}, {unit.y})")
                    elif unit.current_action == 'moving_to_farm':
                        unit.current_action = 'gathering_food'
                        unit.gathering_start_time = current_time
                        unit.gathering_duration = 10  # Temps de récolte de nourriture (10 secondes)
                        print(f"{unit.unit_type} commence à récolter la nourriture à la ferme à ({unit.x}, {unit.y})")
                    elif unit.current_action == 'moving_to_gold':
                        unit.current_action = 'gathering_gold'
                        unit.gathering_start_time = current_time
                        unit.gathering_duration = 8  # Temps de récolte d'or (8 secondes)
                        print(f"{unit.unit_type} commence à récolter de l'or à ({unit.x}, {unit.y})")

        # 2. Mise à jour de l'I.A.
        ai.update_population()
        ai.build(game_map)

    def assign_next_task(self, unit, game_map, buildings):
        """Assigne une nouvelle tâche à une unité, en priorisant les fermes disponibles."""
        # Prioriser la récolte de nourriture si une ferme est disponible
        available_farm = self.find_available_farm(buildings)

        if available_farm:
            farm_path = unit.find_path_to_target(game_map, available_farm.x, available_farm.y)
            if farm_path:
                next_step = farm_path.pop(0)
                unit.move(*next_step)
                unit.current_action = 'moving_to_farm'
                unit.target_path = farm_path
                unit.working_farm = available_farm
                available_farm.occupy()
                print(f"{unit.unit_type} assigné à la récolte de la ferme à ({available_farm.x}, {available_farm.y})")
            else:
                print(f"Aucun chemin vers la ferme à ({available_farm.x}, {available_farm.y}) trouvé.")

        else:
            # Sinon, chercher d'autres ressources (bois ou or)
            wood_path = unit.find_nearest_wood(game_map)
            gold_path = unit.find_nearest_gold(game_map)
            if wood_path and (not gold_path or len(wood_path) < len(gold_path)):
                next_step = wood_path.pop(0)
                unit.move(*next_step)
                unit.current_action = 'moving_to_wood'
                unit.target_path = wood_path
                print(f"{unit.unit_type} assigné à la récolte de bois à ({next_step[0]}, {next_step[1]})")
            elif gold_path:
                next_step = gold_path.pop(0)
                unit.move(*next_step)
                unit.current_action = 'moving_to_gold'
                unit.target_path = gold_path
                print(f"{unit.unit_type} assigné à la récolte d'or à ({next_step[0]}, {next_step[1]})")

    def find_available_farm(self, buildings):
        """Cherche une ferme disponible."""
        for building in buildings:
            if building.building_type == 'Farm' and not building.is_occupied():
                return building
        return None
