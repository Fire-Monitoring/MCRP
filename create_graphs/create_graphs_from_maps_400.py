from algorithms.grid_to_graph import *
from Util.map_functions import *

resolution = 400
PIXEL_WIDTH[0] = PIXEL_WIDTH_CARMEL[0]*2

for index in range(70):
    map_name = f"../maps/high_res/high_res_map_{index}.npy"
    map = load(map_name)
    map_apriori, _ = map_to_gains_and_distances(map, no_distances=True)
    neighborhoods, original_neighborhoods = map_to_graph(map_apriori, resolution, remove_zeroes=False)

    # Save dictionary to a .pkl file
    with open(f'../maps/graphs_r{resolution}_full/graph_{index}.pkl', 'wb') as file:  # 'wb' = write in binary mode
        pickle.dump(neighborhoods, file)

