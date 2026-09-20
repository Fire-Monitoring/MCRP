from numpy import array, random, var, load
from matplotlib import pyplot as plt
import matplotlib.patheffects as pe
import pickle
from .util import *
from create_graphs.map_carmel_reconstruction import *


from configuration import *
from globals import *


def size_map():
    img = Image.open(map_carmel_name)
    img = asarray(img)
    print(img.shape)


def discretization(map, pix_size, by_max=False, dont_change_pix_width=False):
    if by_max:
        f = max
    else:
        f = lambda l: sum(l)/len(l)
    new_map_as_array = []
    for i in range(int(map.shape[0] / pix_size)):
        new_line = []
        for j in range(int(map.shape[1] / pix_size)):
            current_list = []
            for k in range(pix_size * i, pix_size * i + pix_size):
                for h in range(pix_size * j, pix_size * j + pix_size):
                    current_list.append(map[k][h])
            new_line.append(f(current_list))
        new_map_as_array.append(new_line)

    if not dont_change_pix_width:
        PIXEL_WIDTH[0]*=pix_size
    return array(new_map_as_array)


def take_sub_map(apriori_map, outbreak_map, boundaries):
    y_from, y_to, x_from, x_to = boundaries
    x_from = 0 if x_from == None else x_from
    y_from = 0 if y_from == None else y_from
    x_to = len(apriori_map[0]) if x_to == None else x_to
    y_to = len(apriori_map) if y_to == None else y_to
    apriori_map = [line[x_from:x_to] for line in apriori_map[y_from:y_to]]
    apriori_map = array(apriori_map)
    outbreak_map = [line[x_from:x_to] for line in outbreak_map[y_from:y_to]]
    outbreak_map = array(outbreak_map)
    return apriori_map, outbreak_map


def get_discrete_maps(pix_size, boundaries=None):
    map_apriori = get_map()  # numpy.ndarray
    PIXEL_WIDTH[0] = PIXEL_WIDTH_CARMEL[0]
    apriori_dscrt = discretization(map_apriori, pix_size, by_max=False)  # numpy.ndarray
    map_outbreak = get_map(outbreak=True)
    outbreak_dscrt = discretization(map_outbreak, pix_size, by_max=False, dont_change_pix_width=True)  # numpy.ndarray

    if boundaries is not None:
        apriori_dscrt, outbreak_dscrt = take_sub_map(apriori_dscrt, outbreak_dscrt, boundaries)

    return apriori_dscrt, outbreak_dscrt


def get_generated_map(index, boundaries=None, shanxi=False):
    if type(index)==tuple:
        map_name = f"sparkle_maps/sparkle_map_{index[0]}_{index[1]}_{index[2]}.npy"
    elif type(index) == str and shanxi:
        s_index = int(index[7:])
        map_name = f"map_shanxi_{s_index}.npy"
    elif type(index)==str and index[:8]=="high var":
        hv_index = int(index[9:])
        map_name = f"high_var/high_var_{hv_index}.npy"
    elif GRAPH_FLAG[0]:
        map_name = f"maps/high_res/high_res_map_{index}.npy"
        graph_name = f"maps/{GRAPHS_FOLDER_DICT[GRAPH_RES]}/graph_{index}.pkl"
        apriori_map = None
        count_steps = 0
        max_steps_out = 10
        while apriori_map is None and count_steps < max_steps_out:
            try:
                with open(graph_name, "rb") as f:
                    graph = pickle.load(f)
                    GRAPH[0] = graph  # point: included_points, value, inner_perimeter
                    orig_map = load(map_name)
                    apriori_map = {center: graph[center][1] for center in graph.keys()}
            except:
                graph_name = "../" + graph_name
                map_name = "../" + map_name
                count_steps += 1

        outbreak_map = {center: apriori_map[center]/TIME_TO_MAX_RISK for center in apriori_map.keys()}
        PIXEL_WIDTH[0] = PIXEL_WIDTH_CARMEL[0]*2

        return (orig_map, apriori_map), outbreak_map
    else:
        map_name = f"random_map_{index}.npy"

    apriori_map = None
    path = f"maps/{map_name}"
    max_steps_out = 10
    count_steps = 0
    while apriori_map is None and count_steps < max_steps_out:
        try:
            apriori_map = load(path)
        except:
            path = "../" + path
            count_steps += 1

    if P_APRIORI!=0.000101:
        apriori_map = apriori_map * P_APRIORI / 0.000101

    if shanxi:
        PIXEL_WIDTH[0] = PIXEL_WIDTH_SHANXI[0]
    else:
        PIXEL_WIDTH[0] = PIXEL_WIDTH_GENERATED[0]
    outbreak_map = apriori_map/TIME_TO_MAX_RISK

    if boundaries is not None:
        apriori_map, outbreak_map = take_sub_map(apriori_map, outbreak_map, boundaries)

    return apriori_map, outbreak_map


def soft_random_map_old(length=40, k_blur=2):
    PIXEL_WIDTH[0] = PIXEL_WIDTH_RANDOM
    simple_map = random.rand(length, length)/500
    simple_map*=(simple_map<1/1000)
    new_map = ndarray([length, length])

    for i in range(length):
        for j in range(length):
            values_list = []
            for k in range(max(0, i-k_blur), min(length, i+k_blur+1)):
                for h in range(max(0, j - k_blur), min(length, j + k_blur + 1)):
                    values_list.append(simple_map[k][h])
            avrg = sum(values_list)/len(values_list)
            new_map[i][j] = avrg

    new_map = new_map * (new_map>k_blur**0.25/5000)
    outbreak_map = new_map / TIME_TO_MAX_RISK

    return new_map, outbreak_map


def soft_random_map(length=40, k_blur=2):
    PIXEL_WIDTH[0] = PIXEL_WIDTH_RANDOM
    simple_map = random.rand(length, length)/500
    simple_map*=(simple_map<1/1000)
    new_map = ndarray([length, length])

    for i in range(length):
        for j in range(length):
            values_list = []
            for k in range(max(0, i-k_blur), min(length, i+k_blur+1)):
                for h in range(max(0, j - k_blur), min(length, j + k_blur + 1)):
                    values_list.append(simple_map[k][h])
            avrg = sum(values_list)/len(values_list)
            new_map[i][j] = avrg

    new_map = new_map * (new_map>k_blur**0.25/5000)
    outbreak_map = new_map / TIME_TO_MAX_RISK

    return new_map, outbreak_map


def create_map(map_name="carmel", width_of_map_for_dynamic=15, boundaries=None):
    # bounderies: (y_from, y_to, x_from, x_to)
    if map_name == "carmel":
        map_apriori, orig_map_outbreak = get_discrete_maps(RESOLUTION, boundaries)
    elif type(map_name)==str and map_name[:6] == "shanxi":
        map_apriori, orig_map_outbreak = get_generated_map(map_name, boundaries, shanxi=True)
        CHARGE_STATION[0] = CHARGE_STATION_SHANXI
    elif map_name=="random":
        map_apriori, orig_map_outbreak = soft_random_map(MAP_WIDTH_RANDOM, K_BLUR)
    else:
        map_apriori, orig_map_outbreak = get_generated_map(map_name, boundaries)

    if type(map_name)==int and GRAPH_FLAG[0]:
        NORMALIZED_CHARGE_STATION[0] = CHARGE_STATION[0]
        LOCATION[0] = NORMALIZED_CHARGE_STATION[0]

        orig_map, map_apriori = map_apriori
        map_apriori[NORMALIZED_CHARGE_STATION[0]] = 0
        orig_map_outbreak[NORMALIZED_CHARGE_STATION[0]] = 0
        GRAPH[0][NORMALIZED_CHARGE_STATION[0]] = ([NORMALIZED_CHARGE_STATION[0]], 0, 0)
        MAP_APRIORI[0] = copy.deepcopy(map_apriori)
        MAP_DYNAMIC[0] = map_apriori
        MAP_OUTBREAK[0] = orig_map_outbreak
        MAP_ORIG[0] = orig_map
        return

    MAP_ORIG[0] = map_apriori
    if map_name in ["carmel", "random"]:
        pix_size = int(map_apriori.shape[1] / width_of_map_for_dynamic)
        map_dynamic = discretization(map_apriori, pix_size)
        map_outbreak = discretization(orig_map_outbreak, pix_size, dont_change_pix_width=True)
        location_factor = pix_size
    elif map_name=="shanxi":
        map_dynamic = map_apriori
        map_outbreak = orig_map_outbreak
        pix_size = 1
        location_factor = 1
    else:
        map_dynamic = map_apriori
        map_outbreak = orig_map_outbreak
        pix_size = 1
        location_factor = LOCATION_FACTOR

    PIXEL_SIZE[0] = pix_size

    y_station = CHARGE_STATION[0][0]
    x_station = CHARGE_STATION[0][1]
    if boundaries is not None and boundaries[0] is not None:
        y_station-=(boundaries[0]*location_factor)
    if boundaries is not None and boundaries[2] is not None:
        x_station-=(boundaries[2]*location_factor)


    NORMALIZED_CHARGE_STATION[0] = (int(y_station / location_factor), int(x_station / location_factor))
    LOCATION[0] = NORMALIZED_CHARGE_STATION[0]

    map_dynamic_as_dict, distances = map_to_gains_and_distances(map_dynamic)
    map_outbreak_as_dict, _ = map_to_gains_and_distances(map_outbreak)

    map_dynamic_as_dict[NORMALIZED_CHARGE_STATION[0]]=0
    map_outbreak_as_dict[NORMALIZED_CHARGE_STATION[0]]=0

    MAP_APRIORI[0] = copy.deepcopy(map_dynamic_as_dict)
    MAP_DYNAMIC[0] = map_dynamic_as_dict
    MAP_OUTBREAK[0] = map_outbreak_as_dict
    DISTANCES[0] = distances


def print_map():
    plt.gray()
    plt.imshow(MAP_ORIG[0])


def print_path():
    loc_from_prev, loc_to_prev = None, None
    for i in range(len(PATH) - 1):
        loc_from, loc_to = PATH[i], PATH[i + 1]
        plt.plot([loc_from[1], loc_to[1]], [loc_from[0], loc_to[0]], "yellow", lw=5)
        if loc_to_prev is not None:
            plt.plot([loc_from_prev[1], loc_to_prev[1]], [loc_from_prev[0], loc_to_prev[0]], "red", lw=3)
        loc_from_prev, loc_to_prev = loc_from, loc_to
    if loc_to_prev is not None:
        plt.plot([loc_from_prev[1], loc_to_prev[1]], [loc_from_prev[0], loc_to_prev[0]], "red", lw=3)

        # plt.plot([loc_from[1], loc_to[1]], [loc_from[0], loc_to[0]], "red", path_effects=[pe.Stroke(linewidth=3, foreground='yellow'), pe.Normal()])
    plt.plot([PATH[0][1]], [PATH[0][0]], "red", marker="o", linestyle="None",
             path_effects=[pe.Stroke(linewidth=3, foreground='yellow'), pe.Normal()])

    print(PATH)
    print()


def local_var(map):
    length, width = map.shape
    total_local_vars = 0
    count=0
    for l in range(1, length-1):
        for w in range(1, width-1):
            local_map = map[l-1:l+2,w-1:w+2]
            local_var = var(local_map)
            total_local_vars+=local_var
            count+=1
    mean_local_val = total_local_vars/count
    return mean_local_val


def local_var_of_dictionary(map):
    length, width = map.shape
    total_local_vars = 0
    count=0
    for l in range(1, length-1):
        for w in range(1, width-1):
            local_map = []
            for i in range[l-1, l+2]:
                for j in range[w-1, w+2]:
                    if (i, j) in map.keys():
                        local_map.append(map[(i,j)])
            local_var = var(local_map)
            total_local_vars+=local_var
            count+=1
    mean_local_val = total_local_vars/count
    return mean_local_val


def relative_var(map):
    return local_var(map)/var(map)


def weighted_blur_list(l_values, sigma=0.5):
    res = l_values[0]*(1-sigma)
    local_sigma = sigma/(len(l_values)-1)
    for value in l_values[1:]:
        res+=value*local_sigma
    return res


def weighted_blur_map(map, sigma):
    # map: ndarray
    shape = map.shape
    new_map = ndarray(map.shape)
    for l in range(shape[0]):
        for w in range(shape[1]):
            list_to_blur = []
            list_to_blur.append(map[l,w])
            for i in range(l-1, l+2):
                for j in range(w-1, w+2):
                    if (i==l and j==w) or i<0 or w<0 or i>=shape[0] or j>=shape[1]:
                        continue
                    list_to_blur.append(map[i,j])
            new_value = weighted_blur_list(list_to_blur, sigma)
            new_map[l,w] = new_value
    return new_map

##############
# New: Shanxi
##############

def rgb_to_monochrome(M: np.ndarray, D: dict) -> np.ndarray:
    """
    Convert an RGB image to a monochrome map using nearest RGB mapping.

    Parameters:
        M (np.ndarray): Input RGB array of shape (n, m, 3).
        D (dict): Mapping { (r,g,b): value }.

    Returns:
        np.ndarray: Monochrome array of shape (n, m).
    """
    # Convert dictionary keys to numpy array for vectorized distance computation
    keys = np.array(list(D.keys()))  # shape (k, 3)
    values = np.array(list(D.values()))  # shape (k,)

    n, m, _ = M.shape
    output = np.zeros((n, m), dtype=values.dtype)

    # Flatten image for easier computation
    flat_pixels = M.reshape(-1, 3)

    for i, pixel in enumerate(flat_pixels):
        # Compute squared distances to all keys
        distances = np.sum((keys - pixel) ** 2, axis=1)
        nearest_idx = np.argmin(distances)
        output.flat[i] = values[nearest_idx]

    return output