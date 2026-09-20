from Util.basic_functions import *


def demo_simulation(orig_map_dynamic, path, total_time=None, in_place=False, start_point=None):
    if type(list(orig_map_dynamic.keys())[0][0])==tuple:
        map_dynamic, k = flat_dict(orig_map_dynamic, return_k=True)
        path = flat_path(path)
        map_is_doubled = True
        if type(start_point)==tuple and type(start_point[0])==tuple:
            start_point = start_point[0]
        # print("if -", list(orig_map_dynamic.keys())[0])
    else:
        map_dynamic = orig_map_dynamic
        map_is_doubled = False
        # print("else -", list(orig_map_dynamic.keys())[0])

    if not in_place:
        map_dynamic = copy.deepcopy(map_dynamic)
    if total_time==None:
        total_time = MAXIMUM_SORTIE_TIME[0]
    if path==None:
        time_over_map(total_time, map_dynamic=map_dynamic)
        return map_dynamic
    deltas = create_future([path], start_point, return_deltas = True)
    for i in range(len(path)):
        time_over_map(deltas[i], map_dynamic=map_dynamic)
        map_dynamic[path[i]] = 0
    time_over_map(total_time-sum(deltas), map_dynamic=map_dynamic)

    if map_is_doubled:
        dict_to_put_into = orig_map_dynamic if in_place else None
        map_dynamic = double_dict(map_dynamic, k, dict_to_put_into)

    return map_dynamic


def create_future(paths, start_point=None, return_deltas = False):
    if len(paths)>0 and len(paths[0])>0 and type(paths[0][0][0])==tuple:
        paths = flat_path(paths)
    if start_point is not None and type(start_point[0]) == tuple:
        start_point = start_point[0]

    if start_point == None:
        start_point = LOCATION[0]

    future = dict()
    deltas_list = []
    previous_location = start_point
    remember_for_delta = 0
    # print(path)
    n_paths = len(paths)
    for i in range(n_paths):
        path = paths[i]
        temp_time = i * MAXIMUM_SORTIE_TIME[0]
        for next_location in path:
            distance = cartesian(previous_location, next_location)
            delta_time = distance / DRONE_SPEED[0]
            temp_time += delta_time
            deltas_list.append(delta_time+remember_for_delta)
            remember_for_delta=0
            if next_location not in future.keys():
                future[next_location] = temp_time
            previous_location = next_location
        remember_for_delta = MAXIMUM_SORTIE_TIME[0] - (temp_time%MAXIMUM_SORTIE_TIME[0])
        # print("remember_for_delta:", remember_for_delta)

    future["default"] = n_paths*MAXIMUM_SORTIE_TIME[0]  # TIME_TO_MAX_RISK

    if return_deltas:
        return deltas_list
    return future


def create_future_intervals(first_path, paths, start_point=None, return_deltas = False):
    if start_point == None:
        start_point = LOCATION[0]

    first_path_times = path_times(first_path, start_point)
    future_intervals = dict()
    for i in range(len(paths)):
        path = paths[i]
        current_path_times = path_times(path, start_point)
        for j in range(len(path)):
            point = path[j]
            if point in future_intervals.keys():
                continue
            if point not in first_path and point not in MEMORY_TIME.keys():
                interval = TIME_TO_MAX_RISK
            else:
                inner_time = current_path_times[j]
                time_to_visit = inner_time + (i+1) * MAXIMUM_SORTIE_TIME[0]
                if point in first_path:
                    k = last_index_of(first_path, point)
                    interval = time_to_visit - first_path_times[k]
                else:
                    time_from_last_visit = TIME[0] - MEMORY_TIME[point]
                    interval = time_to_visit + time_from_last_visit
            future_intervals[point] = interval
    future_intervals["default"] = MAXIMUM_SORTIE_TIME[0] * (len(paths) + 1)
    return future_intervals


def merge_futures(main_future, alternative_future):
    # change main_future in place
    for point in alternative_future.keys():
        if point not in main_future.keys() or alternative_future[point]<main_future[point]:
            main_future[point] = alternative_future[point]