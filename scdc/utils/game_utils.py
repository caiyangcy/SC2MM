'''
Commonly used gaming utils
'''

import numpy as np
import math

def get_opposite_direction(curr_pos, enemy_pos):
    # directions in action index
    # N S E W: 2, 3, 4, 5
    delta_x, delta_y = enemy_pos.x-curr_pos.x, enemy_pos.y-curr_pos.y
    if np.abs(delta_x) >= np.abs(delta_y):
        if delta_x > 0:
            return 5
        else:
            return 4
    else:
        if delta_y > 0:
            return 3
        else:
            return 2
    
    
def fine_closest_position(pos, enemies):
    '''
    Function used to find closest enemy for given position
    enemy id and minimum distance is returned if enemy found is alive
    otherwise return None
    '''
    if type(pos) is tuple or type(pos) is list:
        x, y = pos
    else:
        x, y = pos.x, pos.y
    target_items = enemies.items()
    closest_id, closest_unit = None, None
    min_dist = None
              
    for t_id, t_unit in target_items: # t_id starts from 0
        if t_unit.health > 0:
            dist = math.hypot(t_unit.pos.x - x, t_unit.pos.y - y) 
            if min_dist is None or dist < min_dist:
                min_dist = dist 
                closest_id = t_id
                closest_unit = t_unit 
                    
    return closest_id, closest_unit
    