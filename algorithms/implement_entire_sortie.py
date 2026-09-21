import time

from Util.util import *
from Util.demo_sim import *

from .alg_configurations import alg_configurations
from .three_phase_algorithm import EZ_interface
from .LNS_algorithm import LNS_interface


algorithms = {"three phase": EZ_interface,
              "lns": LNS_interface,
              }

def return_next_step(algorithm, station, time_function, config, using_n_future_sorties=0, double=None, decision=False):
    if PATH_BY_ALGORITHM[0] == None or STEP_INDEX[0] >= len(PATH_BY_ALGORITHM[0]) or PATH_BY_ALGORITHM[0]=="wait":
        if APRIORI_PATHS[0] is not None and APRIORI_PATHS[0][PATH_INDEX[0]] is not None:
            PATH_BY_ALGORITHM[0] = APRIORI_PATHS[0][PATH_INDEX[0]]
        elif type(using_n_future_sorties)==str:
            PATH_BY_ALGORITHM[0] = multi_sorties_planning(algorithm, station, time_function, config,
                                                          int(using_n_future_sorties), double=double,
                                                          intervals_flag=True, decision=decision)
        elif type(using_n_future_sorties)==tuple:
            n_future_sorties, n_iterations = using_n_future_sorties
            PATH_BY_ALGORITHM[0] = iterative_multi_sorties_planning(algorithm, station, time_function, config, n_future_sorties, n_iterations,
                                             double=double)
        elif using_n_future_sorties > 0:
            PATH_BY_ALGORITHM[0] = multi_sorties_planning(algorithm, station, time_function, config,
                                                          using_n_future_sorties, double=double, decision=decision)
        elif using_n_future_sorties == 0:
            PATH_BY_ALGORITHM[0] = algorithm(station, station, time_function, config, double=double, final=True)
            if DEC_PROCEDURE[0] is not None:
                alternative_path = algorithm(station, station, None, config, double=double, final=True)
                f_time = None if DEC_PROCEDURE[0] == "naive" else time_function
                score_default = evaluate_path(PATH_BY_ALGORITHM[0], start_point=station, time_function=f_time)[1]
                score_new = evaluate_path(alternative_path, start_point=station, time_function=f_time)[1]
                if score_new > score_default:
                    PATH_BY_ALGORITHM[0] = alternative_path
        else:  # using_n_future_sorties < 0
            using_n_future_sorties = -using_n_future_sorties
            PATH_BY_ALGORITHM[0] = multi_sorties_planning(algorithm, station, time_function, config,
                                                          using_n_future_sorties, double=double,
                                                          relative_default_flag=True, decision=decision)

        if SAVE_PATHS[0]:
            SAVED_PATHS.append(PATH_BY_ALGORITHM[0])

        if APRIORI_PATHS[0] is not None:
            PATH_INDEX[0] += 1

        STEP_INDEX[0] = 0
    next_step = PATH_BY_ALGORITHM[0][STEP_INDEX[0]] if PATH_BY_ALGORITHM[0]!="wait" else f"wait {MAXIMUM_SORTIE_TIME[0]}"
    STEP_INDEX[0]+=1
    return next_step


def multi_sorties_planning(algorithm, station, time_function, config, n_future_sorties, only_return_future = False, double=None, intervals_flag=False, relative_default_flag=False, decision = False):
    # first planning
    if n_future_sorties>int(n_future_sorties):
        first_sortie = None
        n_future_sorties = int(n_future_sorties)
    else:
        first_sortie = algorithm(station, station, time_function, config, double=double, use_old_future=REUSE_PROTOCOL[1])

    original_dynamic_map = MAP_DYNAMIC[0]   # Keeping it aside, will return after the demo
    future_sorties = []  # List of sorties (without the first one), Each sortie is a list.

    prev_sortie = first_sortie
    temp_map_dynamic = copy.deepcopy(original_dynamic_map)

    # Demo of future sorties
    for _ in range(n_future_sorties):
        temp_map_dynamic = demo_simulation(temp_map_dynamic, prev_sortie, in_place=True)
        MAP_DYNAMIC[0] = temp_map_dynamic
        new_sortie = algorithm(station, station, time_function, config, double=double)
        future_sorties.append(new_sortie)
        prev_sortie = new_sortie

        # for reuse
        if REUSE_PROTOCOL[1] is not False and OLD_FUTURE_PATH[0] is None:
            OLD_FUTURE_PATH[0] = new_sortie

    if only_return_future:
        MAP_DYNAMIC[0] = original_dynamic_map
        if intervals_flag:
            return create_future_intervals(first_sortie, future_sorties)
        return create_future(future_sorties)

    if FUTURE_AR_PROTOCOL[0] is not None:
        FUTURE[0] = create_future(future_sorties)  # Creates dict for future visit times
        FUTURE_INTERVALS[0] = create_future_intervals(first_sortie, future_sorties)  # Creates dict for future visit intervals
        f_time_1 = time_functions_dict["future intervals"]
        f_time_2 = time_functions_dict["future relative default"] if relative_default_flag else time_functions_dict["future"]
        f_time = (f_time_1, f_time_2)
    elif intervals_flag:
        FUTURE_INTERVALS[0] = create_future_intervals(first_sortie, future_sorties)  # Creates dict for future visit intervals
        f_time = time_functions_dict["future intervals"]
    else:
        FUTURE[0] = create_future(future_sorties)  # Creates dict for future visit times
        f_time = time_functions_dict["future relative default"] if relative_default_flag else time_functions_dict["future"]
    MAP_DYNAMIC[0] = original_dynamic_map

    # second planning
    potential_first_sortie = algorithm(station, station, f_time, config, double=double, final=True, aprior_planning=None)
    if DEC_PROCEDURE[0] is None:
        return potential_first_sortie

    if DEC_PROCEDURE[0]=="naive":
        f_time=None
    elif FUTURE_AR_PROTOCOL[0]:
        f_time = f_time_1 if FUTURE_AR_PROTOCOL[0][3]=="a" else f_time_2
    score_old = evaluate_path(first_sortie, start_point = station, time_function=f_time)[1]
    score_new = evaluate_path(potential_first_sortie, start_point = station, time_function=f_time)[1]
    path = first_sortie if score_new < score_old else potential_first_sortie
    return path


def iterative_multi_sorties_planning(algorithm, station, time_function, config, n_future_sorties, n_iterations, double=None):
    f_time = time_function
    for i in range(n_iterations):
        first_sortie = algorithm(station, station, f_time, config, double=double)
        original_dynamic_map = MAP_DYNAMIC[0]   # Keeping it aside, will return after the demo
        future_sorties = []  # List of sorties (without the first one), Each sortie is a list.

        prev_sortie = first_sortie
        temp_map_dynamic = copy.deepcopy(original_dynamic_map)

        for _ in range(n_future_sorties):  # Demo of future sorties
            temp_map_dynamic = demo_simulation(temp_map_dynamic, prev_sortie, in_place=True)
            MAP_DYNAMIC[0] = temp_map_dynamic
            new_sortie = algorithm(station, station, time_function, config, double=double)
            future_sorties.append(new_sortie)
            prev_sortie = new_sortie

        FUTURE[0] = create_future(future_sorties)  # Creates dict for future visit times
        f_time = time_functions_dict["future"]
        MAP_DYNAMIC[0] = original_dynamic_map

    path = algorithm(station, station, f_time, config, double=double)
    return path


def step_by_deterministic_path(start_point, arguments, decision=False):
    if len(arguments)==4:
        algorithm_name, config_name, time_function_name, k = arguments
        n_future_sorties = 0
    else:
        algorithm_name, config_name, time_function_name, k, n_future_sorties = arguments
    algorithm = algorithms[algorithm_name]
    time_function = time_functions_dict[time_function_name]
    config = alg_configurations[algorithm_name][config_name]
    return return_next_step(algorithm, start_point, time_function, config, n_future_sorties, double=k, decision=decision)
