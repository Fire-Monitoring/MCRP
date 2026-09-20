TIME = [0]
SORTIE_TIME = [0]  # Internal time of monitoring sortie

# map

LOCATION = [None]
NORMALIZED_CHARGE_STATION = [None]
MAP_DYNAMIC = [None]
MAP_APRIORI = [None]
MAP_OUTBREAK = [None]
DISTANCES = [None]
SAVED_MAP = [None]

MAP_ORIG = [None]

PIXEL_WIDTH = [None]  # metre in pixel
PIXEL_SIZE = [1]      # ration between pixel of MAP_ORIG and MAP_APRIORI

# path

UNCERTAINTY = [0]
PATH = []

# algorithms

MEMORY_TIME = dict()         # memory of time of visit
MEMORY_SHORT = [None, None]  # saving [location, time] of the previous point
MEMORY_INTERVAL = dict()     # memory of period between visits
MEMORY_ALL_INTERVALS = dict()
INTERVAL_LIST_LENGTH = 1500
INTERVALS_LIST = []
DIST_LIST = []             # X-values for linear regression with INTERVALS_LIST: distances for station
APRIORI_VALUES_LIST = []   # X-values for linear regression with INTERVALS_LIST: apriori values
QUOTIENT_LIST = []
LINEAR_MODEL_TYPE = [None]
TREND_LINE = [None, None]    # slope, intercept
CONVEXITY = [None]

LR_INTERVAL = 1              # "proportion" or non-negative number

FUTURE = [None]              # dict for future visit times
                             # ref time (time=0): the end of the nearest sortie
                             # future["default"] = n_paths * MAXIMUM_SORTIE_TIME[0]

FUTURE_INTERVALS = [None]    # dict for future visit intervals

OPTIMAL_INVALID = [0]        # count the optimal heuristic paths that we have to give up because they are invalid

FULL_PATH_TIME_WITH_CHARGING = [None]
AVERAGE_DISTANCE_FROM_STATION = [None]
P_FOR_COMBINED = 0.25
RELATIVE_TIME_FROM_STATION = [None]  # Average time_from_station / maximum_sortie_time
GREEDY_PATH_DURATION = [None]
TWO_MINS_HEURISTIC = [None]

# entire path \ sub_path
PATH_BY_ALGORITHM = [None]
STEP_INDEX = [0]
N_NEXT = [None]
SUB_PATH_BY_ALGORITHM = [None]
REST_PATH = [None]
SUB_PATH_STEP_INDEX = [0]
AGGRESSIVE_MULTY_PATH = [True]

DEC_PROCEDURE = [None]
FUTURE_AR_PROTOCOL = [None]  # [initial, insert-remove, reorder, decision]
FUTURE_CD_PROTOCOL = ["cc"]  # [absolute, relative]
PREV_AR = [None]

REUSE_PROTOCOL = [False, False]     # [first_current to new_current, future to first_current]
                                    # [{True, False}, {"soft", "hard", False}]
OLD_FUTURE_PATH = [None]
ELLIPSE_POINTS = [None]

USE_BEST_GUESS = [False]
BEST_GUESS = [None]

MYLS_GRAPH = [None]  # successors, predecessors, sorted_graph

LIMIT_ITERATIVE_MYLS = [None]

CONSTANT_PATH = [None]

FULL_PERIOD = []
PERIOD_PATH_INDEX = [0]
PERIOD_NODE_IN_PATH_INDEX = [0]

APRIORI_PATHS = [None]
PATH_INDEX = [0]

GRAPH = [None]
NEIGHBORS_DICT = [None]

SAVE_TIME = [False]

SAVE_PATHS = [False]
SAVED_PATHS = []

# statistical data
COUNT_IMPROVES = []

# for small instances
NODES = [None]