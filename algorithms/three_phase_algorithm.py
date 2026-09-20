import copy
import time

from Util.util import *

def trapeze_area(risk, duration, time_to_max_risk = None):
    if time_to_max_risk==None:
        time_to_max_risk = TIME_TO_MAX_RISK
    big_triangle_area = risk * time_to_max_risk / 2
    if duration>=time_to_max_risk:
        return big_triangle_area
    small_big_length_proportion = (time_to_max_risk - duration) / time_to_max_risk
    small_triangle_area = big_triangle_area * small_big_length_proportion**2
    return big_triangle_area - small_triangle_area


def future_risk(point, future_sortie_time):
    return min(MAP_DYNAMIC[0][point] + future_sortie_time * MAP_OUTBREAK[0][point], MAP_APRIORI[0][point])


def future_integral(point, future_sortie_time, duration):
    risk = MAP_APRIORI[0][point]
    future_risk_value = future_risk(point, future_sortie_time)
    delta_risk_in_future = risk - future_risk_value
    offset_time_to_max_risk = TIME_TO_MAX_RISK * delta_risk_in_future / risk
    offset = trapeze_area(delta_risk_in_future, duration, time_to_max_risk = offset_time_to_max_risk)
    entire_area = trapeze_area(risk, duration)
    return entire_area - offset


def optimal_insertion_specific_point_by_cost(start_point, path, point, open_path_flag):
    optimal_insertion = (-1, -1)  # index, cost
    complete_path = [start_point] + path
    for i in range(len(complete_path)-1 + int(open_path_flag)):  # if the path is open, then the new point can be at the end
        cost = cartesian(complete_path[i], point) + cartesian(point, complete_path[i+1]) - cartesian(complete_path[i], complete_path[i+1])
        if optimal_insertion[0]==-1 or cost<optimal_insertion[1]:
            optimal_insertion = (i, cost)
    return optimal_insertion  # i, delta cost


def gain_2_next_points(point1, point2, temp_location, temp_time, time_function, path_with_start=None):
    travel_time1 = cartesian(temp_location, point1) / DRONE_SPEED[0]
    arrival_time1 = temp_time + travel_time1
    travel_time2 = cartesian(point1, point2) / DRONE_SPEED[0]
    arrival_time2 = arrival_time1 + travel_time2

    if time_function==-1:
        return (MAP_DYNAMIC[0][point1] + MAP_DYNAMIC[0][point2]) / (travel_time1 + travel_time2)
    if time_function==-2:
        return (MAP_APRIORI[0][point1] + MAP_APRIORI[0][point2]) / (travel_time1 + travel_time2)
    if time_function==time_Nietzsche:
        index2 = len(path_with_start)
        index1 = index2 - 1
        path_with_start = path_with_start + [point1, point2]
        time_list = path_times(path_with_start[1:], path_with_start[0])
        pair_for_nietzsche = (path_with_start[1:], time_list)
    else:
        pair_for_nietzsche = None
        index2 = None
        index1 = None

    future_risk1 = future_risk(point1, arrival_time1)
    future_risk2 = future_risk(point2, arrival_time2)

    if time_function is None:
        gain1 = future_risk1
        gain2 = future_risk2
    else:
        interval1 = time_function(MAP_DYNAMIC[0], point1, index1, future_moment=arrival_time1, memory_map=pair_for_nietzsche)
        gain1 = integral_gain_pixel_simple(future_risk1, point1, interval1)
        interval2 = time_function(MAP_DYNAMIC[0], point2, index2, future_moment=arrival_time2, memory_map=pair_for_nietzsche)
        gain2 = integral_gain_pixel_simple(future_risk2, point2, interval2)
    return (gain1 + gain2) / (travel_time1 + travel_time2)


def gain_of_point_by_opt_next(point, temp_location, points_list, temp_time, time_function, path_with_start=None):
    best_score = 0
    for point_next in points_list:
        if point_next==point:
            continue

        gain = gain_2_next_points(point, point_next, temp_location, temp_time, time_function, path_with_start=path_with_start)
        best_score = max(best_score, gain)
    return best_score


def valid_point(point, temp_location, temp_time, start_point, time_limit):
    travel_time = (cartesian(temp_location, point) + cartesian(point, start_point)) / DRONE_SPEED[0]
    return temp_time + travel_time <= time_limit


def initialize_ez(locations_list, start_point, time_limit, time_function, force_points=[], ellipse_points=None):


    if ellipse_points is None:
        if ELLIPSE_POINTS[0] is not None:
            ellipse_points = ELLIPSE_POINTS[0]
        else:
            distance_limit = time_limit * DRONE_SPEED[0]
            ellipse_points_dict = ellipse(locations_list, start_point, start_point, distance_limit)
            ellipse_points = list(ellipse_points_dict.keys())
    points = copy.deepcopy(ellipse_points)

    temp_time = 0
    temp_location = start_point
    path = []

    for point in force_points:
        path.append(point)
        temp_time += cartesian(temp_location, point) / DRONE_SPEED[0]
        points.remove(point)
        temp_location = point
    if len(force_points)>0:
        points_to_remove = []
        for point in points:
            if not valid_point(point, temp_location, temp_time, start_point, time_limit):
                points_to_remove.append(point)
        points = [point for point in points if point not in points_to_remove]

    while len(points)>0:
        opt_next_point = None
        for point in points:
            path_with_start = [start_point]+path if time_function==time_Nietzsche else None
            score_value = gain_of_point_by_opt_next(point, temp_location, points, temp_time, time_function, path_with_start=path_with_start)
            if opt_next_point is None or score_value>opt_next_point[1]:
                opt_next_point = (point, score_value)

        if opt_next_point is not None:
            next_point = opt_next_point[0]
            # print(opt_next_point)
            path.append(next_point)

            points.remove(next_point)
            temp_time += cartesian(temp_location, next_point)/DRONE_SPEED[0]
            temp_location = next_point

        points_to_remove = []
        for point in points:
            if not valid_point(point, temp_location, temp_time, start_point, time_limit):
                points_to_remove.append(point)
        points = [point for point in points if point not in points_to_remove]

    path.append(start_point)
    # print(path)
    return path, ellipse_points


def greedy_insertion(path, points_list, start_point, time_limit):
    while True>0:
        optimal_insertion = (None, -1, -1)  # point, index, cost
        for j in range(len(points_list)):  # find the lowest-cost insertion
            point = points_list[j]
            if point in path:
                continue
            index, cost = optimal_insertion_specific_point_by_cost(start_point, path, point, False)
            if optimal_insertion[0] == None or cost < optimal_insertion[2]:
                optimal_insertion = (point, index, cost)

        point, index, cost = optimal_insertion
        if point == None:
            break
        potential_path = path[:index] + [point] + path[index:]
        valid_path = validate_path(potential_path, start_point, start_point, 0, time_limit)
        if valid_path:
            path = potential_path
        else:
            break

    return path


def reorder_path(path, ellipse_points, start_point, time_limit):
    path = path[:-1]
    furthest_point = (-1, -1)
    for point in path:
        dist = cartesian(point, start_point)
        if dist > furthest_point[1]:
            furthest_point = (point, dist)
    new_path = [furthest_point[0]]
    path.remove(furthest_point[0])
    new_path = greedy_insertion(new_path, path, start_point, time_limit)
    # new_path = greedy_insertion(new_path, ellipse_points, start_point, time_limit)
    new_path.append(start_point)
    return new_path


def optimal_insertion_point_for_ez(start_point, path, point, orig_gain, orig_cost, time_limit, time_function):
    if orig_cost==0:
        return 0
    time_gain = orig_gain / orig_cost
    optimal_insertion = (-1, -1)  # index, gain
    for i in range(len(path)):
        if point in [path[i-1], path[i]]:
            continue
        potential_path = path[:i] + [point] + path[i:]
        valid = path_times(potential_path, start_point)[-1]<=time_limit
        if not valid:
            continue
        new_cost, new_gain = evaluate_path(potential_path, time_function, start_point)
        delta_gain = new_gain-orig_gain - (new_cost - orig_cost)*time_gain
        if optimal_insertion[0]==-1 or delta_gain>optimal_insertion[1]:
            optimal_insertion = (i, delta_gain)

    return optimal_insertion  # i, delta gain


def insertion_improve_ez_path(path, ellipse_points, start_point, time_limit, time_function, double=False):
    current_cost, current_gain = evaluate_path(path, time_function, start_point)
    no_change = False
    while not no_change:
        no_change=True
        optimal_point = (-1, -1, -1)  # point, index, delta gain
        for point in ellipse_points:
            if point in path and not double:
                continue
            i, delta_gain = optimal_insertion_point_for_ez(start_point, path, point, current_gain, current_cost, time_limit, time_function)
            if delta_gain>0 and delta_gain>optimal_point[2]:
                optimal_point = (point, i, delta_gain)
        if optimal_point[0]!=-1:
            point, i, delta_gain = optimal_point
            path = path[:i] + [point] + path[i:]
            current_cost, current_gain = evaluate_path(path, time_function, start_point)
            no_change = False
    return path


def two_op_and_insert_improve_ez_path(path, ellipse_points, start_point, time_limit, time_function, double=False, paths=[]):
    path = two_op_improvement_ez(path, start_point, time_limit, time_function, consider_cost=True, paths=paths)
    paths.append(path)
    path = insertion_improve_ez_path(path, ellipse_points, start_point, time_limit, time_function, double)
    return path


def two_op_improvement_ez(path, start_point, time_limit, time_function, consider_cost=False, paths=[]):
    entire_path = [start_point] + path
    current_cost, current_gain = evaluate_path(path, time_function, start_point)
    cost_factor = current_gain/current_cost
    current_score = 0 if consider_cost else current_gain
    global_no_improvement = True
    best_reverse = None
    no_improvement = False

    while no_improvement==False:
        no_improvement=True
        for i in range(len(entire_path)-3):
            for j in range(i+2, len(entire_path)-1):
                potential_path = reverse_sub_path(entire_path, i+1, j)
                if potential_path in paths:
                    continue
                valid = validate_path(potential_path, start_point, start_point, time_limit=time_limit)
                if not valid:
                        continue
                new_cost, new_gain = evaluate_path(potential_path, time_function, start_point)
                new_score = new_gain - cost_factor * new_cost if consider_cost else new_gain
                if best_reverse is None or best_reverse[0] < new_score:
                    best_reverse = [new_score, i, j]
                if new_score > current_score:
                        entire_path = potential_path
                        current_score = new_score
                        no_improvement=False
                        global_no_improvement = False
                        break
            if no_improvement==False:
                break

    if global_no_improvement and len(paths)>1 and best_reverse is not None:
        i, j = best_reverse[1], best_reverse[2]
        entire_path = reverse_sub_path(entire_path, i+1, j)

    return entire_path[1:]


PATH_NUM = [0]
def EZ(start_point, time_function, time_limit, n_improves=1, double=False, return_mid=False, f_time_select=-1):
    mid_paths = []

    # step 1
    locations_list = list(MAP_APRIORI[0].keys())
    time_function_for_step_1 = time_function if AGGRESSIVE_MULTY_PATH[0] else None
    path, ellipse_points = initialize_ez(locations_list, start_point, time_limit, time_function_for_step_1)
    ELLIPSE_POINTS[0] = ellipse_points

    mid_paths.append(path)

    # step 2
    paths=[path]
    for _ in range(n_improves):
            path = two_op_and_insert_improve_ez_path(path, ellipse_points, start_point, time_limit,
                                                         time_function, double, paths)
            paths.append(path)

    # step 3
    for i in range(len(paths)):
        paths[i] = two_op_improvement_ez(paths[i], start_point, time_limit, time_function)
    mid_paths.append(paths[0])

    # selection
    path = find_opt_path(paths, time_function, start_point)

    if return_mid:
        return path, mid_paths
    return path


def EZ_interface(start_point, station, time_function, arguments, time_limit=None, time_limit_for_open_path=None, double=None, return_mid=False, final=False, aprior_planning=None, use_old_future=False):
    if time_function==-2 and CONSTANT_PATH[0] is not None:
        return copy.deepcopy(CONSTANT_PATH[0])
    if time_function in [-1, -2]: double = None
    # single_time_value: number or "avrg memory"
    n_improves, n_tails, decision_protocol = arguments
    # if final: n_improves = n_tails
    # f_time_improve = None if decision_protocol[0]=="n" else time_function
    # f_time_select = None if decision_protocol[1]=="n" else time_function
    n_improves = n_tails

    time_limit = MAXIMUM_SORTIE_TIME[0] if time_limit is None else time_limit
    double = double is not None
    path = EZ(start_point, time_function, time_limit, n_improves=n_improves, double=double, return_mid=return_mid)

    if USE_BEST_GUESS[0]:
        _, score = evaluate_path(path, time_function)
        if BEST_GUESS[0] is not None:
            _, old_score = evaluate_path(BEST_GUESS[0], time_function)
        if BEST_GUESS[0] is None or score > old_score:
            BEST_GUESS[0] = path

    if time_function==-2 and CONSTANT_PATH[0] is None:
        CONSTANT_PATH[0] = copy.deepcopy(path)

    return path