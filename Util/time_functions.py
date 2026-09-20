from Util.demo_sim import *


def calculate_avrg_dist_from_station_and_relative_time(map_dynamic):
    if AVERAGE_DISTANCE_FROM_STATION[0] is not None and RELATIVE_TIME_FROM_STATION[0] is not None:
        return
    total_time_from_station = 0
    count_close = 0
    for l in map_dynamic.keys():
        distance_from_station = cartesian(l, NORMALIZED_CHARGE_STATION[0])
        time_from_station = distance_from_station/DRONE_SPEED[0]
        if time_from_station<=MAXIMUM_SORTIE_TIME[0]/2:
            total_time_from_station+=time_from_station
            count_close+=1
    average_time_from_station = total_time_from_station / count_close
    AVERAGE_DISTANCE_FROM_STATION[0] = average_time_from_station * DRONE_SPEED[0]
    RELATIVE_TIME_FROM_STATION[0] = average_time_from_station * 2 / MAXIMUM_SORTIE_TIME[0]


def full_path_time_length(map_dynamic, with_revision=True):
    height = max([l[0] for l in map_dynamic.keys()]) + 1
    width = max([l[1] for l in map_dynamic.keys()]) + 1
    long_d = max(height, width)
    short_d = min(height, width)

    path_len = long_d * short_d * PIXEL_WIDTH[0] + short_d * PIXEL_WIDTH[0]
    revision_len = short_d * PIXEL_WIDTH[0] if short_d%2==0 else PIXEL_WIDTH[0] * (long_d**2 + short_d**2)**0.5
    return (path_len + revision_len * int(with_revision))/DRONE_SPEED[0]


def full_path_time_with_charging(map_dynamic, factor=0):
    if FULL_PATH_TIME_WITH_CHARGING[0] is not None:
        return FULL_PATH_TIME_WITH_CHARGING[0]

    total_time_from_station = 0
    count_close = 0
    for l in map_dynamic.keys():
        distance_from_station = cartesian(l, NORMALIZED_CHARGE_STATION[0])
        time_from_station = distance_from_station/DRONE_SPEED[0]
        if time_from_station<=MAXIMUM_SORTIE_TIME[0]/2:
            total_time_from_station+=time_from_station
            count_close+=1
    average_time_from_station = total_time_from_station / count_close
    AVERAGE_DISTANCE_FROM_STATION[0] = average_time_from_station * DRONE_SPEED[0]

    t_rotation = full_path_time_length(map_dynamic, with_revision=False)
    sortie_duration = MAXIMUM_SORTIE_TIME[0]-0*average_time_from_station
    n_sorties = t_rotation/sortie_duration
    total_duration = t_rotation + factor*n_sorties*average_time_from_station
    RELATIVE_TIME_FROM_STATION[0] = average_time_from_station * 2 / MAXIMUM_SORTIE_TIME[0]

    FULL_PATH_TIME_WITH_CHARGING[0] = total_duration

    return total_duration


def linear_regression_time_function(location, x_type):
    # x_type = "dist" or "value" or "quotient"
    if TREND_LINE[0]==None:
        return time_pseudo_static()
    if x_type not in ["dist", "value", "quotient"]: return None
    dist = cartesian(location, NORMALIZED_CHARGE_STATION[0])
    value = MAP_APRIORI[0][location]
    if x_type=="dist":
        x = dist
    elif x_type=="value":
        x = value
    else:
        x = value / dist if dist > 0 else 0

    slope, intercept = TREND_LINE
    convexity = CONVEXITY[0]
    return convexity * (x ** 2) + slope * x + intercept


def future_absolute_to_relative(ref_path = [NORMALIZED_CHARGE_STATION[0]], future=None, n_next_sorties = 1):
    if future is None:
        future = FUTURE[0]

    start_point = NORMALIZED_CHARGE_STATION[0]

    all_points = list(MAP_DYNAMIC[0].keys())
    relative_future = dict()
    path_schedule = create_future([ref_path], start_point=None)
    for point in all_points:
        if point==start_point:
            continue

        if point in ref_path:
            early_visit = path_schedule[point]
        elif point in MEMORY_TIME.keys():
            early_visit = MEMORY_TIME[point] - TIME[0]
        else:
            early_visit = -TIME_TO_MAX_RISK

        if point in future.keys():
            next_visit = future[point] + MAXIMUM_SORTIE_TIME[0]
        else:
            next_visit = MAXIMUM_SORTIE_TIME[0] * (n_next_sorties + 1)

        future_interval = next_visit-early_visit
        relative_future[point] = future_interval
    return relative_future


def future_relative_to_absolute(ref_path=[NORMALIZED_CHARGE_STATION[0]], relative_future=None, n_next_sorties=1):
    if relative_future is None:
        relative_future = FUTURE_INTERVALS[0]

    start_point = NORMALIZED_CHARGE_STATION[0]

    all_points = list(MAP_DYNAMIC[0].keys())
    absolute_future = dict()
    path_schedule = create_future([ref_path], start_point=None)
    for point in all_points:
        if point == start_point or point not in relative_future.keys():
            continue

        if point in ref_path:
            early_visit = path_schedule[point]
        elif point in MEMORY_TIME.keys():
            early_visit = MEMORY_TIME[point] - TIME[0]
        else:
            early_visit = -TIME_TO_MAX_RISK

        interval_visit = relative_future[point]

        future_visit = early_visit + interval_visit
        if future_visit < MAXIMUM_SORTIE_TIME[0]:
            future_visit = MAXIMUM_SORTIE_TIME[0]
            if interval_visit>=TIME_TO_MAX_RISK:
                future_visit+=TIME_TO_MAX_RISK

        future_visit-=MAXIMUM_SORTIE_TIME[0]
        absolute_future[point] = future_visit
    default = FUTURE[0]["default"] if len(FUTURE)>0 else (n_next_sorties + 1)*MAXIMUM_SORTIE_TIME[0]
    absolute_future["default"] = default
    return absolute_future


# time functions: estimate the time that will pass until the next visit to a certain point:

def time_norm_constant_full_path(map_dynamic, location, dummy2, future_moment=None, memory_map=None):
    full_path_time = full_path_time_with_charging(map_dynamic)
    ratio = cartesian(location, NORMALIZED_CHARGE_STATION[0]) / AVERAGE_DISTANCE_FROM_STATION[0]
    p = RELATIVE_TIME_FROM_STATION[0]
    factor = 1-p + p*ratio
    return full_path_time * factor


def time_norm_constant_full_path_softer_norm(map_dynamic, location, dummy2, future_moment=None, memory_map=None):
    full_path_time = full_path_time_with_charging(map_dynamic)
    ratio = cartesian(location, NORMALIZED_CHARGE_STATION[0]) / AVERAGE_DISTANCE_FROM_STATION[0]
    p = RELATIVE_TIME_FROM_STATION[0]
    p_half = p/2
    factor = 1-p_half + p_half*ratio
    return full_path_time * factor


def time_norm_constant_full_path_one_dir(map_dynamic, location, dummy2, future_moment=None, memory_map=None):
    full_path_time = full_path_time_with_charging(map_dynamic, factor=1)
    ratio = cartesian(location, NORMALIZED_CHARGE_STATION[0]) / AVERAGE_DISTANCE_FROM_STATION[0]
    p = RELATIVE_TIME_FROM_STATION[0]
    factor = 1-p + p*ratio
    return full_path_time * factor


def time_norm_constant_full_path_softer_norm_one_dir(map_dynamic, location, dummy2, future_moment=None, memory_map=None):
    full_path_time = full_path_time_with_charging(map_dynamic, 1)
    ratio = cartesian(location, NORMALIZED_CHARGE_STATION[0]) / AVERAGE_DISTANCE_FROM_STATION[0]
    p = RELATIVE_TIME_FROM_STATION[0]
    p_half = p/2
    factor = 1-p_half + p_half*ratio
    return full_path_time * factor


def time_constant(map_dynamic, location, dummy2, future_moment=None, memory_map=None):
    return full_path_time_length(map_dynamic, with_revision=False)


def time_memory_interval(map_dynamic, location, dummy=None, future_moment=None, memory_map=None):
    if location in MEMORY_INTERVAL:
        return MEMORY_INTERVAL[location]
    return TIME_TO_MAX_RISK
    # return sum([interval[0] for interval in MEMORY_INTERVAL.values()]) / len(MEMORY_INTERVAL)


def time_average_memory_interval(map_dynamic, location, dummy=None, future_moment=None, memory_map=None):
    calculate_avrg_dist_from_station_and_relative_time(map_dynamic)
    if len(MEMORY_INTERVAL)==0:
        return -1
    avrg_interval = sum([interval for interval in MEMORY_INTERVAL.values()]) / len(MEMORY_INTERVAL)
    return avrg_interval


def time_pseudo_static(map_dynamic=None, location=None, dummy=None, future_moment=None, memory_map=None):
    return -1


def time_combined_memory_interval(map_dynamic, location, dummy=None, future_moment=None, memory_map=None):
    if len(MEMORY_INTERVAL)/len(MAP_DYNAMIC[0]) > P_FOR_COMBINED:
        return time_memory_interval(map_dynamic, location)
    else:
        return time_pseudo_static()


def time_combined_avrg_memory_interval(map_dynamic, location, dummy=None, future_moment=None, memory_map=None):
    if len(MEMORY_INTERVAL)/len(MAP_DYNAMIC[0]) > P_FOR_COMBINED:
        return time_average_memory_interval(map_dynamic, location)
    else:
        return time_pseudo_static()


def time_combined_interval_list(map_dynamic, location, dummy=None, future_moment=None, memory_map=None):
    if len(INTERVALS_LIST)==INTERVAL_LIST_LENGTH:
        return sum(INTERVALS_LIST)/INTERVAL_LIST_LENGTH
    else:
        return time_pseudo_static()


def time_memory(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    visit_time = future_moment if future_moment is not None else TIME[0]
    if memory_map==None:
        memory_map = MEMORY_TIME
    if location in memory_map.keys():
        return visit_time - memory_map[location]
    if len(memory_map)==0:
        return full_path_time_with_charging(map_dynamic)
    return visit_time - sum([time for time in memory_map.values()]) / len(memory_map)


def time_const_sortie(map_dynamic, location, dummy=None, future_moment=None, memory_map=None):
    return MAXIMUM_SORTIE_TIME[0]


def time_norm_const_or_sortie(map_dynamic, location, dummy=None, future_moment=None, memory_map=None):
    const_sortie = time_const_sortie(map_dynamic, location)
    norm_const = time_norm_constant_full_path(map_dynamic, location, None)
    return max(const_sortie, norm_const)


def time_2_mins(map_dynamic, location, dummy=None, future_moment=None, memory_map=None):
    if TWO_MINS_HEURISTIC[0] is not None:
        return TWO_MINS_HEURISTIC[0]

    relevant_points = get_relevant_points()
    t_total = 0
    for location_1 in relevant_points:
        distances = []
        for location_2 in relevant_points:
            if location_1==location_2:
                continue
            d = cartesian(location_1, location_2)
            distances.append(d)
        two_mins = min_k(distances, 2)
        two_mins_sum = sum(two_mins)
        time_two_mins = two_mins_sum/DRONE_SPEED[0]
        t_total+=time_two_mins

    TWO_MINS_HEURISTIC[0] = t_total/2
    return TWO_MINS_HEURISTIC[0]


STATISTIC_IN_DICT = [0]
STATISTIC_OUT_DICT = [0]
def time_by_future(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    if memory_map==None:
        future = FUTURE[0]
    else:
        future = memory_map
    visit_time = future_moment if future_moment is not None else TIME[0]
    visit_time_inside_sortie = visit_time % MAXIMUM_SORTIE_TIME[0]
    time_to_end_of_sortie = MAXIMUM_SORTIE_TIME[0] - visit_time_inside_sortie

    if location in future:
        future_visit = future[location]
        STATISTIC_IN_DICT[0]+=1
    else:
        future_visit = future["default"]
        STATISTIC_OUT_DICT[0]+=1

    return time_to_end_of_sortie + future_visit


def time_by_future_and_relative_default(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    if memory_map==None:
        future = FUTURE[0]
    else:
        future = memory_map
    visit_time = future_moment if future_moment is not None else TIME[0]
    visit_time_inside_sortie = visit_time % MAXIMUM_SORTIE_TIME[0]
    time_to_end_of_sortie = MAXIMUM_SORTIE_TIME[0] - visit_time_inside_sortie

    if location not in future:
        return MAXIMUM_SORTIE_TIME[0] + future["default"]

    return time_to_end_of_sortie + future[location]


def time_by_future_intervals(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    if memory_map==None:
        future_intervals = FUTURE_INTERVALS[0]
    else:
        future_intervals = memory_map
    if location in future_intervals.keys():
        return future_intervals[location]
    return future_intervals["default"]


def time_greedy_path(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    if GREEDY_PATH_DURATION[0]==None:
        path = improved_greedy_path()
        greedy_duration = path_times(path, path[0])[-1]
        GREEDY_PATH_DURATION[0]=greedy_duration

    return GREEDY_PATH_DURATION[0]


def time_lr_dist(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    LINEAR_MODEL_TYPE[0] = "dist"
    return linear_regression_time_function(location, "dist")


def time_lr_val(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    LINEAR_MODEL_TYPE[0] = "value"
    return linear_regression_time_function(location, "value")


def time_lr_comb(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    LINEAR_MODEL_TYPE[0] = "comb"
    if type(TREND_LINE[0])!=list and TREND_LINE[0]==None:
        return time_pseudo_static()
    coefficients, intercept = TREND_LINE
    coef_x1, coef_x2, coef_x1x1, coef_x2x2, coef_x1x2 = coefficients
    dist = cartesian(location, NORMALIZED_CHARGE_STATION[0])
    value = MAP_APRIORI[0][location]
    return coef_x1*dist + coef_x2*value + coef_x1x1*dist*dist + coef_x2x2*value*value + coef_x1x2*dist*value + intercept


def time_free_constant(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    # memory_map is a number; represents the value
    return memory_map


def time_absolute(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    # memory_map is a number; represents future end\visit
    return memory_map - future_moment


def time_Nietzsche(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    path, time_list = memory_map
    index = dummy

    if time_list==None:
        start_point = LOCATION[0]
        time_list = path_times(path, start_point)

    path_after = path[index+1:]
    if location in path_after:
        next_visit_index = path_after.index(location) + index + 1
        period = time_list[next_visit_index] - time_list[index]
    else:
        next_visit_index = path.index(location)
        period = time_list[next_visit_index] + MAXIMUM_SORTIE_TIME[0] - time_list[index]

    return period


def time_max(map_dynamic, location, dummy, future_moment=None, memory_map=None):
    return TIME_TO_MAX_RISK


time_functions_dict = {"norm constant": time_norm_constant_full_path,
                       "norm constant sn": time_norm_constant_full_path_softer_norm,
                       "norm constant od": time_norm_constant_full_path_one_dir,
                       "norm constant sn od": time_norm_constant_full_path_softer_norm_one_dir,
                       "constant sortie": time_const_sortie,
                       "norm constant or sortie": time_norm_const_or_sortie,
                       "constant": time_constant,
                       "memory": time_memory,
                       "pseudo static": time_pseudo_static,
                       "memory interval": time_memory_interval,
                       "comb memory interval": time_combined_memory_interval,
                       "comb avrg memory interval": time_combined_avrg_memory_interval,
                       "future": time_by_future,
                       "future intervals": time_by_future_intervals,
                       "future relative default": time_by_future_and_relative_default,
                       "greedy constant": time_greedy_path,
                       "comb interval list": time_combined_interval_list,
                       "2 mins": time_2_mins,
                       "lr dist": time_lr_dist,
                       "lr val": time_lr_val,
                       "lr comb": time_lr_comb,
                       "absolute": time_absolute,
                       "free constant": time_free_constant,
                       None: None,
                       "nietzsche": time_Nietzsche,
                       "max": time_max,
                       "step": -1,
                       "static": -2}