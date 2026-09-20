from Util.map_functions import *
from algorithms.implement_entire_sortie import step_by_deterministic_path
import time

def simulate_path(width_of_map_for_dynamic=15, map_name="carmel", n_steps_or_sorties=8, algorithm_name="k forward", arguments=[6], text=None, by_steps=False, duration=None, suffix=None, boundaries=None, return_results=False, waiting_time=0):
    # boundaries: y_from, y_to, x_from, x_to
    reset_globals()

    algorithms = {"deterministic_doubled_path": step_by_deterministic_path,
                  }

    f_next_step = algorithms[algorithm_name]
    LOCATION[0] = CHARGE_STATION[0]

    create_map(map_name, width_of_map_for_dynamic, boundaries)

    # print([GRAPH[0][node][2] for node in GRAPH[0]])
    # return None

    PATH.append(LOCATION[0])

    # execute algorithm
    count_steps_or_sorties = 0
    count_sorties = 0
    count_steps = 0

    time_before = time.time()
    to_stop = False
    calculate_avrg_dist_from_station_and_relative_time(MAP_DYNAMIC[0])
    while not to_stop:
        # print(count_steps, TIME[0])
        count_steps+=1
        next_location = f_next_step(LOCATION[0], arguments)
        insert_to_memory(LOCATION[0])
        move(next_location, max_duration=duration)
        if SORTIE_TIME[0]>MAXIMUM_SORTIE_TIME[0]:
            print("########################################\n"
                  "# Monitoring failed: ran out of energy #\n"
                  "########################################")
            return

        if by_steps or LOCATION[0]==NORMALIZED_CHARGE_STATION[0]:
            count_steps_or_sorties+=1

        if LOCATION[0]==NORMALIZED_CHARGE_STATION[0]:
            count_sorties+=1
            resting_time = MAXIMUM_SORTIE_TIME[0] - SORTIE_TIME[0]
            UNCERTAINTY[0] += time_over_map(resting_time)
            SORTIE_TIME[0] = 0

        to_stop = (duration is None and count_steps_or_sorties == n_steps_or_sorties) or (duration is not None and TIME[0]>=duration)

    if waiting_time>0:
        UNCERTAINTY[0] += time_over_map(waiting_time)
    average_uncertainty = UNCERTAINTY[0] / TIME[0]
    total_time = TIME[0]

    if return_results:
        # print("computational time:", time.time() - time_before)
        return average_uncertainty

    print("count_steps:", count_steps)
    print("count_sorties:", count_sorties)
    print("computational time:", time.time() - time_before)

    # print map and path
    print_map()
    stretch_path()
    print_path()

    name = f"{algorithm_name}, map {map_name}"
    if suffix is not None:
        name+=" " + suffix

    text = f"{text}, " if text else ""
    plt.title(name + f"\nwidth = {width_of_map_for_dynamic}, {text}time={round_for_simulation(total_time)}, average uncertainty={round_for_simulation(average_uncertainty,1)}")
    plt.savefig(f"results/{name}, {text}{width_of_map_for_dynamic}")
    plt.clf()


def move(next_location, max_duration=None):
    if type(next_location)==str:
        time_period = int(next_location[5:])
    else:
        previous_location = LOCATION[0]
        distance = cartesian(previous_location, next_location)
        time_period = distance / DRONE_SPEED[0]

    if max_duration is not None and time_period+TIME[0]>max_duration:
        uncertainty = time_over_map(max_duration-TIME[0])
        UNCERTAINTY[0] += uncertainty
        return True  # need to stop

    uncertainty = time_over_map(time_period)
    UNCERTAINTY[0] += uncertainty
    if next_location is None or next_location[:4] != "wait":
        LOCATION[0] = next_location
        if next_location is not None:
            MAP_DYNAMIC[0][next_location] = 0
    PATH.append(next_location)

    if next_location==NORMALIZED_CHARGE_STATION[0] and len(INTERVALS_LIST)>=INTERVAL_LIST_LENGTH:
        if LINEAR_MODEL_TYPE[0] in ["dist", "value", "quotient"]:
            X_dict = {"dist": DIST_LIST, "value": APRIORI_VALUES_LIST, "quotient": QUOTIENT_LIST}
            X = X_dict[LINEAR_MODEL_TYPE[0]]
            convexity, slope, intercept = trend_line(X, INTERVALS_LIST, True)
            TREND_LINE[0] = slope
            TREND_LINE[1] = intercept
            CONVEXITY[0] = convexity
        if LINEAR_MODEL_TYPE[0]=="comb":
            X1 = DIST_LIST
            X2 = APRIORI_VALUES_LIST
            coefficients, intercept = multilinear_regression(X1, X2, INTERVALS_LIST, True)
            TREND_LINE[0] = list(coefficients)
            TREND_LINE[1] = intercept



