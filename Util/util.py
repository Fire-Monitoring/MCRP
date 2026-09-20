from Util.time_functions import *
from Util.demo_sim import *
from Util.random_numbers import RANDOM_INDEX_FOR_FLOATS
import copy


def first_sig(number):
    i = 0
    for _ in range(20):
        if number>=1: return i
        number*=10
        i+=1
    return 20


def find_shortest_edge(relevant_points):
    shortest_edge = None
    for point_1 in relevant_points:
        for point_2 in relevant_points:
            if point_1 == point_2:
                continue
            distance = cartesian(point_1, point_2)
            if shortest_edge is None or distance < shortest_edge:
                shortest_edge = distance

    return shortest_edge


def stretch_path():
    pix_size = PIXEL_SIZE[0]
    for i in range(len(PATH)):
        y, x = PATH[i]
        new_loc = (y*pix_size+pix_size/2, x*pix_size+pix_size/2)
        PATH[i]=new_loc


def map_to_gains_and_distances(map):
    # map: 2d-array
    # return: gains, distances: dictionary of (int, int) --> float
    gains = dict()
    distances = dict()

    for i in range(map.shape[0]):
        for j in range(map.shape[1]):
            location = (i, j)
            gains[location] = map[i][j]

            distances_from_here = dict()
            for k in range(map.shape[0]):
                for h in range(map.shape[1]):
                    if k==i and h==j: # and (k,h)!=NORMALIZED_CHARGE_STATION[0]:
                        continue
                    dist = cartesian((i, j), (k, h))
                    distances_from_here[(k, h)] = dist
            distances[location] = distances_from_here

    return gains, distances


def risk_in_future_moment(current_risk, period, maximum, p_outbreak):
    return min(maximum, current_risk+period*p_outbreak)


def integral_uncertainty(p_current, p_outbreak, p_apriori, time):
    if time==-1:
        return p_current
    time_to_maximum = 0 if p_apriori==0 else (p_apriori - p_current) / p_outbreak
    t_increasing = min(time_to_maximum, time)
    future_p = p_current + t_increasing * p_outbreak
    uncertainty = integral_uncertainty_by_increasing_and_total(t_increasing, time, p_current, future_p)
    return uncertainty


def integral_gain_pixel(p_current, p_apriori, p_outbreak, time):
    return integral_uncertainty(p_current, p_outbreak, p_apriori, time) - integral_uncertainty(0, p_outbreak, p_apriori, time)


def integral_gain_pixel_simple(p_current, point, time):
    p_apriori = MAP_APRIORI[0][point]
    p_outbreak = MAP_OUTBREAK[0][point]
    return integral_gain_pixel(p_current, p_apriori, p_outbreak, time)


def maximum_integral_gain(p_apriori):
    time = P_APRIORI/P_OUTBREAK
    return time*p_apriori/2


def reset_paths():
    PATH_BY_ALGORITHM[0] = None
    STEP_INDEX[0] = 0
    N_NEXT[0] = None
    SUB_PATH_BY_ALGORITHM[0] = None
    REST_PATH[0] = None
    SUB_PATH_STEP_INDEX[0] = 0


def reset_globals():
    for g in [LOCATION, MAP_DYNAMIC, MAP_APRIORI, MAP_OUTBREAK, DISTANCES, SAVED_MAP, MAP_ORIG, PIXEL_WIDTH,
              FULL_PATH_TIME_WITH_CHARGING, AVERAGE_DISTANCE_FROM_STATION, RELATIVE_TIME_FROM_STATION,
              NORMALIZED_CHARGE_STATION, FUTURE, GREEDY_PATH_DURATION, TWO_MINS_HEURISTIC, LINEAR_MODEL_TYPE, CONVEXITY,
              ELLIPSE_POINTS, OLD_FUTURE_PATH, BEST_GUESS, MYLS_GRAPH, CONSTANT_PATH, NODES]:
        g[0] = None
    PIXEL_SIZE[0] = 1
    UNCERTAINTY[0] = 0
    TIME[0] = 0
    SORTIE_TIME[0] = 0
    OPTIMAL_INVALID[0] = 0
    PERIOD_PATH_INDEX[0] = 0
    PATH_INDEX[0] = 0
    PERIOD_NODE_IN_PATH_INDEX[0] = 0
    RANDOM_INDEX_FOR_FLOATS[0] = 0
    for pair in (MEMORY_SHORT, TREND_LINE):
        pair[0] = None
        pair[1] = None

    for l in [PATH, MEMORY_TIME, MEMORY_INTERVAL, MEMORY_ALL_INTERVALS, INTERVALS_LIST, DIST_LIST, APRIORI_VALUES_LIST, QUOTIENT_LIST, FULL_PERIOD, SAVED_PATHS]:
        l.clear()

    reset_paths()


def evaluate_path(path, time_function=None, start_point=None, return_only_time=False, print_times=False, map_dynamic=None, future_dict=None, start_time = None):
    if map_dynamic==None:
        map_dynamic = MAP_DYNAMIC[0]
    if start_point==None:
        start_point = LOCATION[0]
    if start_time==None:
        start_time=TIME[0]

    if len(path)>0 and type(path[0][0])==tuple:
        path = flat_path(path)
        map_dynamic = flat_dict(map_dynamic)
        if type(start_point[0])==tuple:
            start_point = start_point[0]

    time_list = path_times(path, start_point)

    if print_times:
        print("path:", path)
        print("time_list:", time_list)
        return

    if return_only_time:
        return time_list[-1]

    # check if memory is needed
    memory_map = None
    try:
        time_function(map_dynamic, path[0], None, future_moment=None, memory_map="_")
    except:
        memory_map = copy.deepcopy(MEMORY_TIME)

    if time_function in [time_by_future, time_absolute, time_free_constant, time_by_future_intervals, time_by_future_and_relative_default]:
        memory_map = future_dict
        STATISTIC_IN_DICT[0] = 0
        STATISTIC_OUT_DICT[0] = 0

    # estimate gain by demo simulation
    demo_map_dynamic = copy.deepcopy(map_dynamic)
    total_gain = 0
    for i in range(len(path)):
        location = path[i]
        current_risk = demo_map_dynamic[location]
        p_outbreak = MAP_OUTBREAK[0][location]
        maximum = MAP_APRIORI[0][location]
        time_to_future = time_list[i]    # the period from the start of the path to this point
        future_risk = risk_in_future_moment(current_risk, time_to_future, maximum, p_outbreak)

        path_after = path[i + 1:]
        if time_function==time_Nietzsche:
            period = time_function(map_dynamic, location, i, future_moment=start_time + time_to_future,
                                   memory_map=(path, time_list))
        elif location in path_after:
            next_visit_period = path_after.index(location)+i+1
            next_visit_time = time_list[next_visit_period]
            period = next_visit_time - time_to_future
            if time_function == None:  # case we count only the point profit from the visit (the risk we reduced to 0)
                future_future_risk_if_visit = risk_in_future_moment(0, period, maximum, p_outbreak)
                future_future_risk_if_not_visit = risk_in_future_moment(current_risk, next_visit_time, maximum, p_outbreak)
                offsetting_gain = future_future_risk_if_not_visit - future_future_risk_if_visit  # gain that is offset from the next visit
                current_gain_after_offsetting = future_risk - offsetting_gain
                total_gain+=current_gain_after_offsetting
                continue
            elif time_function in [-1, -2]:
                continue
        else:
            if time_function == None:
                total_gain += future_risk
                continue
            elif time_function == -1:
                total_gain += current_risk
                continue
            elif time_function == -2:
                total_gain += MAP_APRIORI[0][location]
                continue
            period = time_function(map_dynamic, location, None, future_moment=start_time + time_to_future, memory_map=memory_map)

        gain = integral_gain_pixel(future_risk, maximum, p_outbreak, period)
        total_gain+=gain
    return time_list[-1], total_gain


def evaluate_series_of_paths(paths, start_point, first_map, together=False):
    scores = []
    original_dynamic_map = copy.deepcopy(MAP_DYNAMIC[0])
    if together:
        MAP_DYNAMIC[0] = copy.deepcopy(MAP_APRIORI[0])
    else:
        MAP_DYNAMIC[0] = copy.deepcopy(first_map)
    time_function = time_functions_dict["future"]
    for i in range(len(paths)):
        path = paths[i]
        FUTURE[0] = create_future(paths[i+1:], start_point=start_point)
        score = evaluate_path(path, time_function=time_function, start_point = start_point)[1]
        scores.append(score)
        if together:
            MAP_DYNAMIC[0] = copy.deepcopy(MAP_APRIORI[0])
        else:
            MAP_DYNAMIC[0] = demo_simulation(MAP_DYNAMIC[0], path, in_place=True)
    MAP_DYNAMIC[0] = original_dynamic_map
    return scores


def validate_path(path, start_point=None, end_point=None, start_time=None, time_limit=None, allowed_replacement=False):
    if start_point is not None and type(start_point[0])==tuple:
        path = flat_path(path)
        start_point = start_point[0]
        end_point = end_point[0]

    if start_point==None:
        start_point=LOCATION[0]
    if end_point==None:
        end_point=NORMALIZED_CHARGE_STATION[0]
    if start_time==None:
        start_time=SORTIE_TIME[0]
    if time_limit==None:
        time_limit=MAXIMUM_SORTIE_TIME[0]

    path = [start_point] + path + [end_point]

    sub_path_start_index = 0
    time_since_starting_count_limit = start_time
    for i in range(len(path)):
        if (path[i]==end_point and allowed_replacement) or i==len(path)-1:
            sub_path = path[sub_path_start_index:i + 1]
            period = evaluate_path(sub_path, start_point=path[sub_path_start_index], return_only_time=True)
            period+=time_since_starting_count_limit
            if period>time_limit:
                return False
            sub_path_start_index = i
            time_since_starting_count_limit=0
    return True


def filter_dict(locations_dict, center_point, distance_limit):
    to_delete = []
    for point in locations_dict.keys():
        if point in [center_point]:
            continue
        distance = cartesian(center_point, point)
        if distance > distance_limit:
            to_delete.append(point)

    for point in to_delete:
        del locations_dict[point]


def insert_to_memory(location):
    # insert to intervals memory
    if location in MEMORY_TIME.keys():
        dist = cartesian(location, NORMALIZED_CHARGE_STATION[0])
        if location not in MEMORY_ALL_INTERVALS.keys():
            l = dist / AVERAGE_DISTANCE_FROM_STATION[0]
            MEMORY_ALL_INTERVALS[location] = (l, [])
        interval = TIME[0] - MEMORY_TIME[location]
        MEMORY_ALL_INTERVALS[location][1].append(interval)
        MEMORY_INTERVAL[location] = interval
        INTERVALS_LIST.append(interval)
        DIST_LIST.append(dist)
        APRIORI_VALUES_LIST.append(MAP_APRIORI[0][location])
        QUOTIENT_LIST.append(MAP_APRIORI[0][location] / dist)

        if len(INTERVALS_LIST) > INTERVAL_LIST_LENGTH:
            for global_list in [INTERVALS_LIST, DIST_LIST, APRIORI_VALUES_LIST, QUOTIENT_LIST]:
                del global_list[0]

    # insert to time memory
    # insert to memory with delay (of the previous visit)
    if MEMORY_SHORT[0] is not None and MEMORY_SHORT[0]!=NORMALIZED_CHARGE_STATION[0]:
        MEMORY_TIME[MEMORY_SHORT[0]] = MEMORY_SHORT[1]
    MEMORY_SHORT[0] = location
    MEMORY_SHORT[1] = TIME[0]


def find_opt_path(paths, time_function, start_point):
    opt_path = None
    for path in paths:
        score = evaluate_path(path, time_function, start_point)[1]
        if opt_path is None or opt_path[1] < score:
            opt_path = (path, score)
    return opt_path[0]


def convert_future(ar_dict, cd_dict, phase_index, path):
    future_type = FUTURE_AR_PROTOCOL[0][phase_index]
    time_function = ar_dict[future_type]
    if phase_index == 0: return time_function

    cd = cd_dict[future_type]
    if cd == "d" and PREV_AR[0]!=future_type:
        if future_type == "a":
            FUTURE[0] = future_relative_to_absolute(path)
        if future_type == "r":
            FUTURE_INTERVALS[0] = future_absolute_to_relative(path)

    PREV_AR[0] = future_type
    return time_function


def valid_place_and_time(point, start_point, time, time_limit):
    residual_time_limit = time_limit-time
    time_distance = cartesian(point, start_point) / DRONE_SPEED[0]
    return time_distance<=min(time, residual_time_limit)


def valid_place(point, start_point, time_limit):
    time_distance = cartesian(point, start_point) / DRONE_SPEED[0]
    return time_distance*2 <= time_limit


def calc_profit(point, visit_time, time_function, map_dynamic=None, memory_map = None, future_risk=None, to_print=False):
    if map_dynamic==None:
        map_dynamic=MAP_DYNAMIC[0]

    if time_function==-1:
        return map_dynamic[point]
    if time_function==-2:
        return MAP_APRIORI[0][point]

    maximum = MAP_APRIORI[0][point]
    p_outbreak = MAP_OUTBREAK[0][point]
    if future_risk==None:
        current_risk = map_dynamic[point]
        future_risk = risk_in_future_moment(current_risk, visit_time, maximum, p_outbreak)

    if time_function is None:
        return future_risk

    dummy = len(memory_map[0])-1 if time_function==time_Nietzsche else None
    period = time_function(map_dynamic, point, dummy=dummy, future_moment=TIME[0] + visit_time,
                           memory_map=memory_map)

    gain = integral_gain_pixel(future_risk, maximum, p_outbreak, period)
    if to_print:
        print("\t", period)

    return gain


def calc_discreet_past_nietzsche_path_profit(path, time_list, time_function):
    late_time_list = [t + MAXIMUM_SORTIE_TIME[0] for t in time_list]
    long_time_list = time_list + late_time_list
    long_path = path+path

    total_profit = 0
    path_len = len(path)
    for i in range(path_len, 2*path_len):
        point = long_path[i]
        prev_visit_time = None
        for j in range(1, i):
            if long_path[i-j]==point:
                prev_visit_time = long_path[i-j]
                break
        period = long_time_list[i]-prev_visit_time

        p_outbreak = MAP_OUTBREAK[0][point]
        maximum = MAP_APRIORI[0][point]
        future_risk = risk_in_future_moment(0, period, maximum, p_outbreak)
        value = calc_profit(point, i-path_len, time_function, future_risk=future_risk)

        total_profit += value

    return total_profit


def ellipse(locations_list, start_point, end_point, distance_limit):
    points_inside_ellipse = {}
    for point in locations_list:
        if point in [start_point, end_point]:
            continue
        distance = cartesian(start_point, point) + cartesian(point, end_point)
        if distance <= distance_limit:
            points_inside_ellipse[point] = distance
    return points_inside_ellipse


def get_rectangle_points(points, center, radius):
    low_1, high_1 = center[0]-radius, center[0]+radius
    low_2, high_2 = center[1]-radius, center[1]+radius

    points_in_rectangle = []
    for i in range(len(points)):
        point = points[i]
        if point[0] >= low_1 and point[0] <= high_1 and point[1] >= low_2 and point[1] <= high_2:
            points_in_rectangle.append(i)

    return points_in_rectangle