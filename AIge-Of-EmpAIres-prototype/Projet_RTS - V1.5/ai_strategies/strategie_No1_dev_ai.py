import time
from ai_strategies.base_strategie import AIStrategy

class StrategieNo1(AIStrategy):
    def execute(self, units, buildings, game_map, ai):
        current_time = time.time()
        
        for unit in units:
            if unit.returning_to_town_center:
                path = unit.find_nearest_town_center(game_map, buildings)
                if path:
                    next_step = path.pop(0)
                    unit.move(*next_step)
                    if (unit.x, unit.y) == (buildings[0].x, buildings[0].y):
                        unit.deposit_resource(buildings[0])
                        unit.returning_to_town_center = False
                        unit.resource_collected = 0
                        wood_path = unit.find_nearest_wood(game_map)
                        gold_path = unit.find_nearest_gold(game_map)
                        if wood_path and (not gold_path or len(wood_path) < len(gold_path)):
                            next_step = wood_path.pop(0)
                            unit.move(*next_step)
                            unit.gather_resource(game_map)
                        elif gold_path:
                            next_step = gold_path.pop(0)
                            unit.move(*next_step)
                            unit.gather_resource(game_map)
            else:
                wood_path = unit.find_nearest_wood(game_map)
                gold_path = unit.find_nearest_gold(game_map)
                if wood_path and (not gold_path or len(wood_path) < len(gold_path)):
                    next_step = wood_path.pop(0)
                    unit.move(*next_step)
                    unit.gather_resource(game_map)
                elif gold_path:
                    next_step = gold_path.pop(0)
                    unit.move(*next_step)
                    unit.gather_resource(game_map)
        
        ai.update_population()
        ai.build(game_map)
