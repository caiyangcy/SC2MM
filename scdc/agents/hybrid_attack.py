from scdc.env.micro_env.mm_env import MMEnv, Direction
import time
import numpy as np
import argparse
import math

class HybridAttack():
    def __init__(self, n_agents, env, alpha):
        self.n_agents = n_agents
        self.env = env
        self.alpha = alpha 
        
        
    def _calculate_score(self, alpha, health, distance):
        return alpha*health+(1-alpha)*distance 
    
    
    def step(self):
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
                
        