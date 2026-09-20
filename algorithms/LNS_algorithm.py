import math

from Util.util import *
from globals import *
from Util.random_numbers import get_random_float, get_random_index, get_random_from_range


def get_delta_distance(point1, point2, candidates):
    sub_path = [point1] + candidates + [point2]

    delta = 0
    for i in range(1, len(sub_path)):
        delta+=cartesian(sub_path[i-1], sub_path[i])

    delta-= cartesian(point1, point2)
    return delta


def cheapest_insertion(station, relevant_points, distance_limit):
    relevant_points = copy.deepcopy(relevant_points)
    path = [station, station]
    temp_length = 0

    count = 0

    while len(relevant_points) > 0:
        # print(count, len(relevant_points), len(path), temp_length)
        best_insertion = None
        points_to_remove = []
        for point in relevant_points:
            best_insertion_index = None
            for i in range(1, len(path)):
                delta = get_delta_distance(path[i - 1], path[i], [point])
                if temp_length+delta <= distance_limit:
                    if best_insertion_index is None or delta < best_insertion_index[1]:
                        best_insertion_index = i, delta
            if best_insertion_index is not None:
                if best_insertion is None or best_insertion_index[1]<best_insertion[2]:
                    best_insertion = (point, best_insertion_index[0], best_insertion_index[1])
            else:
                points_to_remove.append(point)

        if best_insertion is None:
            break

        path.insert(best_insertion[1], best_insertion[0])
        temp_length += best_insertion[2]
        relevant_points.remove(best_insertion[0])
        for point in points_to_remove:
            relevant_points.remove(point)

        count += 1

    return path[1:]


# Destroy operators

def destroy_worst_cost(path, k, time_function):
    k = min(k, len(path) - 1)
    deltas = dict()
    path_with_station = [NORMALIZED_CHARGE_STATION[0]] + path

    for i in range(1, len(path_with_station)-1):
        delta = get_delta_distance(path_with_station[i - 1], path_with_station[i + 1], [path_with_station[i]])
        deltas[i] = delta

    deleted = []
    for _ in range(k):
        i = max(deltas, key=lambda k: deltas[k])
        deleted.append(path_with_station[i])
        del path_with_station[i]
        for j in range(i, len(path_with_station)-1):
            deltas[j] = deltas[j+1]
        del deltas[len(path_with_station)-1]
        deltas[i-1] = get_delta_distance(path_with_station[i - 2], path_with_station[i], [path_with_station[i - 1]])
        if i<len(path_with_station)-1:
            deltas[i] = get_delta_distance(path_with_station[i - 1], path_with_station[i + 1], [path_with_station[i]])

    return path_with_station[1:], deleted


def destroy_worst_cost_seq(path, k, time_function):
    k=min(k, len(path)-1)
    path_with_station = [NORMALIZED_CHARGE_STATION[0]] + path

    higher_cost = None
    for i in range(1, len(path_with_station)-k):
        delta = get_delta_distance(path_with_station[i - 1], path_with_station[i + k], path_with_station[i:i + k])
        if higher_cost is None or delta > higher_cost[1]:
            higher_cost = (i, delta)

    i = higher_cost[0]
    deleted = path_with_station[i:i + k]
    path = path_with_station[1:i]+path_with_station[i+k:]
    return path, deleted


def destroy_worst_profit(path, k, time_function):
    k = min(k, len(path) - 1)

    deleted = []
    for _ in range(k):
        highest_path_profit = None
        for i in range(len(path)-1):
            potential_path = path[:i]+path[i+1:]
            path_profit = evaluate_path(potential_path, time_function)[1]
            if highest_path_profit is None or path_profit > highest_path_profit[1]:
                highest_path_profit = (i, path_profit)
        i = highest_path_profit[0]
        deleted.append(path[i])
        path = path[:i]+path[i+1:]

    return path, deleted


def destroy_worst_profit_seq(path, k, time_function):
    k = min(k, len(path) - 1)

    highest_path_profit = None
    for i in range(len(path) - k):
        potential_path = path[:i] + path[i + k:]
        path_profit = evaluate_path(potential_path, time_function)[1]
        if highest_path_profit is None or path_profit > highest_path_profit[1]:
            highest_path_profit = (i, path_profit)

    i = highest_path_profit[0]
    deleted = path[i:i + k]
    path = path[:i] + path[i + k:]
    return path, deleted


def destroy_random(path, k, time_function):
    k = min(k, len(path) - 1)

    deleted = []
    for _ in range(k):
        rand_float = get_random_float()
        index = int(rand_float*(len(path)-1))
        deleted.append(path[index])
        path = path[:index] + path[index+1:]
    return path, deleted


def destroy_random_seq(path, k, time_function):
    k = min(k, len(path) - 1)
    rand_float = get_random_float()
    index = int(rand_float*(len(path)-k))
    # print("\t", k, len(path), len(path) - k, rand_float, index)
    # if NORMALIZED_CHARGE_STATION[0] in path[index:index+k]:
    #     print("$$$$$$$$$$", path[index:index+k], "\n\t", path)
    deleted = path[index:index + k]
    path = path[:index] + path[index+k:]
    return path, deleted


def destroy_shaw(path, k, time_function):
    k = min(k, len(path) - 1)
    index = get_random_index(path[:-1])

    indices = [index]

    def relativeness(i):
        if i in indices:
            return 0
        else:
            point = path[i]
            point_relativeness_list = []
            for j in indices:
                dist = cartesian(path[j], point)
                if dist==0:
                    return -1
                point_relativeness_list.append(1/dist)
            return max(point_relativeness_list)

    for i in range(1, k):
        relativeness_list = [relativeness(j)for j in range(len(path[:-1]))]
        if -1 in relativeness_list:
            indices.append(relativeness_list.index(-1))
            continue
        p = get_random_float()
        norm_p = p*sum(relativeness_list)
        for j in range(len(path)):
            norm_p-= relativeness_list[j]
            if norm_p <= 0:
                indices.append(j)
                break

    new_path = [path[i] for i in range(len(path)) if i not in indices]
    deleted = [path[i] for i in indices]

    return new_path, deleted


def destroy_rectangle(path, k, time_function):
    k = min(k, len(path) - 1)
    index = get_random_index(path[:-1])
    center = path[index]

    station = NORMALIZED_CHARGE_STATION[0]

    radius = abs(center[0]-([station]+path)[index][0])
    lower_bound = 0
    higher_bound = radius

    for _ in range(30):
        points_in_rectangle = get_rectangle_points(path[:-1], center, radius)
        n_points = len(points_in_rectangle)
        if n_points==k:
            break

        if n_points>k:
            higher_bound = radius
            radius = (radius+lower_bound)/2
            continue

        if n_points<k:
            lower_bound = radius
            if radius==higher_bound:
                higher_bound*=2
                radius = higher_bound
            else:
                radius = (radius+higher_bound)/2
            continue

    new_path = [path[i] for i in range(len(path)) if i not in points_in_rectangle]
    deleted = [path[i] for i in points_in_rectangle]

    return new_path, deleted


def destroy_cost_efficiency(path, k, time_function):
    k = min(k, len(path) - 1)

    path_with_station = [NORMALIZED_CHARGE_STATION[0]] + path
    deleted = []
    current_path_profit = evaluate_path(path, time_function)[1]
    for _ in range(k):
        worst_cost_efficiency = None
        potential_new_profit = None
        for i in range(1, len(path)-1):
            potential_path = path[:i]+path[i+1:]
            path_profit = evaluate_path(potential_path, time_function)[1]
            delta_profit = current_path_profit - path_profit
            delta_cost = get_delta_distance(path_with_station[i], path_with_station[i + 2], [path_with_station[i + 1]])

            if delta_cost==0:
                continue

            cost_efficiency = delta_profit / delta_cost

            if worst_cost_efficiency is None or cost_efficiency < worst_cost_efficiency[1]:
                worst_cost_efficiency = (i, cost_efficiency)
                potential_new_profit = path_profit

        if worst_cost_efficiency is None:
            break
        i = worst_cost_efficiency[0]
        deleted.append(path[i])
        path = path[:i]+path[i+1:]
        current_path_profit = potential_new_profit

    return path, deleted


def destroy_cost_efficiency_seq(path, k, time_function):
    k = min(k, len(path) - 1)

    path_with_station = [NORMALIZED_CHARGE_STATION[0]] + path
    current_path_profit = evaluate_path(path, time_function)[1]
    worst_cost_efficiency = None

    for i in range(1, len(path)-k):
            potential_path = path[:i]+path[i+k:]
            path_profit = evaluate_path(potential_path, time_function)[1]
            delta_profit = current_path_profit - path_profit
            delta_cost = get_delta_distance(path_with_station[i], path_with_station[i + k + 1], path_with_station[i + 1:i + k + 1])

            if delta_cost==0:
                continue

            cost_efficiency = delta_profit / delta_cost

            if worst_cost_efficiency is None or cost_efficiency < worst_cost_efficiency[1]:
                worst_cost_efficiency = (i, cost_efficiency)

    i = worst_cost_efficiency[0]
    deleted = path[i:i + k]
    path = path[:i]+path[i+k:]

    return path, deleted


destroy_dict = {"worst cost": destroy_worst_cost,
                "worst cost seq": destroy_worst_cost_seq,
                "worst profit": destroy_worst_profit,
                "worst profit seq": destroy_worst_profit_seq,
                "random": destroy_random,
                "random seq": destroy_random_seq,
                "shaw": destroy_shaw,
                "rectangle": destroy_rectangle,
                "cost efficiency": destroy_cost_efficiency,
                "cost efficiency seq": destroy_cost_efficiency_seq,}


# Insertion operators

def cost_value(path_with_station, node, index, time_function, current_duration, current_profit=None):
    cost = get_delta_distance(path_with_station[index - 1], path_with_station[index], [node])/DRONE_SPEED[0]
    if current_duration+cost>MAXIMUM_SORTIE_TIME[0]:
        return False
    return -1 * cost


def profit_value(path_with_station, node, index, time_function, current_duration, current_profit=None):
    cost = get_delta_distance(path_with_station[index - 1], path_with_station[index], [node])/DRONE_SPEED[0]
    if current_duration + cost > MAXIMUM_SORTIE_TIME[0]:
        return False

    # print(len(path_with_station), evaluate_path(path_with_station[1:], time_function), path_with_station)
    potential_path = path_with_station[1:index]+[node]+path_with_station[index:]
    if time_function==-2:
        return current_profit+MAP_APRIORI[0][node]
    if time_function == -1:
        return current_profit + MAP_DYNAMIC[0][node]
    return evaluate_path(potential_path, time_function)[1]


def cost_efficiency_value(path_with_station, node, index, time_function, current_duration, current_profit):
    cost = get_delta_distance(path_with_station[index - 1], path_with_station[index], [node])/DRONE_SPEED[0]
    if current_duration + cost > MAXIMUM_SORTIE_TIME[0]:
        return False
    potential_path = path_with_station[1:index] + [node] + path_with_station[index:]
    if time_function==-2:
        return (current_profit + MAP_APRIORI[0][node]) / cost
    if time_function == -1:
        return (current_profit + MAP_DYNAMIC[0][node]) / cost

    profit = evaluate_path(potential_path, time_function)[1]
    if profit==0:
        return 0
    return (profit-current_profit) / cost


INSERTIONS_INPATH_DICT = {"cost": cost_value,
                          "profit": profit_value,
                          "cost efficiency": cost_efficiency_value}


def insertion_global(path, from_neighbors, to_neighbors, time_function, insertion_heuristic_name, deleted, reverse=False, double=True):
    heuristic_function = INSERTIONS_INPATH_DICT[insertion_heuristic_name]

    path_with_station = [NORMALIZED_CHARGE_STATION[0]] + path

    while True:
        best_insertion = None
        current_duration, current_profit = evaluate_path(path_with_station[1:], time_function)

        for index in range(1, len(path_with_station)):
            relevant_points = to_neighbors[path_with_station[index-1]]
            relevant_points = [neighbor for neighbor in relevant_points if (neighbor in from_neighbors[path_with_station[index]] and neighbor!=NORMALIZED_CHARGE_STATION[0])]
            if insertion_heuristic_name == "cost" or not double:
                relevant_points = [neighbor for neighbor in relevant_points if neighbor not in path_with_station]

            for point in relevant_points:
                score = heuristic_function(path_with_station, point, index, time_function, current_duration, current_profit)
                if score==False:
                    continue
                if best_insertion is None or score>best_insertion[2]:
                    best_insertion = (point, index, score)

        if best_insertion is None:
            break

        point, index, score = best_insertion
        path_with_station = path_with_station[:index]+[point]+path_with_station[index:]

    return path_with_station[1:]


def insertion_order(path, from_neighbors, to_neighbors, time_function, insertion_heuristic_name, deleted, reverse=False, double=True):
    heuristic_function = INSERTIONS_INPATH_DICT[insertion_heuristic_name]
    if reverse:
        deleted.reverse()

    path_with_station = [NORMALIZED_CHARGE_STATION[0]] + path

    # print("B", NORMALIZED_CHARGE_STATION[0] in deleted)
    for node in deleted:
        best_insertion = None
        current_duration, current_profit = evaluate_path(path_with_station[1:], time_function)

        for index in range(1, len(path_with_station)):
            if node not in to_neighbors[path_with_station[index-1]] or node not in from_neighbors[path_with_station[index]]:
                continue

            score = heuristic_function(path_with_station, node, index, time_function, current_duration, current_profit)
            if score == False:
                    continue
            if best_insertion is None or score > best_insertion[1]:
                    best_insertion = (index, score)

        if best_insertion is None:
            continue

        index, score = best_insertion
        path_with_station = path_with_station[:index] + [node] + path_with_station[index:]

    return path_with_station[1:]


def insertion_k_regrets(path, from_neighbors, to_neighbors, time_function, insertion_heuristic_name, deleted, reverse=False, double=True):
    path_with_station = [NORMALIZED_CHARGE_STATION[0]] + path
    current_duration, current_profit = evaluate_path(path, time_function)
    k_regrets = dict()

    for node in ELLIPSE_POINTS[0]:
            if not double and node in path_with_station:
                continue
            node_ce = [] # Cost efficiencies
            for index in range(1, len(path_with_station)):
                if node not in to_neighbors[path_with_station[index-1]] or node not in from_neighbors[path_with_station[index]]:
                    continue

                score = cost_efficiency_value(path_with_station, node, index, time_function, current_duration, current_profit)
                if score == False:
                        continue

                node_ce.append(score)

            if len(node_ce)>1:
                best_ce = max(node_ce)
                k_regrets[node] = sum([best_ce-ce for ce in node_ce])

    sorted_points = sorted(k_regrets, key=k_regrets.get, reverse=True)

    for node in sorted_points:
        best_insertion = None
        current_duration, current_profit = evaluate_path(path_with_station[1:], time_function)

        for index in range(1, len(path_with_station)):
            if node not in to_neighbors[path_with_station[index]]: # or node not in from_neighbors[path_with_station[index + 1]]:
                continue

            score = cost_efficiency_value(path_with_station, node, index, time_function, current_duration, current_profit)
            if score == False:
                continue
            if best_insertion is None or score > best_insertion[1]:
                best_insertion = (index, score)

        if best_insertion is None:
            continue

        index, score = best_insertion
        path_with_station = path_with_station[:index] + [node] + path_with_station[index:]

    return path_with_station[1:]


MAP_INSERTIONS = {"cost": insertion_global,
                  "profit": insertion_global,
                  "cost efficiency": insertion_global,
                  "order": insertion_order,
                  "reverse order": insertion_order,
                  "k regret": insertion_k_regrets}


# Utility functions

def get_neighbors(path, eta, beta, max_nbrs):
    theta = beta * path_times(path, NORMALIZED_CHARGE_STATION[0])[-1]
    to_neighbors = dict()
    for node1 in ELLIPSE_POINTS[0]+[NORMALIZED_CHARGE_STATION[0]]:
        distances_from_node1 = {node2:cartesian(node1, node2) for node2 in ELLIPSE_POINTS[0]+[NORMALIZED_CHARGE_STATION[0]] if node2!=node1}
        sorted_points = sorted(distances_from_node1, key=distances_from_node1.get)
        to_neighbors[node1] = sorted_points[:eta]
        for node2 in sorted_points[eta:]:
            if distances_from_node1[node2]>theta:
                break
            to_neighbors[node1].append(node2)
            if len(to_neighbors[node1])>max_nbrs:
                break

    from_neighbors = {node1:[node2 for node2 in to_neighbors.keys() if node1 in to_neighbors[node2]] for node1 in ELLIPSE_POINTS[0]+[NORMALIZED_CHARGE_STATION[0]]}

    return from_neighbors, to_neighbors


# def get_G(path):
#     total_x = 0
#     total_y = 0
#     for point in path[:-1]:
#         y, x = point
#         total_x += x
#         total_y += y
#     G = (total_x/(len(path)-1), total_y/(len(path)-1))
#     return G
#
#
# def width(point1, point2, G, station):
#     v0 = G[0]-station[0]
#     v1 = G[1]-station[1]
#     numerator = abs(v1*(point1[0]-point2[0])-(v0*(point1[1]-point2[1])))
#     denominator = (v0**2+v1**2)**(1/2)
#     return numerator/denominator
#
#
# def depth(point, station):
#     return simple_cartesian(point, station)
#
#
# def point_evaluation(point_index, station, constants_dict, time_function, current_profit):
#     pass


def reverse_and_try(sub_paths, indices_to_reverse, to_neighbors, time_function, current_duration):
    i = indices_to_reverse[0]

    last_in_i_minus_1 = sub_paths[i - 1][-1] if len(sub_paths[i - 1]) > 0 else sub_paths[-1][-1]
    last_in_i = sub_paths[i][-1]
    first_in_i_plus_1 = sub_paths[i + 1][0]
    first_in_i = sub_paths[i][0]

    if len(indices_to_reverse)==1:

        if last_in_i in to_neighbors[last_in_i_minus_1] and first_in_i_plus_1 in to_neighbors[first_in_i]:
            duration1 = current_duration + (cartesian(last_in_i_minus_1, last_in_i) + cartesian(first_in_i, first_in_i_plus_1) - cartesian(last_in_i_minus_1, first_in_i) - cartesian(last_in_i, first_in_i_plus_1))/DRONE_SPEED[0]
            if duration1 <= MAXIMUM_SORTIE_TIME[0]:
                sub_paths[i].reverse()
                path1 = []
                for sub_path in sub_paths:
                    path1+=sub_path
                _duration1, profit1 = evaluate_path(path1, time_function) if time_function not in [-1, -2] else 1, -1
                score1 = profit1/duration1 if duration1 <= MAXIMUM_SORTIE_TIME[0] else -1
                sub_paths[i].reverse()
            else:
                path1, score1, duration1 = None, None, None
        else:
            path1, score1, duration1 = None, None, None

        if first_in_i in to_neighbors[last_in_i_minus_1] and first_in_i_plus_1 in to_neighbors[last_in_i]:
            duration2 = current_duration
            path2 = []
            for sub_path in sub_paths:
                path2+=sub_path
            _duration2, profit2 = evaluate_path(path2, time_function) if time_function not in [-1, -2] else 1, -1
            score2 = profit2/duration2 if duration2 <= MAXIMUM_SORTIE_TIME[0] else -1
        else:
            path2, score2, duration2 = None, None, None

    else:   # Recursion
        if last_in_i in to_neighbors[last_in_i_minus_1] and first_in_i_plus_1 in to_neighbors[first_in_i]:
            new_duration = current_duration + (
                        cartesian(last_in_i_minus_1, last_in_i) + cartesian(first_in_i, first_in_i_plus_1) - cartesian(
                    last_in_i_minus_1, first_in_i) - cartesian(last_in_i, first_in_i_plus_1)) / DRONE_SPEED[0]

            sub_paths[indices_to_reverse[0]].reverse()
            path1, score1, duration1 = reverse_and_try(sub_paths, indices_to_reverse[1:], to_neighbors, time_function, new_duration)
            sub_paths[indices_to_reverse[0]].reverse()

        else:
            path1, score1, duration1 = None, None, None

        if first_in_i in to_neighbors[last_in_i_minus_1] and first_in_i_plus_1 in to_neighbors[last_in_i]:
            path2, score2, duration2 = reverse_and_try(sub_paths, indices_to_reverse[1:], to_neighbors, time_function, current_duration)
        else:
            path2, score2, duration2 = None, None, None

    # Take the better one
    if path1 == None:
        return path2, score2, duration2
    if path2 == None:
        return path1, score1, duration1

    if time_function in [-1, -2]:
        return (path1, score1, duration1) if duration1<duration2 else (path2, score2, duration2)

    if score1 > score2:
        return path1, score1, duration1
    else:
        return path2, score2, duration2


def execute_3_opt(path, to_neighbors, time_function, current_cost, current_profit):
    current_score = current_profit/current_cost
    for i in range(len(path)-2):
        sub_path1 = path[:i]
        old_first_edge = cartesian(path[i-1], path[i]) if i>0 else cartesian(NORMALIZED_CHARGE_STATION[0], path[i])
        for j in range(i+1, len(path)-1):
            sub_path2 = path[i:j]
            new_first_edge = cartesian(path[i - 1], path[j]) if i > 0 else cartesian(NORMALIZED_CHARGE_STATION[0], path[j])
            for l in range(j+1, len(path)):
                sub_path3 = path[j:l]
                sub_path4 = path[l:]

                path1, score1, duration1 = reverse_and_try([sub_path1, sub_path2, sub_path3, sub_path4], [1, 2], to_neighbors, time_function, current_cost)
                additional_edges_duration = (new_first_edge + cartesian(sub_path3[-1], sub_path2[0]) + cartesian(sub_path2[-1], sub_path4[0]))/DRONE_SPEED[0]
                removed_edges_duration = (old_first_edge + cartesian(sub_path2[-1], sub_path3[0]) + cartesian(sub_path3[-1], sub_path4[0]))/DRONE_SPEED[0]
                potential_cost = current_cost + additional_edges_duration - removed_edges_duration
                path2, score2, duration2 = reverse_and_try([sub_path1, sub_path3, sub_path2, sub_path4], [1, 2], to_neighbors, time_function, potential_cost)

                if time_function in [-1,-2]:
                    if path1 is not None and duration1 < current_cost*0.99999 and (duration2 is None or duration1 < duration2):
                        cost, profit = evaluate_path(path1, time_function)
                        return path1, cost, profit
                    if path2 is not None and duration2 < current_cost*0.999999:
                        cost, profit = evaluate_path(path2, time_function)
                        return path2, cost, profit
                else:
                    if path1 is not None and score1 > current_score and (path2 is None or score1 > score2):
                        cost, profit = evaluate_path(path1, time_function)
                        return path1, cost, profit
                    if path2 is not None and score2 > current_score:
                        cost, profit = evaluate_path(path2, time_function)
                        return path2, cost, profit
    return None, None, None


def best_replace(path, from_neighbors, to_neighbors, time_function, double):
    current_duration, current_profit = evaluate_path(path, time_function)
    path_with_station = [NORMALIZED_CHARGE_STATION[0]] + path
    best_replacement = (None, None, current_duration, current_profit)

    for index in range(1, len(path_with_station)-1):
        old_point = path_with_station[index]
        relevant_points = [point for point in to_neighbors[path_with_station[index - 1]] if point!=NORMALIZED_CHARGE_STATION[0]]
        # relevant_points = [neighbor for neighbor in relevant_points if neighbor in from_neighbors[path_with_station[index+1]]]
        if not double:
            relevant_points = [neighbor for neighbor in relevant_points if neighbor not in path_with_station]
        for point in relevant_points:
            path_with_station[index] = point
            duration, profit = evaluate_path(path_with_station[1:], time_function)
            if duration > MAXIMUM_SORTIE_TIME[0]:
                continue
            if profit > best_replacement[3] or (profit==best_replacement[3] and duration<best_replacement[2]):
                best_replacement = (point, index, duration, profit)
        path_with_station[index] = old_point

    if best_replacement[0] is not None:
        point, index, duration, profit = best_replacement
        path_with_station[index] = point
        return path_with_station[1:], duration, profit
    return None, None, None


def local_search(path, from_neighbors, to_neighbors, time_function, current_cost, current_profit, double):
    improvements = [1, 1]
    while sum(improvements)>0:
        new_path, new_cost, new_profit = execute_3_opt(path, to_neighbors, time_function, current_cost, current_profit)
        if new_path is not None:
            path, current_cost, current_profit = new_path, new_cost, new_profit
            improvements[0] = 1
        else:
            improvements[0] = 0
            if improvements[1]==0:
                return path, current_cost, current_profit

        new_path, new_cost, new_profit = best_replace(path, from_neighbors, to_neighbors, time_function, double=double)
        if new_path is not None:
            path, current_cost, current_profit = new_path, new_cost, new_profit
            improvements[1] = 1

            path = insertion_global(path, from_neighbors, to_neighbors, time_function, "profit", None, reverse=None, double=double)
            current_cost, current_profit = evaluate_path(path, time_function)
        else:
            improvements[1] = 0

    return path, current_cost, current_profit


# Main algorithm

def LNS(station, time_function, double, temperature, n_non_imp_to_increase_beta, cooling, step_size, eta, max_nbrs, beta, beta_factor, max_beta,  n_non_imp_to_stop, max_iterations, dual=False):
    distance_limit = MAXIMUM_SORTIE_TIME[0] * DRONE_SPEED[0]
    if ELLIPSE_POINTS[0] is None:
        ELLIPSE_POINTS[0] = list(ellipse(list(MAP_APRIORI[0].keys()), station, station, distance_limit).keys())
    relevant_points = ELLIPSE_POINTS[0]
    solution_0 = cheapest_insertion(station, relevant_points, distance_limit)
    current_profit = evaluate_path(solution_0, time_function)[1]
    best_solution = (solution_0, current_profit)

    current_beta = beta
    count_no_imp_for_beta=0
    count_no_imp_for_stop=0
    count_steps = 0
    destroy_percentage_range = (0.01, 0.2)
    from_neighbors, to_neighbors = get_neighbors(solution_0, eta, current_beta, max_nbrs)

    destroy_list = ["worst cost", "worst cost seq", "random seq", "shaw", "rectangle", "worst profit", "cost efficiency", "cost efficiency seq"]
    insertion_list = ["profit", "cost efficiency", "order", "reverse order", "k regret"]
    insertion_inpath_list = ["profit", "cost efficiency"]
    to_stop = False

    # time1 = time.time()
    while not to_stop:
        for step in range(step_size):
            new_solution = copy.deepcopy(solution_0)

            # Deletion
            l0 = len(solution_0)
            q = int(get_random_from_range(destroy_percentage_range) * (len(solution_0) - 1))
            q = max(1, q)
            destroy_op_name = destroy_list[get_random_index(destroy_list)]
            destroy_op = destroy_dict[destroy_op_name]
            new_solution, deleted = destroy_op(new_solution, q, time_function)

            if len(new_solution)==0:
                raise ValueError(f"Empty path after {destroy_op_name}. Original length = {l0}; q = {q}.")

            # Insertion
            insertion_op_name = insertion_list[get_random_index(insertion_list)]

            # print("B", insertion_op_name)
            insertion_function = MAP_INSERTIONS[insertion_op_name]

            if insertion_op_name in insertion_inpath_list:
                insertion_heuristic_name = insertion_op_name
            else:
                insertion_heuristic_name = insertion_inpath_list[get_random_index(insertion_inpath_list)]
            reverse = True if insertion_op_name == "reverse order" else False

            new_solution = insertion_function(new_solution, from_neighbors, to_neighbors, time_function, insertion_heuristic_name, deleted, reverse=reverse, double=double)
            new_cost, new_profit = evaluate_path(new_solution, time_function)

            if new_cost>MAXIMUM_SORTIE_TIME[0]:
                raise ValueError("Invalid duration after insertion")

            Delta = new_profit - current_profit

            if station in new_solution[:-1]:
                raise ValueError("Station inside path (insertion)")

            # print("C")

            # Local search
            time_function_for_local_search = -2 if dual else time_function
            double_for_local_search = False if dual else double
            if new_profit > best_solution[1]:
                new_solution, new_cost, new_profit = local_search(new_solution, from_neighbors, to_neighbors, time_function_for_local_search, new_cost, new_profit, double=double_for_local_search)

            if new_cost>MAXIMUM_SORTIE_TIME[0]:
                raise ValueError("Invalid duration after local search")

            delta = get_random_float()
            if new_profit > current_profit or delta > math.e ** (Delta/temperature):
                solution_0 = new_solution
                current_profit = new_profit

            if station in new_solution[:-1]:
                raise ValueError("Station inside path (local search)")
            # print("D")

            if new_profit>best_solution[1]:
                best_solution = (new_solution, new_profit)
                # print("imp:", new_profit)
                if current_beta!=beta:
                    current_beta = beta
                    from_neighbors, to_neighbors = get_neighbors(solution_0, eta, current_beta, max_nbrs)
                count_no_imp_for_beta = 0
                count_no_imp_for_stop = 0
            else:
                count_no_imp_for_beta += 1
                count_no_imp_for_stop += 1

            if count_no_imp_for_beta >= n_non_imp_to_increase_beta and beta < max_beta:
                current_beta+=beta_factor
                from_neighbors, to_neighbors = get_neighbors(solution_0, eta, current_beta, max_nbrs)
                count_no_imp_for_beta = 0

            count_steps += 1

            if count_no_imp_for_stop >= n_non_imp_to_stop or count_steps >= max_iterations:
                to_stop = True
                break

        temperature *= cooling
        # print(count_steps, time.time() - time1)

    return best_solution[0]


def LNS_with_fine_tuning(station, time_function, double, temperature, n_non_imp_to_increase_beta, cooling, step_size, eta, max_nbrs, beta, beta_factor, max_beta, n_non_imp_to_stop, max_iterations, dual = None):
    if time_function!=-2 and CONSTANT_PATH[0] is not None:
        path = copy.deepcopy(CONSTANT_PATH[0])
    else:
        path = LNS(station, time_function=-2, double=False, temperature=temperature, n_non_imp_to_increase_beta=n_non_imp_to_increase_beta, cooling=cooling, step_size=step_size, eta=eta, max_nbrs=max_nbrs, beta=beta, beta_factor=beta_factor, max_beta=max_beta, n_non_imp_to_stop=n_non_imp_to_stop, max_iterations=max_iterations)
    if time_function!=-2 and CONSTANT_PATH[0] is None:
        CONSTANT_PATH[0] = copy.deepcopy(path)
    cost, profit = evaluate_path(path, time_function)
    from_neighbors, to_neighbors = get_neighbors(path, max_nbrs, max_beta, max_nbrs)
    path, _, _ = local_search(path, from_neighbors, to_neighbors, time_function, cost, profit, double=double)
    return path


def LNS_interface(start_point, station, time_function, arguments, double=True, final=True, aprior_planning=None, use_old_future=False, fine_tuning=False, dual=False):

    temperature = arguments["temperature"]
    cooling = arguments["cooling"]
    step_size = arguments["step_size"]
    n_non_imp_to_increase_beta = arguments["n_non_imp_to_increase_beta"]
    eta = arguments["eta"]
    max_nbrs = arguments["max_nbrs"]
    beta = arguments["beta"]
    beta_factor = arguments["beta_factor"]
    max_beta = arguments["max_beta"]
    n_non_imp_to_stop = arguments["n_non_imp_to_stop"]
    max_iterations = arguments["max_iterations"]

    if time_function==-2 and CONSTANT_PATH[0] is not None:
        return copy.deepcopy(CONSTANT_PATH[0])
    if time_function in [-1, -2]: double = False

    LNS_function = LNS_with_fine_tuning if fine_tuning else LNS
    path = LNS_function(station,time_function, double, temperature, n_non_imp_to_increase_beta, cooling, step_size, eta, max_nbrs, beta, beta_factor, max_beta, n_non_imp_to_stop, max_iterations, dual=dual)
    if time_function==-2 and CONSTANT_PATH[0] is None:
        CONSTANT_PATH[0] = copy.deepcopy(path)
    return path


def LNS_with_fine_tuning_interface(start_point, station, time_function, arguments, double=True, final=True, aprior_planning=None, use_old_future=False):
    return LNS_interface(start_point, station, time_function, arguments, double, final, aprior_planning=aprior_planning, use_old_future=use_old_future, fine_tuning=True)


def LNS_dual_interface(start_point, station, time_function, arguments, double=True, final=True, aprior_planning=None, use_old_future=False, fine_tuning=False):
    return LNS_interface(start_point, station, time_function, arguments, double=double, final=final, aprior_planning=aprior_planning, use_old_future=use_old_future, fine_tuning=fine_tuning, dual=True)

