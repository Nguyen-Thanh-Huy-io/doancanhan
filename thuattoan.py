from collections import deque
import time
import heapq
from copy import deepcopy
from queue import PriorityQueue
import random
import math
import sys

moves_delta = [(-1, 0), (1, 0), (0, -1), (0, 1)] 
move_names = {(-1, 0): 'UP', (1, 0): 'DOWN', (0, -1): 'LEFT', (0, 1): 'RIGHT'}

def find_blank(state_list_of_lists):
    if not isinstance(state_list_of_lists, list) or len(state_list_of_lists) != 3:
        return None
    for i in range(3):
        if not isinstance(state_list_of_lists[i], list) or len(state_list_of_lists[i]) != 3:
            return None
        for j in range(3):
            try:
                if not isinstance(state_list_of_lists[i][j], int):
                    return None 
                if state_list_of_lists[i][j] == 0:
                    return i, j
            except IndexError:
                return None
    return None

def is_valid(x, y):
         return 0 <= x < 3 and 0 <= y < 3

def state_to_tuple(state_list_of_lists):
    try:
        if not isinstance(state_list_of_lists, list) or len(state_list_of_lists) != 3:
            return None
        if not all(isinstance(row, list) and len(row) == 3 for row in state_list_of_lists):
            return None
        if not all(isinstance(item, int) for row in state_list_of_lists for item in row):
             return None
        return tuple(tuple(row) for row in state_list_of_lists)
    except (TypeError, IndexError): 
        return None

def tuple_to_list(state_tuple):
    try:
        if not isinstance(state_tuple, tuple) or len(state_tuple) != 3:
            return None
        if not all(isinstance(row, tuple) and len(row) == 3 for row in state_tuple):
            return None
        if not all(isinstance(item, int) for row in state_tuple for item in row):
             return None
        return [list(row) for row in state_tuple]
    except (TypeError, IndexError):
        return None

def get_neighbors(state):
    state_list = tuple_to_list(state) if isinstance(state, tuple) else deepcopy(state)
    if state_list is None: return []

    blank_pos = find_blank(state_list)
    if blank_pos is None: return [] 
    
    x, y = blank_pos 
    neighbors = []     
    for dr, dc in moves_delta: 
        tile_x, tile_y = x + dr, y + dc 

        if is_valid(tile_x, tile_y): 
            new_state = deepcopy(state_list)             
            new_state[x][y], new_state[tile_x][tile_y] = new_state[tile_x][tile_y], new_state[x][y]             
            neighbors.append({'state': new_state, 'move': (tile_x, tile_y)}) 
            
    return neighbors 
def manhattan_distance(state, goal):
    state_list = tuple_to_list(state) if isinstance(state, tuple) else state
    goal_list = tuple_to_list(goal) if isinstance(goal, tuple) else goal
    if state_list is None or goal_list is None: return float('inf')

    distance = 0
    goal_positions = {} 
    try:
        for r_goal in range(3):
            for c_goal in range(3):
                val_goal = goal_list[r_goal][c_goal]
                if not isinstance(val_goal, int): raise TypeError("Goal state contains non-integer")
                goal_positions[val_goal] = (r_goal, c_goal)
        
        for r_state in range(3):
            for c_state in range(3):
                value_state = state_list[r_state][c_state]
                if not isinstance(value_state, int): raise TypeError("Current state contains non-integer")
                if value_state != 0: 
                    if value_state in goal_positions:
                        goal_x, goal_y = goal_positions[value_state]
                        distance += abs(r_state - goal_x) + abs(c_state - goal_y)
                    else:
                        return float('inf') 
    except (IndexError, TypeError, KeyError):
        return float('inf') 
    return distance 

def bfs(initial, goal):
    initial_list = deepcopy(initial) if isinstance(initial, list) else tuple_to_list(initial)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if initial_list is None or goal_list is None: return None
    initial_tuple = state_to_tuple(initial_list)
    goal_tuple = state_to_tuple(goal_list)
    if initial_tuple is None or goal_tuple is None: return None

    queue = deque([(initial_list, [])]); visited = {initial_tuple} 
    while queue:
        current_state_list, path = queue.popleft()
        current_tuple = state_to_tuple(current_state_list)
        if current_tuple is None: continue 
        if current_tuple == goal_tuple: return path

        neighbors_data = get_neighbors(current_state_list)
        for neighbor_info in neighbors_data:
            new_state = neighbor_info['state']
            move_coord = neighbor_info['move'] 
            new_tuple = state_to_tuple(new_state)
            if new_tuple is None: continue
            if new_tuple not in visited:
                visited.add(new_tuple)
                queue.append((new_state, path + [move_coord]))
    return None

def ucs(initial, goal):
    initial_list = deepcopy(initial) if isinstance(initial, list) else tuple_to_list(initial)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if initial_list is None or goal_list is None: return None
    initial_tuple = state_to_tuple(initial_list)
    goal_tuple = state_to_tuple(goal_list)
    if initial_tuple is None or goal_tuple is None: return None

    priority_queue = PriorityQueue()
    priority_queue.put((0, initial_list, [])) 
    visited = {initial_tuple: 0} 

    while not priority_queue.empty():
        cost, current_state_list, path = priority_queue.get()
        current_tuple = state_to_tuple(current_state_list)
        if current_tuple is None: continue
        if current_tuple == goal_tuple: return path
        if cost > visited.get(current_tuple, float('inf')): continue 

        neighbors_data = get_neighbors(current_state_list)
        for neighbor_info in neighbors_data:
            new_state = neighbor_info['state']
            move_coord = neighbor_info['move']
            new_tuple = state_to_tuple(new_state)
            if new_tuple is None: continue
            
            new_cost = cost + 1 
            if new_cost < visited.get(new_tuple, float('inf')):
                visited[new_tuple] = new_cost
                priority_queue.put((new_cost, new_state, path + [move_coord]))
    return None

def dfs(initial, goal):     
    initial_list = deepcopy(initial) if isinstance(initial, list) else tuple_to_list(initial)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)

    if initial_list is None:
        return None
    if goal_list is None:
        return None

    initial_tuple = state_to_tuple(initial_list)
    goal_tuple = state_to_tuple(goal_list)

    if initial_tuple is None:
        return None
    if goal_tuple is None:
        return None     
    stack = [(initial_list, [])] 
    visited_tuples = {initial_tuple}     
    while stack:
        current_state_list, path_to_current = stack.pop()
        
        current_state_tuple = state_to_tuple(current_state_list)
        if current_state_tuple is None:
            continue         
        if current_state_tuple == goal_tuple:
            return path_to_current         
        neighbors_data = get_neighbors(current_state_list)         
        for neighbor_info in reversed(neighbors_data):
            new_neighbor_state_list = neighbor_info['state']
            tile_coord_moved = neighbor_info['move']

            new_neighbor_state_tuple = state_to_tuple(new_neighbor_state_list)
            if new_neighbor_state_tuple is None:
                continue

            if new_neighbor_state_tuple not in visited_tuples:
                visited_tuples.add(new_neighbor_state_tuple)
                new_path = path_to_current + [tile_coord_moved]
                stack.append((new_neighbor_state_list, new_path))
    return None
def depth_limited_search_recursive(current_state_list, goal_list, current_depth_limit, current_path_coords, visited_in_path_tuples):
    current_tuple = state_to_tuple(current_state_list)
    goal_tuple = state_to_tuple(goal_list) 
    if current_tuple is None or goal_tuple is None: return None
    if current_tuple == goal_tuple: return current_path_coords
    if current_depth_limit <= 0: return None 

    visited_in_path_tuples.add(current_tuple)

    neighbors_data = get_neighbors(current_state_list)
    for neighbor_info in neighbors_data:
        new_state = neighbor_info['state']
        move_coord = neighbor_info['move']
        new_tuple = state_to_tuple(new_state) 
        if new_tuple is None: continue
        
        if new_tuple not in visited_in_path_tuples: 
            result_path = depth_limited_search_recursive(
                new_state, goal_list, current_depth_limit - 1, 
                current_path_coords + [move_coord], visited_in_path_tuples
            )
            if result_path is not None: 
                if current_tuple in visited_in_path_tuples: visited_in_path_tuples.remove(current_tuple)
                return result_path
    
    if current_tuple in visited_in_path_tuples:
        visited_in_path_tuples.remove(current_tuple)
    return None


def iddfs(initial, goal, max_depth=30): 
    initial_list = deepcopy(initial) if isinstance(initial, list) else tuple_to_list(initial)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if initial_list is None or goal_list is None: return None

    for depth in range(max_depth + 1):
        visited_in_this_dls_path = set() 
        result = depth_limited_search_recursive(initial_list, goal_list, depth, [], visited_in_this_dls_path)
        if result is not None:
            return result
    return None 
def greedy_search(initial, goal):
    initial_list = deepcopy(initial) if isinstance(initial, list) else tuple_to_list(initial)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if initial_list is None or goal_list is None: return None
    initial_tuple = state_to_tuple(initial_list)
    goal_tuple = state_to_tuple(goal_list)
    if initial_tuple is None or goal_tuple is None: return None

    priority_queue = PriorityQueue()
    h_initial = manhattan_distance(initial_list, goal_list)
    if h_initial == float('inf'): return None 
    
    priority_queue.put((h_initial, initial_list, [])) 
    visited_tuples = {initial_tuple} 

    while not priority_queue.empty():
        _, current_state_list, path = priority_queue.get()
        current_tuple = state_to_tuple(current_state_list)
        if current_tuple is None: continue
        if current_tuple == goal_tuple: return path

        neighbors_data = get_neighbors(current_state_list)
        for neighbor_info in neighbors_data:
            new_state = neighbor_info['state']
            move_coord = neighbor_info['move']
            new_tuple = state_to_tuple(new_state)
            if new_tuple is None: continue

            if new_tuple not in visited_tuples:
                visited_tuples.add(new_tuple)
                h_cost_neighbor = manhattan_distance(new_state, goal_list)
                if h_cost_neighbor != float('inf'): 
                    priority_queue.put((h_cost_neighbor, new_state, path + [move_coord]))
    return None

def a_star(initial, goal):
    initial_list = deepcopy(initial) if isinstance(initial, list) else tuple_to_list(initial)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if initial_list is None or goal_list is None: return None
    initial_tuple = state_to_tuple(initial_list)
    goal_tuple = state_to_tuple(goal_list)
    if initial_tuple is None or goal_tuple is None: return None

    priority_queue = PriorityQueue()
    g_cost_initial = 0
    h_cost_initial = manhattan_distance(initial_list, goal_list)
    if h_cost_initial == float('inf'): return None
    
    f_cost_initial = g_cost_initial + h_cost_initial
    priority_queue.put((f_cost_initial, g_cost_initial, initial_list, [])) 
    visited_g_costs = {initial_tuple: g_cost_initial}

    while not priority_queue.empty():
        f_cost, g_cost_current, current_state_list, path = priority_queue.get()
        current_tuple = state_to_tuple(current_state_list)
        if current_tuple is None: continue
        if current_tuple == goal_tuple: return path

        if g_cost_current > visited_g_costs.get(current_tuple, float('inf')):
            continue

        neighbors_data = get_neighbors(current_state_list)
        for neighbor_info in neighbors_data:
            new_state = neighbor_info['state']
            move_coord = neighbor_info['move']
            new_tuple = state_to_tuple(new_state)
            if new_tuple is None: continue

            g_cost_neighbor = g_cost_current + 1 
            
            if g_cost_neighbor < visited_g_costs.get(new_tuple, float('inf')):
                visited_g_costs[new_tuple] = g_cost_neighbor 
                h_cost_neighbor = manhattan_distance(new_state, goal_list)
                if h_cost_neighbor != float('inf'): 
                    f_cost_neighbor = g_cost_neighbor + h_cost_neighbor
                    priority_queue.put((f_cost_neighbor, g_cost_neighbor, new_state, path + [move_coord]))
    return None


def ida_star_search_recursive(current_state_list, goal_list, g_cost, current_threshold, current_path_coords, visited_in_path_tuples):
    current_tuple = state_to_tuple(current_state_list)
    goal_tuple = state_to_tuple(goal_list) 
    if current_tuple is None or goal_tuple is None: return float('inf'), None 

    h_cost = manhattan_distance(current_state_list, goal_list)
    if h_cost == float('inf'): return float('inf'), None 

    f_cost = g_cost + h_cost
    if f_cost > current_threshold:
        return f_cost, None 

    if current_tuple == goal_tuple:
        return -1, current_path_coords 

    if current_tuple in visited_in_path_tuples:
        return float('inf'), None 
    
    visited_in_path_tuples.add(current_tuple)
    min_next_threshold = float('inf') 

    neighbors_data = get_neighbors(current_state_list)
    for neighbor_info in neighbors_data:
        new_state = neighbor_info['state']
        move_coord = neighbor_info['move']
        
        next_t, result_path = ida_star_search_recursive(
            new_state, goal_list, g_cost + 1, current_threshold, 
            current_path_coords + [move_coord], visited_in_path_tuples
        )
        
        if next_t == -1: 
            if current_tuple in visited_in_path_tuples: visited_in_path_tuples.remove(current_tuple)
            return -1, result_path 
        
        if next_t < min_next_threshold: 
            min_next_threshold = next_t
            
    if current_tuple in visited_in_path_tuples: 
        visited_in_path_tuples.remove(current_tuple)
        
    return min_next_threshold, None 


def ida_star(initial, goal):
    initial_list = deepcopy(initial) if isinstance(initial, list) else tuple_to_list(initial)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if initial_list is None or goal_list is None: return None

    threshold = manhattan_distance(initial_list, goal_list)
    if threshold == float('inf'): return None 

    while True:
        visited_for_this_iteration = set()
        next_threshold_candidate, path = ida_star_search_recursive(
            initial_list, goal_list, 0, threshold, [], visited_for_this_iteration
        )
        if next_threshold_candidate == -1: return path
        if next_threshold_candidate == float('inf'): return None
        threshold = next_threshold_candidate 
def hill_climbing(initial_state, goal, max_steps=1500):
    current_state_list = deepcopy(initial_state) if isinstance(initial_state, list) else tuple_to_list(initial_state)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if current_state_list is None or goal_list is None: return None
    goal_tuple = state_to_tuple(goal_list)
    if goal_tuple is None: return None
    path_coords = []; steps = 0
    while steps < max_steps:
        current_tuple = state_to_tuple(current_state_list)
        if current_tuple is None: return path_coords 
        if current_tuple == goal_tuple: return path_coords
        current_score = manhattan_distance(current_state_list, goal_list)
        if current_score == float('inf'): return path_coords 
        neighbors_data = get_neighbors(current_state_list)
        random.shuffle(neighbors_data) 
        best_next_state_list = None; best_next_move_coord = None; found_better = False
        for neighbor_info in neighbors_data:
            score = manhattan_distance(neighbor_info['state'], goal_list)
            if score < current_score:
                best_next_state_list = neighbor_info['state']
                best_next_move_coord = neighbor_info['move']
                found_better = True; break 
        if not found_better: return path_coords 
        current_state_list = best_next_state_list
        path_coords.append(best_next_move_coord); steps += 1
    return path_coords if state_to_tuple(current_state_list) == goal_tuple else None

def steepest_hill_climbing(initial_state, goal, max_steps=1500):
    current_state_list = deepcopy(initial_state) if isinstance(initial_state, list) else tuple_to_list(initial_state)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if current_state_list is None or goal_list is None: return None
    goal_tuple = state_to_tuple(goal_list);
    if goal_tuple is None: return None
    path_coords = []; steps = 0
    while steps < max_steps:
        current_tuple = state_to_tuple(current_state_list)
        if current_tuple is None: return path_coords 
        if current_tuple == goal_tuple: return path_coords
        current_score = manhattan_distance(current_state_list, goal_list)
        if current_score == float('inf'): return path_coords 
        neighbors_data = get_neighbors(current_state_list)
        best_neighbor_overall_list = None; best_neighbor_score = current_score; best_move_to_make = None
        for neighbor_info in neighbors_data:
            score = manhattan_distance(neighbor_info['state'], goal_list)
            if score < best_neighbor_score: 
                best_neighbor_score = score; best_neighbor_overall_list = neighbor_info['state']
                best_move_to_make = neighbor_info['move']
        if best_neighbor_overall_list is None: return path_coords
        current_state_list = best_neighbor_overall_list
        path_coords.append(best_move_to_make); steps += 1
    return path_coords if state_to_tuple(current_state_list) == goal_tuple else None

def stochastic_hill_climbing(initial_state, goal, max_steps=2500):
    current_state_list = deepcopy(initial_state) if isinstance(initial_state, list) else tuple_to_list(initial_state)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if current_state_list is None or goal_list is None: return None
    goal_tuple = state_to_tuple(goal_list)
    if goal_tuple is None: return None
    path_coords = []; steps = 0
    while steps < max_steps:
        current_tuple = state_to_tuple(current_state_list)
        if current_tuple is None: return path_coords
        if current_tuple == goal_tuple: return path_coords
        current_score = manhattan_distance(current_state_list, goal_list)
        if current_score == float('inf'): return path_coords
        neighbors_data = get_neighbors(current_state_list)
        better_neighbors = []
        for neighbor_info in neighbors_data:
            score = manhattan_distance(neighbor_info['state'], goal_list)
            if score < current_score: 
                better_neighbors.append({'state': neighbor_info['state'], 'move': neighbor_info['move'], 'score': score})
        if not better_neighbors: return path_coords
        chosen_one = random.choice(better_neighbors)
        current_state_list = chosen_one['state']
        path_coords.append(chosen_one['move']); steps += 1
    return path_coords if state_to_tuple(current_state_list) == goal_tuple else None

def beam_search(initial, goal, beam_width=5, max_iterations=500):
    initial_list = deepcopy(initial) if isinstance(initial, list) else tuple_to_list(initial)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if initial_list is None or goal_list is None: return None
    initial_tuple = state_to_tuple(initial_list); goal_tuple = state_to_tuple(goal_list)
    if initial_tuple is None or goal_tuple is None: return None
    h_initial = manhattan_distance(initial_list, goal_list)
    if h_initial == float('inf'): return None
    beam = [(h_initial, initial_list, [])]; visited_global_tuples = {initial_tuple}
    iterations = 0
    while beam and iterations < max_iterations:
        iterations += 1; next_beam_candidates = []
        for h_cost, current_s_list, current_path in beam:
            current_s_tuple = state_to_tuple(current_s_list) 
            if current_s_tuple == goal_tuple: return current_path
            neighbors_data = get_neighbors(current_s_list)
            for neighbor_info in neighbors_data:
                new_s = neighbor_info['state']; new_s_tuple = state_to_tuple(new_s); move_c = neighbor_info['move']
                if new_s_tuple is None: continue
                if new_s_tuple not in visited_global_tuples:
                    visited_global_tuples.add(new_s_tuple) 
                    h_new = manhattan_distance(new_s, goal_list)
                    if h_new != float('inf'): heapq.heappush(next_beam_candidates, (h_new, new_s, current_path + [move_c]))
        if not next_beam_candidates: break 
        new_beam = [];
        for _ in range(min(beam_width, len(next_beam_candidates))):
            if next_beam_candidates: new_beam.append(heapq.heappop(next_beam_candidates))
            else: break
        beam = new_beam
    for _, s_list_final, path_final in beam:
        if state_to_tuple(s_list_final) == goal_tuple: return path_final
    return None

def simulated_annealing(initial_state, goal, initial_temp=1000, cooling_rate=0.997, min_temp=0.01, max_iterations=50000):
    current_s_list = deepcopy(initial_state) if isinstance(initial_state, list) else tuple_to_list(initial_state)
    goal_s_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if current_s_list is None or goal_s_list is None: return None
    goal_tuple = state_to_tuple(goal_s_list)
    if goal_tuple is None: return None
    current_score = manhattan_distance(current_s_list, goal_s_list)
    if current_score == float('inf'): return None
    path_coords = []; temp = initial_temp; iterations = 0
    best_state_so_far_list = deepcopy(current_s_list); best_score_so_far = current_score; best_path_so_far = []
    while temp > min_temp and iterations < max_iterations:
        current_s_tuple_check = state_to_tuple(current_s_list)
        if current_s_tuple_check == goal_tuple: return path_coords
        iterations += 1
        neighbors_data = get_neighbors(current_s_list)
        if not neighbors_data: break 
        chosen_neighbor_info = random.choice(neighbors_data)
        next_s_list = chosen_neighbor_info['state']; move_made_coord = chosen_neighbor_info['move']
        next_score = manhattan_distance(next_s_list, goal_s_list)
        if next_score == float('inf'): continue 
        delta_e = next_score - current_score 
        if delta_e < 0: 
            current_s_list = next_s_list; current_score = next_score; path_coords.append(move_made_coord)
            if current_score < best_score_so_far:
                best_score_so_far = current_score; best_state_so_far_list = deepcopy(current_s_list); best_path_so_far = deepcopy(path_coords)
        elif temp > 0 and random.random() < math.exp(-delta_e / temp): 
            current_s_list = next_s_list; current_score = next_score; path_coords.append(move_made_coord)
        temp *= cooling_rate
    if state_to_tuple(best_state_so_far_list) == goal_tuple: return best_path_so_far
    if state_to_tuple(current_s_list) == goal_tuple: return path_coords
    return None

POPULATION_SIZE = 50; MAX_GENERATIONS = 100; CHROMOSOME_LENGTH = 35 
MUTATION_RATE = 0.15; TOURNAMENT_SIZE = 5; ELITISM_COUNT = 2
def calculate_fitness_ga(chromosome_moves, initial_state_list, goal_state_tuple):
    current_s_list = deepcopy(initial_state_list); path_len = 0
    for move_coord in chromosome_moves: 
        if not (isinstance(move_coord, tuple) and len(move_coord) == 2): return -float('inf')
        blank_pos = find_blank(current_s_list)
        if blank_pos is None: return -float('inf') 
        br, bc = blank_pos; mr, mc = move_coord
        if not (is_valid(mr, mc) and abs(br - mr) + abs(bc - mc) == 1): return -10000 - path_len 
        current_s_list[br][bc], current_s_list[mr][mc] = current_s_list[mr][mc], current_s_list[br][bc]
        path_len += 1
        current_s_tuple = state_to_tuple(current_s_list)
        if current_s_tuple == goal_state_tuple: return 5000 - path_len
    heuristic_val = manhattan_distance(current_s_list, tuple_to_list(goal_state_tuple))
    if heuristic_val == float('inf'): return -float('inf')
    return 1000 - heuristic_val * 3 - path_len 
def initialize_population_ga(initial_s_list, pop_size, chromo_len):
    population = []
    for _ in range(pop_size):
        chromosome = []; current_temp_s = deepcopy(initial_s_list)
        for _ in range(chromo_len):
            neighbors_data = get_neighbors(current_temp_s)
            if not neighbors_data: break 
            chosen_neighbor_info = random.choice(neighbors_data)
            chromosome.append(chosen_neighbor_info['move'])
            current_temp_s = chosen_neighbor_info['state']
        population.append(chromosome)
    return population
def select_parents_ga(population_with_fitness): 
    if not population_with_fitness: return None, None
    actual_tournament_size = min(TOURNAMENT_SIZE, len(population_with_fitness))
    if actual_tournament_size == 0: return None, None
    parents = []
    for _ in range(2): 
        tournament = random.sample(population_with_fitness, actual_tournament_size)
        tournament.sort(key=lambda item: item[1], reverse=True) 
        parents.append(tournament[0][0]) 
    return parents[0], parents[1]
def crossover_ga(parent1_moves, parent2_moves):
    if not parent1_moves or not parent2_moves:
        return deepcopy(parent1_moves) if parent1_moves else [], deepcopy(parent2_moves) if parent2_moves else []
    min_len = min(len(parent1_moves), len(parent2_moves))
    if min_len <= 1 : return deepcopy(parent1_moves), deepcopy(parent2_moves)
    crossover_point = random.randint(1, min_len -1)
    offspring1_moves = parent1_moves[:crossover_point] + parent2_moves[crossover_point:]
    offspring2_moves = parent2_moves[:crossover_point] + parent1_moves[crossover_point:]
    return offspring1_moves[:CHROMOSOME_LENGTH], offspring2_moves[:CHROMOSOME_LENGTH]
def mutate_ga(chromosome_moves, initial_s_list): 
    if not chromosome_moves or random.random() >= MUTATION_RATE:
        return deepcopy(chromosome_moves)
    mutated_chromo = deepcopy(chromosome_moves)
    idx_to_mutate = random.randint(0, len(mutated_chromo) - 1)
    temp_s_at_mutation = deepcopy(initial_s_list); valid_path_to_mutation = True
    for i in range(idx_to_mutate):
        move_coord = mutated_chromo[i]
        blank_pos = find_blank(temp_s_at_mutation)
        if blank_pos is None: valid_path_to_mutation = False; break
        br, bc = blank_pos; mr, mc = move_coord
        if not (is_valid(mr,mc) and abs(br-mr)+abs(bc-mc)==1): valid_path_to_mutation = False; break
        temp_s_at_mutation[br][bc], temp_s_at_mutation[mr][mc] = temp_s_at_mutation[mr][mc], temp_s_at_mutation[br][bc]
    if valid_path_to_mutation:
        neighbors_at_mutation = get_neighbors(temp_s_at_mutation)
        if neighbors_at_mutation:
            new_random_move_info = random.choice(neighbors_at_mutation)
            mutated_chromo[idx_to_mutate] = new_random_move_info['move'] 
            return mutated_chromo
    return deepcopy(chromosome_moves) 
def genetic_algorithm(initial_state, goal_state):
    initial_s_list = deepcopy(initial_state) if isinstance(initial_state, list) else tuple_to_list(initial_state)
    goal_s_list = deepcopy(goal_state) if isinstance(goal_state, list) else tuple_to_list(goal_state)
    if initial_s_list is None or goal_s_list is None: return None
    goal_s_tuple = state_to_tuple(goal_s_list)
    if goal_s_tuple is None: return None
    population_moves = initialize_population_ga(initial_s_list, POPULATION_SIZE, CHROMOSOME_LENGTH)
    if not population_moves: return None
    best_overall_chromosome_moves = None; best_overall_fitness = -float('inf')
    for generation in range(MAX_GENERATIONS):
        population_with_fitness = []
        for chromo_moves in population_moves:
            fitness = calculate_fitness_ga(chromo_moves, initial_s_list, goal_s_tuple)
            population_with_fitness.append((chromo_moves, fitness))
            if fitness > best_overall_fitness:
                best_overall_fitness = fitness; best_overall_chromosome_moves = chromo_moves
                if fitness >= (5000 - CHROMOSOME_LENGTH): 
                     temp_s_verify = deepcopy(initial_s_list); path_valid_and_reaches_goal = True
                     for i_mv, mv_coord in enumerate(best_overall_chromosome_moves):
                         bp = find_blank(temp_s_verify)
                         if bp is None: path_valid_and_reaches_goal = False; break
                         br_v, bc_v = bp; mr_v, mc_v = mv_coord
                         if not(is_valid(mr_v,mc_v) and abs(br_v-mr_v)+abs(bc_v-mc_v)==1): path_valid_and_reaches_goal=False; break
                         temp_s_verify[br_v][bc_v], temp_s_verify[mr_v][mc_v] = temp_s_verify[mr_v][mc_v], temp_s_verify[br_v][bc_v]
                         if state_to_tuple(temp_s_verify) == goal_s_tuple:
                             return best_overall_chromosome_moves[:i_mv+1] 
        if not population_with_fitness: break 
        population_with_fitness.sort(key=lambda item: item[1], reverse=True) 
        new_population_moves = []
        for i in range(min(ELITISM_COUNT, len(population_with_fitness))): new_population_moves.append(population_with_fitness[i][0]) 
        while len(new_population_moves) < POPULATION_SIZE:
            p1_moves, p2_moves = select_parents_ga(population_with_fitness)
            if p1_moves is None or p2_moves is None: break 
            off1_moves, off2_moves = crossover_ga(p1_moves, p2_moves)
            mut_off1_moves = mutate_ga(off1_moves, initial_s_list)
            mut_off2_moves = mutate_ga(off2_moves, initial_s_list)
            if len(new_population_moves) < POPULATION_SIZE: new_population_moves.append(mut_off1_moves)
            if len(new_population_moves) < POPULATION_SIZE: new_population_moves.append(mut_off2_moves)
        if not new_population_moves: break 
        population_moves = new_population_moves
    if best_overall_chromosome_moves:
        temp_s_final_check = deepcopy(initial_s_list); path_len_final = 0
        for i_mv_f, mv_coord_f in enumerate(best_overall_chromosome_moves):
            bp_f = find_blank(temp_s_final_check)
            if bp_f is None: break 
            br_f, bc_f = bp_f; mr_f, mc_f = mv_coord_f
            if not(is_valid(mr_f,mc_f) and abs(br_f-mr_f)+abs(bc_f-mc_f)==1): break
            temp_s_final_check[br_f][bc_f], temp_s_final_check[mr_f][mc_f] = temp_s_final_check[mr_f][mc_f], temp_s_final_check[br_f][bc_f]
            path_len_final = i_mv_f + 1
            if state_to_tuple(temp_s_final_check) == goal_s_tuple:
                return best_overall_chromosome_moves[:path_len_final]
    return None 
def and_or_search_recursive(state_list, goal_list, path_coords, visited_path_tuples):
    state_tuple = state_to_tuple(state_list)
    goal_tuple = state_to_tuple(goal_list)
    if state_tuple is None or goal_tuple is None: return None
    if state_tuple == goal_tuple: return path_coords
    if state_tuple in visited_path_tuples: return None 
    visited_path_tuples.add(state_tuple)
    neighbors_data = get_neighbors(state_list)
    neighbors_data.sort(key=lambda info: manhattan_distance(info['state'], goal_list))
    for neighbor_info in neighbors_data:
        result_p = and_or_search_recursive(neighbor_info['state'], goal_list, path_coords + [neighbor_info['move']], visited_path_tuples)
        if result_p is not None: 
            if state_tuple in visited_path_tuples: visited_path_tuples.remove(state_tuple) 
            return result_p 
    if state_tuple in visited_path_tuples: visited_path_tuples.remove(state_tuple)
    return None

def and_or_search(initial, goal):
    initial_list = deepcopy(initial) if isinstance(initial, list) else tuple_to_list(initial)
    goal_list = deepcopy(goal) if isinstance(goal, list) else tuple_to_list(goal)
    if initial_list is None or goal_list is None: return None
    return and_or_search_recursive(initial_list, goal_list, [], set())

def and_or_search_visual_recursive_gen(current_state_list, goal_list, current_path_coords, visited_path_tuples):
    state_tuple = state_to_tuple(current_state_list)
    goal_tuple = state_to_tuple(goal_list)
    yield ('AND_STATE', deepcopy(current_state_list), deepcopy(current_path_coords))
    if state_tuple == goal_tuple:
        yield ('GOAL_FOUND', deepcopy(current_path_coords)); return True 
    if state_tuple in visited_path_tuples:
        yield ('INFO', f"State {state_tuple} already in current exploration path. Pruning.", deepcopy(current_path_coords)); return False 
    visited_path_tuples.add(state_tuple)
    neighbors_data = get_neighbors(current_state_list) 
    if not neighbors_data:
        yield ('INFO', f"No valid (or unvisited by this path) neighbors from {state_tuple}. Dead end.", deepcopy(current_path_coords))
    else:
        neighbors_data.sort(key=lambda info: manhattan_distance(info['state'], goal_list))
        yield ('OR_OPTIONS', deepcopy(neighbors_data), deepcopy(current_path_coords))
        for i, neighbor_info in enumerate(neighbors_data):
            chosen_neighbor_state_list = neighbor_info['state']
            tile_that_moved_coord = neighbor_info['move']
            yield ('CHOSEN_OR', deepcopy(neighbor_info), i, deepcopy(current_path_coords))
            if (yield from and_or_search_visual_recursive_gen(
                chosen_neighbor_state_list, goal_list,
                current_path_coords + [tile_that_moved_coord],
                visited_path_tuples )):
                if state_tuple in visited_path_tuples: visited_path_tuples.remove(state_tuple)
                return True 
            yield ('BACKTRACK_FROM_OR', deepcopy(neighbor_info), deepcopy(current_path_coords))
    if state_tuple in visited_path_tuples: visited_path_tuples.remove(state_tuple)
    return False

def and_or_search_visual(initial_state_list, goal_state_list):
    initial_copy = deepcopy(initial_state_list); goal_copy = deepcopy(goal_state_list)
    solution_was_found_flag = False
    recursive_gen = and_or_search_visual_recursive_gen(initial_copy, goal_copy, [], set())
    for item_yielded in recursive_gen:
        if item_yielded[0] == 'GOAL_FOUND': solution_was_found_flag = True
        yield item_yielded
    if not solution_was_found_flag: yield ('NO_SOLUTION_OVERALL', initial_copy, []) 

def find_tile_general(board_list_of_lists, tile_value):
    if not isinstance(board_list_of_lists, list) or len(board_list_of_lists) != 3:
        return None
    for r_idx, row in enumerate(board_list_of_lists):
        if not isinstance(row, list) or len(row) != 3:
            return None
        for c_idx, val in enumerate(row):
            if not isinstance(val, int): 
                return None
            if val == tile_value:
                return r_idx, c_idx
    return None

def are_tiles_adjacent_3_6_csp(board_list_of_lists):
    pos3 = find_tile_general(board_list_of_lists, 3)
    pos6 = find_tile_general(board_list_of_lists, 6)
    if not pos3 or not pos6:
        return False 
    r3, c3 = pos3
    r6, c6 = pos6
    return abs(r3 - r6) + abs(c3 - c6) == 1

def get_valid_empty_tile_moves_csp(board_list_of_lists):
    empty_pos = find_blank(board_list_of_lists)
    if empty_pos is None:
        return []
    x, y = empty_pos
    possible_deltas_for_empty = [] 
    
    if x > 0: possible_deltas_for_empty.append({'original_tile_moved_from': (x-1, y), 'new_empty_pos': (x-1, y), 'empty_delta': (-1,0)})
    if x < 2: possible_deltas_for_empty.append({'original_tile_moved_from': (x+1, y), 'new_empty_pos': (x+1, y), 'empty_delta': (1,0)})
    if y > 0: possible_deltas_for_empty.append({'original_tile_moved_from': (x, y-1), 'new_empty_pos': (x, y-1), 'empty_delta': (0,-1)})
    if y < 2: possible_deltas_for_empty.append({'original_tile_moved_from': (x, y+1), 'new_empty_pos': (x, y+1), 'empty_delta': (0,1)})
    return possible_deltas_for_empty


def apply_move_csp(board_list_of_lists, empty_pos_current, new_empty_pos_target):
    new_board = deepcopy(board_list_of_lists)
    ex, ey = empty_pos_current
    nex, ney = new_empty_pos_target
    new_board[ex][ey], new_board[nex][ney] = new_board[nex][ney], new_board[ex][ey]
    return new_board

def is_valid_board_values_csp(board_list_of_lists):
    seen = set()
    count = 0
    if not isinstance(board_list_of_lists, list) or len(board_list_of_lists) != 3:
        return False
    for row in board_list_of_lists:
        if not isinstance(row, list) or len(row) != 3:
            return False
        for val in row:
            if not isinstance(val, int) or not (0 <= val <= 8):
                return False
            if val != 0: 
                if val in seen:
                    return False 
                seen.add(val)
            count += 1
    return count == 9 and len(seen) == 8 # (Constants from Pygame code, can be defined here or passed if needed)
CSP_BACKTRACKING_MAX_DEPTH = 35
CSP_FORWARD_CHECKING_MAX_DEPTH = 35
CSP_MIN_CONFLICTS_MAX_ITERATIONS = 200

def backtracking_csp(initial_state_list, goal_state_list, depth=CSP_BACKTRACKING_MAX_DEPTH):     # path stores lists of lists
    
    memoized_3_6_check = {}
    def _is_3_6_adjacent_memoized(state_tuple):
        if state_tuple in memoized_3_6_check:
            return memoized_3_6_check[state_tuple]         
        state_list_for_check = tuple_to_list(state_tuple)
        if state_list_for_check is None: 
            result = False
        else:
            result = are_tiles_adjacent_3_6_csp(state_list_for_check)
        memoized_3_6_check[state_tuple] = result
        return result

    def _backtrack_recursive(current_state_list, current_path_list_of_states, visited_set_of_tuples, current_depth):
        if current_state_list == goal_state_list:
            return current_path_list_of_states
        if current_depth == 0:
            return None

        empty_pos = find_blank(current_state_list)
        if empty_pos is None: 
            return None        
        current_state_tuple_for_3_6_check = state_to_tuple(current_state_list)
        if current_state_tuple_for_3_6_check is None: return None 

        currently_3_6_adjacent = _is_3_6_adjacent_memoized(current_state_tuple_for_3_6_check)         
        potential_next_moves_info = get_neighbors(current_state_list) 

        for move_info in potential_next_moves_info:
            next_state_list = move_info['state'] 
            next_state_tuple = state_to_tuple(next_state_list)
            if next_state_tuple is None: 
                continue             
            if currently_3_6_adjacent:
                if not _is_3_6_adjacent_memoized(next_state_tuple):
                    continue 

            if next_state_tuple not in visited_set_of_tuples:
                visited_set_of_tuples.add(next_state_tuple)
                new_result_path = _backtrack_recursive(
                    next_state_list,
                    current_path_list_of_states + [next_state_list],
                    visited_set_of_tuples,
                    current_depth - 1
                )
                if new_result_path:
                    return new_result_path
                visited_set_of_tuples.remove(next_state_tuple) 
        return None

    initial_state_tuple = state_to_tuple(initial_state_list)
    if initial_state_tuple is None: return None 

    return _backtrack_recursive(deepcopy(initial_state_list), [deepcopy(initial_state_list)], {initial_state_tuple}, depth)


def forward_checking_csp(initial_state_list, goal_state_list, depth=CSP_FORWARD_CHECKING_MAX_DEPTH):
    def _fc_recursive(current_state_list, current_path_list_of_states, visited_set_of_tuples, current_depth):
        if current_state_list == goal_state_list:
            return current_path_list_of_states
        if current_depth == 0:
            return None         
        potential_next_moves_info = get_neighbors(current_state_list)

        for move_info in potential_next_moves_info:
            next_state_list = move_info['state']
            next_state_tuple = state_to_tuple(next_state_list)
            if next_state_tuple is None: continue             
            if next_state_tuple not in visited_set_of_tuples:
                visited_set_of_tuples.add(next_state_tuple)
                new_result_path = _fc_recursive(
                    next_state_list,
                    current_path_list_of_states + [next_state_list],
                    visited_set_of_tuples,
                    current_depth - 1
                )
                if new_result_path:
                    return new_result_path
                visited_set_of_tuples.remove(next_state_tuple) 
        return None

    initial_state_tuple = state_to_tuple(initial_state_list)
    if initial_state_tuple is None: return None

    return _fc_recursive(deepcopy(initial_state_list), [deepcopy(initial_state_list)], {initial_state_tuple}, depth)


def ac3_generate_board_csp():
    max_attempts = 2000
    for _ in range(max_attempts):
        nums = list(range(9)) 
        random.shuffle(nums)
        board = [nums[i*3:(i+1)*3] for i in range(3)]                 
        if is_valid_board_values_csp(board) and \
           is_solvable(board) and \
           are_tiles_adjacent_3_6_csp(board):
            return board

    print(f"Warning: Không thể tạo bảng AC-3 với 3&6 kề nhau sau {max_attempts} lần thử.")     
    fallback_board = [[1, 2, 3], [4, 5, 6], [0, 7, 8]] 
    if is_valid_board_values_csp(fallback_board) and \
       is_solvable(fallback_board) and \
       are_tiles_adjacent_3_6_csp(fallback_board): 
        print("Dùng fallback board có 3&6 kề nhau.")
        return fallback_board     
        for _ in range(100): 
            nums = list(range(9)); random.shuffle(nums)
            b_fallback_solvable = [nums[i*3:(i+1)*3] for i in range(3)]
            if is_valid_board_values_csp(b_fallback_solvable) and is_solvable(b_fallback_solvable):
                print("Dùng fallback board ngẫu nhiên chỉ đảm bảo giải được (3&6 có thể không kề).")
                return b_fallback_solvable
            
    print("CRITICAL: Không thể tạo fallback board hợp lệ.")
    return None


def min_conflicts_csp(initial_state_list, goal_state_list, max_iterations=CSP_MIN_CONFLICTS_MAX_ITERATIONS):
    current_state = deepcopy(initial_state_list)
    path = [deepcopy(current_state)]

    if current_state == goal_state_list:
        return path

    for _ in range(max_iterations):
        if current_state == goal_state_list:
            return path 
        neighbor_options_info = []
        potential_next_states_info = get_neighbors(current_state)

        if not potential_next_states_info:             return path 

        for move_info in potential_next_states_info:
            next_s_list = move_info['state']             
            h_score = manhattan_distance(next_s_list, goal_state_list)
            if h_score == float('inf'): 
                continue
            neighbor_options_info.append({'state': next_s_list, 'score': h_score})
        
        if not neighbor_options_info:             return path         
        neighbor_options_info.sort(key=lambda x: x['score'])
        
        min_conflict_score = neighbor_options_info[0]['score']         
        best_options_states = [info['state'] for info in neighbor_options_info if info['score'] == min_conflict_score]
        
        if not best_options_states:             return path

        current_state = random.choice(best_options_states)
        path.append(deepcopy(current_state))     
        return path 
Q_TABLE_GLOBAL = {} 
TRAINING_IN_PROGRESS = False
LAST_TRAINED_INITIAL_STATE_TUPLE = None 
LAST_TRAINED_GOAL_STATE_TUPLE = None

def get_valid_actions_for_q(state_list):
    valid_actions = []; blank_pos = find_blank(state_list)
    if blank_pos is None: return [] 
    blank_r, blank_c = blank_pos
    for dr, dc in moves_delta: 
        new_blank_r, new_blank_c = blank_r + dr, blank_c + dc
        if is_valid(new_blank_r, new_blank_c): valid_actions.append((dr, dc)) 
    return valid_actions

def choose_action_epsilon_greedy(q_table, state_tuple, valid_actions, epsilon):
    if not valid_actions: return None 
    if random.random() < epsilon: return random.choice(valid_actions)
    else: 
        q_values_for_state = q_table.get(state_tuple, {})
        max_q = -float('inf'); best_actions = []
        if not q_values_for_state and valid_actions: return random.choice(valid_actions)
        for action in valid_actions:
            q_val = q_values_for_state.get(action, 0.0) 
            if q_val > max_q: max_q = q_val; best_actions = [action]
            elif q_val == max_q: best_actions.append(action)
        if best_actions: return random.choice(best_actions) 
        elif valid_actions: return random.choice(valid_actions)
        return None

def q_learning_train_and_solve(initial_state_raw, goal_state_raw, 
                               episodes=2000, max_steps_per_episode=150, 
                               alpha=0.1, gamma=0.95, 
                               epsilon_start=1.0, epsilon_end=0.01, 
                               force_retrain=False):
    global Q_TABLE_GLOBAL, TRAINING_IN_PROGRESS, LAST_TRAINED_INITIAL_STATE_TUPLE, LAST_TRAINED_GOAL_STATE_TUPLE
    initial_list = tuple_to_list(initial_state_raw) if isinstance(initial_state_raw, tuple) else deepcopy(initial_state_raw)
    goal_list = tuple_to_list(goal_state_raw) if isinstance(goal_state_raw, tuple) else deepcopy(goal_state_raw)
    if initial_list is None or goal_list is None: return None
    initial_tuple = state_to_tuple(initial_list)
    goal_tuple = state_to_tuple(goal_list)
    if initial_tuple is None or goal_tuple is None: return None

    needs_training = force_retrain or not Q_TABLE_GLOBAL or \
                     LAST_TRAINED_INITIAL_STATE_TUPLE != initial_tuple or \
                     LAST_TRAINED_GOAL_STATE_TUPLE != goal_tuple
    if needs_training:
        if TRAINING_IN_PROGRESS: print("Q-Learning: Training in progress. Please wait."); return None 
        TRAINING_IN_PROGRESS = True
        print(f"Q-Learning: Starting training for {episodes} episodes...")
        Q_TABLE_GLOBAL.clear(); epsilon_decay_episodes = episodes * 0.75 
        if epsilon_decay_episodes == 0: epsilon_decay_episodes = 1
        for episode in range(episodes):
            current_s_list = deepcopy(initial_list) 
            epsilon = epsilon_end + (epsilon_start - epsilon_end) * math.exp(-1. * episode / (epsilon_decay_episodes / 5))
            for step in range(max_steps_per_episode):
                current_s_tuple = state_to_tuple(current_s_list)
                if current_s_tuple is None: break 
                valid_actions = get_valid_actions_for_q(current_s_list)
                if not valid_actions: break 
                action_delta = choose_action_epsilon_greedy(Q_TABLE_GLOBAL, current_s_tuple, valid_actions, epsilon)
                if action_delta is None: break 
                next_s_list = deepcopy(current_s_list)
                br, bc = find_blank(next_s_list); dr, dc = action_delta
                new_blank_r, new_blank_c = br + dr, bc + dc 
                next_s_list[br][bc], next_s_list[new_blank_r][new_blank_c] = next_s_list[new_blank_r][new_blank_c], next_s_list[br][bc]
                next_s_tuple = state_to_tuple(next_s_list)
                if next_s_tuple is None: break 
                reward = -1; is_terminal_next_state = False
                if next_s_tuple == goal_tuple: reward = 100; is_terminal_next_state = True
                if current_s_tuple not in Q_TABLE_GLOBAL: Q_TABLE_GLOBAL[current_s_tuple] = {}
                if action_delta not in Q_TABLE_GLOBAL[current_s_tuple]: Q_TABLE_GLOBAL[current_s_tuple][action_delta] = 0.0
                old_q_value = Q_TABLE_GLOBAL[current_s_tuple][action_delta]
                max_q_next_state = 0.0
                if not is_terminal_next_state: 
                    next_valid_actions_from_s_prime = get_valid_actions_for_q(next_s_list)
                    if next_valid_actions_from_s_prime:
                        q_values_s_prime = Q_TABLE_GLOBAL.get(next_s_tuple, {})
                        if q_values_s_prime: 
                            max_q_next_state = max(q_values_s_prime.get(act_prime, 0.0) for act_prime in next_valid_actions_from_s_prime)
                td_target = reward + gamma * max_q_next_state
                td_error = td_target - old_q_value
                Q_TABLE_GLOBAL[current_s_tuple][action_delta] = old_q_value + alpha * td_error
                current_s_list = next_s_list 
                if is_terminal_next_state or step == max_steps_per_episode -1 : break 
            if (episode + 1) % (episodes // 20 if episodes >= 20 else 1) == 0:
                print(f"Q-Learning Training: Episode {episode+1}/{episodes} completed. Epsilon: {epsilon:.4f}. Q-Table size: {len(Q_TABLE_GLOBAL)}")
        LAST_TRAINED_INITIAL_STATE_TUPLE = initial_tuple; LAST_TRAINED_GOAL_STATE_TUPLE = goal_tuple
        TRAINING_IN_PROGRESS = False; print("Q-Learning: Training finished.")
    else: print("Q-Learning: Using existing Q-Table.")

    if not Q_TABLE_GLOBAL: print("Q-Learning: Q-Table is empty. Cannot solve."); return None
    print("Q-Learning: Solving using the learned Q-Table...")
    path_to_goal_coords = []; current_solve_s_list = deepcopy(initial_list)
    max_solve_steps = max_steps_per_episode * 2 
    for _ in range(max_solve_steps):
        current_solve_s_tuple = state_to_tuple(current_solve_s_list)
        if current_solve_s_tuple == goal_tuple:
            print(f"Q-Learning: Goal reached in {_} steps during solving!"); return path_to_goal_coords
        valid_actions_solve = get_valid_actions_for_q(current_solve_s_list)
        if not valid_actions_solve: print("Q-Learning: No valid actions from current state during solving. Stuck."); return None 
        q_values_current_solve_state = Q_TABLE_GLOBAL.get(current_solve_s_tuple, {})
        best_q_solve = -float('inf'); chosen_action_solve = None; potential_best_actions = []
        if not q_values_current_solve_state and valid_actions_solve : 
             chosen_action_solve = random.choice(valid_actions_solve) 
        else:
            for act_solve in valid_actions_solve:
                q_val_solve = q_values_current_solve_state.get(act_solve, 0.0) 
                if q_val_solve > best_q_solve: best_q_solve = q_val_solve; potential_best_actions = [act_solve]
                elif q_val_solve == best_q_solve: potential_best_actions.append(act_solve)
            if potential_best_actions: chosen_action_solve = random.choice(potential_best_actions)
            elif valid_actions_solve: chosen_action_solve = random.choice(valid_actions_solve)
            else: print("Q-Learning Error: Stuck during solving phase."); return None
        br_s, bc_s = find_blank(current_solve_s_list); dr_s, dc_s = chosen_action_solve 
        moved_tile_r, moved_tile_c = br_s + dr_s, bc_s + dc_s
        path_to_goal_coords.append((moved_tile_r, moved_tile_c)) 
        current_solve_s_list[br_s][bc_s], current_solve_s_list[moved_tile_r][moved_tile_c] = \
            current_solve_s_list[moved_tile_r][moved_tile_c], current_solve_s_list[br_s][bc_s]
    print(f"Q-Learning: Failed to reach goal within {max_solve_steps} steps during solving.")
    return None 
def is_solvable(state):
    state_list = tuple_to_list(state) if isinstance(state, tuple) else state
    if state_list is None: return False 
    flat_state = []
    try:
        for row in state_list:
            if not isinstance(row, list) or len(row) != 3: return False
            for num in row:
                 if not isinstance(num, int): return False
                 if num != 0: flat_state.append(num) 
        if len(flat_state) != 8: return False 
    except (TypeError, IndexError): return False 
    inversions = 0
    for i in range(len(flat_state)):
        for j in range(i + 1, len(flat_state)):
            if flat_state[i] > flat_state[j]: inversions += 1
    return inversions % 2 == 0 
    GOAL_STATE_TUPLE_CONFORMANT = state_to_tuple([[1, 2, 3], [4, 5, 6], [7, 8, 0]]) 
def physical_result_8puzzle(state_tuple, move_delta_action):
    state_list = tuple_to_list(state_tuple)
    if state_list is None: return None
    blank_pos = find_blank(state_list)
    if blank_pos is None: return None 
    blank_r, blank_c = blank_pos; dr_blank, dc_blank = move_delta_action 
    tile_to_swap_r, tile_to_swap_c = blank_r + dr_blank, blank_c + dc_blank
    if is_valid(tile_to_swap_r, tile_to_swap_c): 
        state_list[blank_r][blank_c], state_list[tile_to_swap_r][tile_to_swap_c] = \
            state_list[tile_to_swap_r][tile_to_swap_c], state_list[blank_r][blank_c]
        return state_to_tuple(state_list)
    else: return state_tuple 
def belief_state_update_8puzzle(belief_state_frozenset, move_delta_for_blank):
    next_possible_physical_states = set()
    if not isinstance(belief_state_frozenset, frozenset): return frozenset()
    for s_tuple in belief_state_frozenset:
        next_s_tuple = physical_result_8puzzle(s_tuple, move_delta_for_blank)
        if next_s_tuple is not None: next_possible_physical_states.add(next_s_tuple)
    return frozenset(next_possible_physical_states)
def is_goal_belief_state_8puzzle(belief_state_frozenset, target_goal_tuple):
    if target_goal_tuple is None: return False
    return belief_state_frozenset == frozenset([target_goal_tuple])
def conformant_bfs_8puzzle(initial_belief_fset, goal_s_tuple, possible_moves_deltas):
    if not initial_belief_fset or goal_s_tuple is None: return None
    queue = deque([(initial_belief_fset, [])]); visited_belief_fsets = {initial_belief_fset}
    max_visited_limit = 2000; count_visited = 0
    while queue:
        count_visited +=1
        if count_visited > max_visited_limit : print(f"Conformant BFS: Reached max visited limit {max_visited_limit}"); return None
        current_b_fset, current_plan = queue.popleft()
        if is_goal_belief_state_8puzzle(current_b_fset, goal_s_tuple):
            return [move_names.get(delta, str(delta)) for delta in current_plan]
        for move_d in possible_moves_deltas: 
            next_b_fset = belief_state_update_8puzzle(current_b_fset, move_d)
            if next_b_fset and next_b_fset not in visited_belief_fsets: 
                visited_belief_fsets.add(next_b_fset)
                queue.append((next_b_fset, current_plan + [move_d]))
    return None
def search_no_observation(initial_state_list_for_conformant, goal_state_list_for_conformant):
    print("\n--- Running 'No Observation' Demo (Conformant BFS) ---")
    initial_tuple_conf = state_to_tuple(initial_state_list_for_conformant)
    goal_tuple_conf = state_to_tuple(goal_state_list_for_conformant)
    if initial_tuple_conf is None or goal_tuple_conf is None:
        print("Conformant Demo Error: Invalid initial or goal state format."); return None 
    demo_initial_belief = frozenset([initial_tuple_conf]) 
    if initial_tuple_conf == goal_tuple_conf: 
         demo_initial_belief = frozenset([goal_tuple_conf])
    print(f"Conformant Demo: Initial DEMO belief state (size={len(demo_initial_belief)}):")
    if is_goal_belief_state_8puzzle(demo_initial_belief, goal_tuple_conf):
        print("Conformant Demo: Initial belief state is already the goal belief state."); return [] 
    start_time_conf = time.time()
    plan_of_action_names = conformant_bfs_8puzzle(demo_initial_belief, goal_tuple_conf, moves_delta)
    duration_conf = time.time() - start_time_conf
    print(f"Conformant BFS (Demo) finished in {duration_conf:.4f} seconds.")
    if plan_of_action_names is not None:
        print(f">>> Conformant Plan Found (for DEMO belief): {plan_of_action_names} ({len(plan_of_action_names)} steps)")
    else:
        print(f">>> No Conformant Plan Found (for DEMO belief).")
    return None

