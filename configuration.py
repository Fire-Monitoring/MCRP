PIXEL_WIDTH_CARMEL = [31.25]       # metre (before discretization by RESOLUTION)
LOCATION_FACTOR = int(284/15)
PIXEL_WIDTH_GENERATED = [62.5*LOCATION_FACTOR]
PIXEL_WIDTH_SHANXI = [1515.15]
PIXEL_WIDTH_RANDOM = 62.5        # metre
MAP_WIDTH_RANDOM = 150           # pixels
RESOLUTION = 2                   # pixels of image in map
K_BLUR = 2
DRONE_SPEED = [13.9]            # metre per second
TIME_TO_MAX_RISK = 1800 * (2**(0))
P_APRIORI = 0.000101          # units for a-priori probability of fire
P_OUTBREAK = P_APRIORI / TIME_TO_MAX_RISK    # per second
MAXIMUM_SORTIE_TIME = [1800]  # 30 minutes x 60 seconds
CHARGE_STATION = [(180, 70)]    # old: (150, 250)
CHARGE_STATION_SHANXI = (8, 8)

N_SORTIES_IN_MISSION = [15]

GRAPH_FLAG = [True]
GRAPHS_FOLDER_DICT = {"200": "graphs_r200",
                      "400": "graphs_r400",
                      "1000": "graphs_r1000", }
GRAPH_RES = "400"

map_carmel_name = "map_carmal.png"
