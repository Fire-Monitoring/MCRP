from Util.util import *
from .three_phase_algorithm import initialize_ez, two_op_improvement_ez


def brideau_cavalier(start_point, time_function, time_limit):

    # step 1
    locations_list = list(MAP_APRIORI[0].keys())
    path, ellipse_points = initialize_ez(locations_list, start_point, time_limit, time_function)

    # step 2
    path = two_op_improvement_ez(path, start_point, time_limit, time_function)

    return path

def brideau_cavalier_interface(start_point, station, time_function, arguments, time_limit=None, time_limit_for_open_path=None, double=None, reorder_flag=False, return_mid=False, final=False, aprior_planning=None, use_old_future=False):

    if time_function==-2 and CONSTANT_PATH[0] is not None:
        return copy.deepcopy(CONSTANT_PATH[0])

    time_limit = MAXIMUM_SORTIE_TIME[0] if time_limit is None else time_limit

    path = brideau_cavalier(start_point, time_function, time_limit)

    if time_function==-2 and CONSTANT_PATH[0] is None:
        CONSTANT_PATH[0] = copy.deepcopy(path)

    return path
