from scmm.agents.scripted.alternating_fire import AlternatingFire
from scmm.agents.scripted.hybrid_attack import HybridAttackHeal
from scmm.agents.scripted.focus_fire import FocusFire
from scmm.agents.scripted.kiting import Kiting
from scmm.agents.scripted.positioning import Positioning
from scmm.agents.scripted.wall_off import WallOff
from scmm.agents.scripted.dying_retreat import DyingRetreat
from scmm.agents.scripted.block_enemy import BlockEnemy

from scmm.env.micro_env.mm_env import MMEnv
from scmm.utils.game_show import game_show, game_show_adv
import argparse
import numpy as np
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Run an agent with actions randomly sampled.')
parser.add_argument('--map_name', default='6h_vs_5z', type=str, help='The name of the map. The full list can be found by running bin/map_list.')
parser.add_argument('--step_mul', default=2, type=int, help='How many game steps per agent step (default is 8). None indicates to use the default map step_mul..')
parser.add_argument('--difficulty', default='A', help='The difficulty of built-in computer AI bot (default is "7").')
parser.add_argument('--reward_sparse', default=True, help='Receive 1/-1 reward for winning/loosing an episode (default is False). The rest of reward parameters are ignored if True.')
parser.add_argument('--debug', default=True, help='Log messages about observations, state, actions and rewards for debugging purposes (default is False).')
parser.add_argument('--n_episodes', default=1, type=int, help='Number of episodes the game will run for.')
parser.add_argument('--agent', default="FocusFire", type=str, help='Number of episodes the game will run for.')
parser.add_argument('--alpha', default=0, type=float, help='Parameter used for calculating score in HybridAttack.')
parser.add_argument('--consec_attack', default=10, type=int, help='Parameter used for consecutive attack counts in Kiting.')
parser.add_argument('--overkill', default=True, type=bool, help='Parameter used for overkill in FocusFire.')
parser.add_argument('--plot_level', default=0,  type=int, help='Whether using advanced plot or not')


args = parser.parse_args()
    

if __name__ == "__main__":
    
    map_name = args.map_name
    step_mul = args.step_mul
    difficulty = args.difficulty
    reward_sparse = args.reward_sparse
    debug = args.debug 
    n_episodes = args.n_episodes
    alpha = args.alpha
    plot_level = args.plot_level

    env = MMEnv(map_name=map_name, step_mul=step_mul, difficulty=difficulty, reward_sparse=reward_sparse, debug=debug)
    env_info = env.get_env_info()

    n_actions = env_info["n_actions"]
    n_agents = env_info["n_agents"]
    
    if args.agent == 'HybridAttackHeal':
        agent = globals()[args.agent](n_agents, alpha=args.alpha)
    elif args.agent == 'Kiting':
        agent = globals()[args.agent](n_agents, consuctive_attack_count=args.consec_attack)
    elif args.agent == 'FocusFire':
        agent = globals()[args.agent](n_agents, no_over_kill=not args.overkill)
    else:
        agent = globals()[args.agent](n_agents)
    
    agent.fit(env)
    
    for e in range(n_episodes):
        agent.env.reset()
        episode_reward = 0
        terminated = False
        
        game_map = np.zeros((env.map_x, env.map_y))

        while not terminated:
            
            if not plot_level:
                reward, terminated, _  = agent.step(plot_level)
            else:
                actions, reward, terminated, info  = agent.step(plot_level)
                   
            episode_reward += reward 
                
            map_size = (agent.env.map_x, agent.env.map_y)
            
            if plot_level == 2:
                game_show_adv(['b.', 'r.'], 20.0, map_size, agent.env.enemies, agent.env.agents, actions, agent.env)
            elif plot_level == 1:
                ally_pos, enemy_pos = agent.env.get_ally_positions(plot_level), agent.env.get_enemy_positions(plot_level)
                game_show(['b.', 'r.'], 20.0, map_size, enemy_pos, ally_pos)
                            
        print("Total reward in episode {} = {}".format(e, episode_reward))
        
        plt.close()
        
    env.close()