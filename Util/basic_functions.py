from configuration import *
from globals import *
import copy
import numpy as np

def simple_cartesian(location1, location2):
    try:
        dist = ((location1[0]-location2[0])**2 + (location1[1]-location2[1])**2)**0.5
        return PIXEL_WIDTH[0] * dist
    except:
        print(location1, location2)
        p = 1/0


def cartesian(location1, location2):
    try:
        if type(location1[0]) == tuple:
            return cartesian(location1[0], location2[0])
        dist = ((location1[0]-location2[0])**2 + (location1[1]-location2[1])**2)**0.5
        if GRAPH_FLAG[0] and GRAPH[0] is not None:
            dist+=GRAPH[0][location2][2]
        return PIXEL_WIDTH[0] * dist
    except:
        print(location1, location2)
        p = 1/0


def cartesian_by_indices(location1, location2):
    return cartesian(NODES[0][location1], NODES[0][location2])


def zeros_after_point(v):
    l = 0

    if v>1:
        return 0

    for _ in range(10):
        if 10 ** (-l) < v:
            return l-1
        l += 1
    return "ERROR"


def round_for_simulation(v, more=0):
    if v==0:
        return 0
    n_0 = zeros_after_point(v)
    ndigits = 1 if v>1 else n_0+2
    ndigits+=more
    return round(v, ndigits)


# checking if edges intersect

def orientation(p, q, r):
    """Return the orientation of the triplet (p, q, r).
    0 -> p, q and r are collinear
    1 -> Clockwise
    2 -> Counterclockwise
    """
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

    if val == 0:
        return 0  # Collinear
    elif val > 0:
        return 1  # Clockwise
    else:
        return 2  # Counterclockwise


def on_segment(p, q, r):
    """Given three collinear points p, q, r, check if point q lies on the segment pr."""
    return (min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and
            min(p[1], r[1]) <= q[1] <= max(p[1], r[1]))


def are_collinear(edge1, edge2):
    # Unpack the points from the edges
    (x1, y1), (x2, y2) = edge1
    (x3, y3), (x4, y4) = edge2

    # Vectors representing the direction of the edges
    vector1 = (x2 - x1, y2 - y1)  # Direction vector of the first edge
    vector2 = (x4 - x3, y4 - y3)  # Direction vector of the second edge

    # Cross product to check if the vectors are collinear
    cross_product = (vector1[0] * vector2[1]) - (vector1[1] * vector2[0])

    # If cross product is 0, the vectors are collinear (same line)
    return cross_product == 0


def do_intersect(edge1, edge2):
    if type(edge1[0][0])==tuple:
        edge1, edge2 = (edge1[0][0], edge1[1][0]), (edge2[0][0], edge2[1][0])
    """Return True if the line segments p1p2 and q1q2 intersect."""
    # Find the four orientations needed for general and special cases
    if are_collinear(edge1, edge2):
        return False

    p1, p2 = edge1
    q1, q2 = edge2

    if p1==q2 or q1==p2 or p1==q1 or q2==p2:
        return False

    o1 = orientation(p1, p2, q1)
    o2 = orientation(p1, p2, q2)
    o3 = orientation(q1, q2, p1)
    o4 = orientation(q1, q2, p2)

    # General case: If the orientations are different, the segments intersect
    if o1 != o2 and o3 != o4:
        return True

    # Special cases: Check for collinearity and overlap
    # p1, p2, q1 are collinear, and q1 lies on the segment p1p2
    if o1 == 0 and on_segment(p1, q1, p2):
        return True

    # p1, p2, q2 are collinear, and q2 lies on the segment p1p2
    if o2 == 0 and on_segment(p1, q2, p2):
        return True

    # q1, q2, p1 are collinear, and p1 lies on the segment q1q2
    if o3 == 0 and on_segment(q1, p1, q2):
        return True

    # q1, q2, p2 are collinear, and p2 lies on the segment q1q2
    if o4 == 0 and on_segment(q1, p2, q2):
        return True

    # Otherwise, the segments do not intersect
    return False


def integral_uncertainty_by_increasing_and_total(t_increasing, t_total, p_old, p_new):
    uncertainty_while_increasing = t_increasing * (p_old + p_new) / 2
    uncertainty_while_p_is_maximal = (t_total - t_increasing) * p_new
    # print(t_increasing, t_total, p_old, p_new)
    # print(uncertainty_while_increasing, uncertainty_while_p_is_maximal)
    return uncertainty_while_increasing + uncertainty_while_p_is_maximal


def time_over_map(time_period, map_dynamic = None):
    if map_dynamic == None:
        demo = False
        map_dynamic = MAP_DYNAMIC[0]
    else:
        demo = True
    total_uncertainty = 0

    for location in map_dynamic.keys():
        p_apriori = MAP_APRIORI[0][location]
        p_outbreak = MAP_OUTBREAK[0][location]
        uncertainty = time_over_pixel(location, p_apriori, p_outbreak, time_period, map_dynamic)
        total_uncertainty+=uncertainty

    if not demo:
        TIME[0] += time_period
        SORTIE_TIME[0] += time_period
    return total_uncertainty


def time_over_pixel(pixel, p_apriori, p_outbreak, time_period, map_dynamic = None):
    if map_dynamic == None:
        map_dynamic = MAP_DYNAMIC[0]

    # update p
    if p_outbreak==0:
        return 0
    p_old = map_dynamic[pixel]
    p_outbreak_by_time = p_outbreak * time_period
    p_new = min(p_old + p_outbreak_by_time, p_apriori)
    map_dynamic[pixel] = p_new

    # calculate uncertainty
    t_increasing = min((p_apriori - p_old) / p_outbreak, time_period)
    uncertainty = integral_uncertainty_by_increasing_and_total(t_increasing, time_period, p_old, p_new)
    return uncertainty


def to_average(X, Y, min_n=0, count = False):
    unique_X = list(set(X))
    unique_X.sort()
    sums = []
    counts = []
    values = []
    for x in unique_X:
        sums.append(0)
        counts.append(0)
        values.append([])

    for i in range(len(Y)):
        y = Y[i]
        x = X[i]

        x_idx = unique_X.index(x)
        sums[x_idx]+=y
        counts[x_idx]+=1
        values[x_idx].append(y)

    for i in range(len(unique_X)-1,-1,-1):
        if counts[i]<min_n:
            del counts[i]
            del sums[i]
            del unique_X[i]
            del values[i]

    new_y = [sums[i] / counts[i] for i in range(len(sums))]

    if count:
        return unique_X, new_y, sum(counts)
    return unique_X, new_y


def discreet(l, n):
    min_l = min(l)
    prop = (max(l)-min_l)/n
    new_list = [(x-min_l)/prop for x in l]
    new_list = [int(x) for x in new_list]
    for i in range(len(new_list)):
        new_list[i] = n-1 if new_list[i]==n else new_list[i]
    new_list = [min_l+x*prop for x in new_list]
    return new_list


def trend_line(x_values, y_values, squared=False):
    x = np.array(x_values)
    y = np.array(y_values)
    deg = 2 if squared else 1
    coefficients = np.polyfit(x, y, deg)
    return coefficients


def get_relevant_points():
    relevant_points = []
    for point in MAP_DYNAMIC[0].keys():
        if point==NORMALIZED_CHARGE_STATION[0]:
            continue
        distance = cartesian(NORMALIZED_CHARGE_STATION[0], point)
        time_distance = distance/DRONE_SPEED[0]
        if time_distance<=MAXIMUM_SORTIE_TIME[0]/2:
            relevant_points.append(point)
    return relevant_points


def greedy_path():
    relevant_points = get_relevant_points()
    path = [NORMALIZED_CHARGE_STATION[0]]
    prev_point = NORMALIZED_CHARGE_STATION[0]
    while len(relevant_points)>0:
        next_point_and_dist = (-1, -1)
        for point in relevant_points:
            dist = cartesian(prev_point, point)
            if next_point_and_dist[0]==-1 or dist<next_point_and_dist[1]:
                next_point_and_dist = (point, dist)
        path.append(next_point_and_dist[0])
        relevant_points.remove(next_point_and_dist[0])
    path.append(NORMALIZED_CHARGE_STATION[0])
    return path


def improved_greedy_path():
    path = greedy_path()
    path = one_op_improvement_basic(path)
    path = two_op_improvement_basic(path)
    path = one_op_improvement_basic(path)
    return path


def reverse_sub_path(path, i_from, j_to):
    # including both i, j
    new_path = copy.deepcopy(path)
    temp_list = []
    for point in new_path[i_from:j_to+1]:
        temp_list.append(point)

    temp_list.reverse()
    for h in range(i_from, j_to+1):
        new_path[h] = temp_list[h-i_from]

    return new_path


def path_times(path, start_point=None):
    if start_point==None:
        start_point = LOCATION[0]

    time_list = []
    temp_time = 0
    previous_location = start_point
    for next_location in path:
        distance = cartesian(previous_location, next_location)
        delta_time = distance / DRONE_SPEED[0]
        temp_time+=delta_time
        time_list.append(temp_time)
        previous_location=next_location

    return time_list


def two_op_improvement_basic(path):
    no_improvement = False
    while no_improvement==False:
        no_improvement=True
        for i in range(len(path)-3):
            edge1= (path[i], path[i+1])
            for j in range(i+2, len(path)-1):
                edge2 = (path[j], path[j+1])
                if do_intersect(edge1, edge2):
                    path = reverse_sub_path(path, i+1, j)
                    no_improvement = False
                    break
            if no_improvement==False:
                break
    return path


def one_op_improvement_basic(path):
    no_improvement = False
    while no_improvement==False:
        no_improvement=True
        for i in range(1, len(path)-1):
            prev, curr, next = path[i-1:i+2]
            old_cost = cartesian(prev, curr)+cartesian(curr,next) - cartesian(prev,next)
            temp_path = path[:i] + path[i + 1:]
            for j in range(len(temp_path) - 1):
                if j==i-1:
                    continue
                new_cost = cartesian(temp_path[j], curr) + cartesian(curr, temp_path[j + 1]) - cartesian(temp_path[j], temp_path[j + 1])
                if new_cost*1.000001<old_cost:  # Prevents false replacement due to numerical error
                    new_path = temp_path[:j + 1] + [curr] + temp_path[j + 1:]
                    path = new_path
                    no_improvement = False

                    break

            if no_improvement==False:
                break

    return path


def min_k(l, k):
    mins = []
    for _ in range(k):
        new_min = min(l)
        mins.append(new_min)
        l.remove(new_min)
    return mins


def exchange_inside_path(path, i, j):
    # not in place
    if i==j:
        return path
    if i>j:
        temp = i
        i=j
        j=temp
    new_path = path[:i] + [path[j]] + path[i+1:j] + [path[i]] + path[j+1:]

    return new_path


def double_dict(d, k=2, dict_to_put_into=None, station = NORMALIZED_CHARGE_STATION[0]):
    new_d = dict() if dict_to_put_into == None else dict_to_put_into
    for key in d.keys():
        if key==station:
            continue
        for i in range(k):
            new_d[(key, i)] = d[key]
    return new_d


def flat_path(path):
    if len(path)>0 and type(path[0])==list:
        return [flat_path(sub_path) for sub_path in path]
    new_path = [location[0] for location in path]
    return new_path


def flat_dict(d, return_k=False):
    new_d = dict()
    largest = 0
    for key in d.keys():
            new_d[key[0]] = d[key]
            if key[1]>largest:
                largest = key[1]

    if return_k:
        return new_d, largest
    return new_d


def last_index_of(l, v):
    for i in range(len(l) - 1, -1, -1):
        if l[i] == v:
            return i
    return -1


def top_k_nodes(data, k, depot):

    distance_limit = MAXIMUM_SORTIE_TIME[0] * DRONE_SPEED[0]

    eligible = {
        node: value
        for node, value in data.items()
        if node != depot and cartesian(depot, node) + cartesian(node, depot) < distance_limit
    }

    top_nodes = sorted(
        eligible.items(),
        key=lambda x: x[1],
        reverse=True
    )[:k]

    result = dict(top_nodes)

    # Always include the depot
    result[depot] = 0

    nodes = [depot] + list(result.keys() - {depot})
    NODES[0] = nodes

    return result