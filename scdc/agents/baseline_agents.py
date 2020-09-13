from scdc.agents.base_agent import BaseAgent
# import base_agent
from scdc.env.micro_env.mm_env import MMEnv, Direction
import time
import numpy as np
import argparse
import math

class FocusFire():
    def __init__(self, n_agents, env, no_over_kill=False):
        self.n_agents = n_agents 
        self.env = env
        self.no_over_kill = no_over_kill
        
    def step(self, obs, state):                    
       
        if self.no_over_kill:
            actions = self.find_focus_targets()
        else:
            all_closest_id = self.find_closest()
            actions = [6+all_closest_id]*self.n_agents
            
        reward, terminated, _ = self.env.step(actions)
        return reward, terminated 
        
    
    def find_closest(self):
        center_x, center_y = self.env.get_ally_center()
        target_items = self.env.enemies.items()
        all_closest_id = None
        min_dist = math.hypot(self.env.max_distance_x, self.env.max_distance_y)
                  
        for t_id, t_unit in target_items: # t_id starts from 0
            if t_unit.health > 0:
                dist = self.env.distance(center_x, center_y, t_unit.pos.x, t_unit.pos.y)
                if dist < min_dist:
                    min_dist = dist 
                    all_closest_id = t_id
                        
        return all_closest_id
    
    def find_focus_targets(self):
        # Find top k closest targets and each ally unit doesn't do damage more than enough to kill them
        # Must use on homogeneous maps at the moment
        center_x, center_y = self.env.get_ally_center()
        
        target_items = self.env.enemies.items()
        
        # sort distances
        dist_arr = [] 
        hp_arr = []
        e_id_arr = []
        
        for t_id, t_unit in target_items: # t_id starts from 0
            if t_unit.health > 0:
                dist = self.env.distance(center_x, center_y, t_unit.pos.x, t_unit.pos.y)
                dist_arr.append(dist)
                hp_arr.append(t_unit.health)        
                e_id_arr.append(t_id)
        
        dist_arr = np.array(dist_arr)
        hp_arr = np.array(hp_arr)
        e_id_arr = np.array(e_id_arr)
        
        ind = np.argsort(dist_arr)
        
        dist_arr = dist_arr[ind]
        hp_arr = hp_arr[ind]
        e_id_arr = e_id_arr[ind]
        
        attack_id = []
        enermy_counter, count = 0, 0
        single_unit_damage = self.env.unit_damage(self.env.get_unit_by_id(0))
        
        for agent_id in range(self.n_agents):
            unit = self.env.get_unit_by_id(agent_id)    
            if unit.health > 0:
                count += 1
                attack_id.append(e_id_arr[enermy_counter]+6)
                
                if hp_arr[enermy_counter] <= single_unit_damage*count:
                    count = 0
                    
                    if enermy_counter+1 >= len(e_id_arr):
                        remaining = self.n_agents - agent_id
                        for _ in range(remaining):
                            attack_id.append(np.random.randint(0, len(e_id_arr))+6)
                            return attack_id 
                    else:
                        enermy_counter += 1
            else:
                attack_id.append(1)
        
        return attack_id 
    
    
class HybridAttack():
    def __init__(self, n_agents, env, alpha):
        self.n_agents = n_agents
        self.env = env
        self.alpha = alpha 
        
        
    def _calculate_score(self, alpha, health, distance):
        return alpha*health+(1-alpha)*distance 
    
    
    def step(self, obs, state):
        actions = []        
        target_items = self.env.enemies.items()

        for agent_id in range(self.n_agents):
            unit = self.env.get_unit_by_id(agent_id)
            min_score_e_id = self.find_lowest_score(unit, target_items)
            action = 6+min_score_e_id
                
            actions.append(action)

        reward, terminated, _ = self.env.step(actions)
        
        return reward, terminated 
        
        
    def find_lowest_score(self, unit, target_items):
        min_score = None
        min_score_e_id = None
        for t_id, t_unit in target_items:
            if t_unit.health > 0:
                dist = self.env.distance(unit.pos.x, unit.pos.y, t_unit.pos.x, t_unit.pos.y)
                score = self._calculate_score(self.alpha, t_unit.health, dist)
                if min_score is None or score < min_score :
                    min_score = score 
                    min_score_e_id = t_id
                    
        return min_score_e_id 
                
        
        
class AlternatingFire():
    def __init__(self, n_agents, env):
        assert n_agents > 1, "AlternatingFire doesn't support agents less than 2."
        self.n_agents = n_agents 
        self.env = env
        
    def step(self, obs, state):
        pass
    
    

class Kiting():
    '''
    Kiting is only tested on 3s_vs_3z, 3s_vs_4z, 3s_vs_5z
    '''
    def __init__(self, n_agents, env, consuctive_attack_count=7):
        assert env.map_name in {'3s_vs_3z', '3s_vs_4z', '3s_vs_5z'}, "Kiting trick only works for 3s_vs_3z, 3s_vs_4z, 3s_vs_5z maps."
        self.n_agents = n_agents 
        self.env = env
        self.distination_point = 0
        self.move_direction = 2
        self.direction_map = {2:4, 3:5, 4:3, 5:2}
        self.consuctive_attack_count = consuctive_attack_count
        self.ready_for_attack = False
    
    def step(self, obs, state):
        closest_e_id, close_e_unit, closest_dist, move_direction = self.find_closest()
        actions = []
        for agent_id in range(self.n_agents):
            unit = self.env.get_unit_by_id(agent_id)
            
            if self.ready_for_attack:
                actions.append(6+closest_e_id)
                self.consuctive_attack_count -= 1
                if self.consuctive_attack_count == 0:
                    self.ready_for_attack = False

                
            elif self.env.unit_shoot_range(unit) >= closest_dist and self.env.unit_shoot_range(close_e_unit) < 1.2*closest_dist:
            # if self.env.unit_shoot_range(unit) - self.env.unit_shoot_range(close_e_unit) > closest_dist:
                actions.append(6+closest_e_id)
                self.ready_for_attack = True
                self.consuctive_attack_count = 7
                
            elif self.env.unit_shoot_range(close_e_unit) >= 1.2*closest_dist:
                actions.append(move_direction)
                
            else: # find enermy and make them give a chase
                # passive
                actions.append(1)
                
        reward, terminated, _ = self.env.step(actions)
        return reward, terminated 

    def find_closest(self):
        center_x, center_y = self.env.get_ally_center()
        
        target_items = self.env.enemies.items()
        all_closest_id, all_closest_unit = None, None
        min_dist = math.hypot(self.env.max_distance_x, self.env.max_distance_y)
        move_direction = None
        
        for t_id, t_unit in target_items: # t_id starts from 0
            if t_unit.health > 0:
                
                e_pos_x, e_pos_y = t_unit.pos.x, t_unit.pos.y
                
                dist = self.env.distance(center_x, center_y, e_pos_x, e_pos_y)
                if dist < min_dist:
                    min_dist = dist 
                    all_closest_id = t_id
                    all_closest_unit = t_unit
        
                    
        e_pos_x, e_pos_y = self.env.get_enermy_center()      
        map_x, map_y = self.env.map_x, self.env.map_y
        # botton left is (0, 0)
        # N S E W: 2, 3, 4, 5
        
        # The first four are directly hard-coded
        discount_factor = 0.2
        
        offset_x, offset_y = map_x*discount_factor, map_y*discount_factor
        distination_list = [(offset_x, map_y-offset_y), (map_x-offset_x, map_y-offset_y), (map_x-offset_x,offset_y),  (offset_x, offset_y)]
        
        move_direction = self.move_direction
        distination_point = distination_list[self.distination_point]
        dist = self.env.distance(center_x, center_y, distination_point[0], distination_point[1])
        # print('dist: ', dist)
        if dist < 5: # check if close to destination
            self.distination_point = (self.distination_point+1)%4
            move_direction = self.direction_map[move_direction]
            self.move_direction = move_direction 
            
        return all_closest_id, all_closest_unit, min_dist, move_direction
    

class Positioning():
    '''
    hard-coded
    '''
    def __init__(self, n_agents, env):
        assert env.map_name in {'bane_vs_bane', 'so_many_baneling', '2c_vs_64zg'}, "Not supported map"
        self.n_agents = n_agents 
        self.env = env
        self.map_name = env.map_name
        self.in_position = False
        
    def step(self, obs, state):
        if self.in_position:
            actions = self.find_close_k()
        else:
            self.in_position, actions = self.partition()                
         
        reward, terminated, _ = self.env.step(actions)
        return reward, terminated    
    
    def partition(self):
        if self.map_name == 'bane_vs_bane':
            # 5 partitions
            zerg_partition_counter = 1
            banelings, zergs = [], []
            actions = []
            patition_done = True
            
            for agent_id in range(self.n_agents):
                unit = self.env.get_unit_by_id(agent_id)
                if unit.health > 0:
                    if unit.unit_type == self.env.baneling_id:
                        actions.append(1)
                    else:
                        # 20 zergs in total
                        pos = unit.pos 
                        if zerg_partition_counter <= 5: 
                            move_direction = self.get_move_direction(pos, (7, 11), zerg_partition_counter)
                        elif zerg_partition_counter <= 10: 
                            move_direction = self.get_move_direction(pos, (10, 8), zerg_partition_counter)
                        elif zerg_partition_counter <= 15: 
                            move_direction = self.get_move_direction(pos, (21, 11), zerg_partition_counter)
                        elif zerg_partition_counter <= 20: 
                            move_direction = self.get_move_direction(pos, (24, 8), zerg_partition_counter)
                            
                        zerg_partition_counter += 1
                        
                        actions.append(move_direction)
                        if actions[-1] != 1:
                            patition_done = False
                else:
                    actions.append(1)
                    
            return patition_done, actions
        
        elif self.map_name == 'so_many_baneling':
            pass
        else:
            pass
    
    def get_group_center(self, group):
        center_x, center_y = 0, 0
        for unit in group:
            center_x += unit.pos.x 
            center_y += unit.pos.y
        return (center_x/len(group), center_y/len(group))
        
        
    def get_move_direction(self, center, distination, zerg_partition_counter):
        center_x, center_y = center.x, center.y
        if self.env.distance(center_x, center_y, distination[0], distination[1]) < 3:
            return 1
        else:
            
            if zerg_partition_counter <= 5:
                return 5
            elif zerg_partition_counter <= 10:
                if np.abs(distination[0]-center_x) > np.abs(distination[1]-center_y):
                    action = 5
                else:
                    action = 3
                    
            elif zerg_partition_counter <= 15:
                return 4
                    
                    
            elif zerg_partition_counter <= 20:
                if np.abs(distination[0]-center_x) > np.abs(distination[1]-center_y):
                    action = 4
                else:
                    action = 3

        return action
    
    def find_close_k(self):
        e_id_arr = []
        target_items = self.env.enemies.items()
        for agent_id in range(self.n_agents):
            
            unit = self.env.get_unit_by_id(agent_id)
            min_dist = math.hypot(self.env.max_distance_x, self.env.max_distance_y)
            min_dist_id = -5
            
            for t_id, t_unit in target_items: # t_id starts from 0
                if t_unit.health > 0:
                    dist = self.env.distance(unit.pos.x, unit.pos.y, t_unit.pos.x, t_unit.pos.y)
                    if dist < min_dist:
                        min_dist = dist
                        min_dist_id = t_id 
            
            e_id_arr.append(min_dist_id+6)
        
        return e_id_arr
    
class WallOff():
    '''
    hard-coded
    '''
    def __init__(self, n_agents, env):
        assert env.map_name == 'corridor', "WallOff trick only works for corridor maps."
        self.n_agents = n_agents 
        self.env = env
        self.destination_point = (9, 9) # this one is hard-coded 
        self.arrival = False 
        
    def step(self, obs, state):
        actions = []
        if self.arrival:
            actions = self.find_close_k()
            reward, terminated, _ = self.env.step(actions)
            return reward, terminated      
            
        center_x, center_y = self.env.get_ally_center()
        if self.env.distance(center_x, center_y, self.destination_point[0], self.destination_point[1]) < 2:
            self.arrival = True
            actions = self.find_close_k()
        else:
            if center_x > center_y:
                actions = [5]*self.n_agents
            else:
                actions = [3]*self.n_agents
                
        
        
        reward, terminated, _ = self.env.step(actions)
        return reward, terminated      
    
    
    def find_close_k(self):
        e_id_arr = []
        target_items = self.env.enemies.items()
        for agent_id in range(self.n_agents):
            
            unit = self.env.get_unit_by_id(agent_id)
            min_dist = math.hypot(self.env.max_distance_x, self.env.max_distance_y)
            min_dist_id = -5
            
            for t_id, t_unit in target_items: # t_id starts from 0
                if t_unit.health > 0:
                    dist = self.env.distance(unit.pos.x, unit.pos.y, t_unit.pos.x, t_unit.pos.y)
                    if dist < min_dist:
                        min_dist = dist
                        min_dist_id = t_id 
            
            e_id_arr.append(min_dist_id+6)
        
        return e_id_arr