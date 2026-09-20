import time

from Util.util import *
import numpy as np
import matplotlib.pyplot as plt


def env_of_point(p, radius, M):
    radius_in_pixels = int(radius / PIXEL_WIDTH[0])
    neighbors = []
    y, x = p
    value = 0
    for i in range(-radius_in_pixels, radius_in_pixels+1):
        for j in range(-radius_in_pixels, radius_in_pixels+1):
            neighbor = (y+i, x+j)
            if neighbor in M and cartesian(neighbor, p)<=radius:
                neighbors.append(neighbor)
                value+=M[neighbor]
    return neighbors, value


def env_of_points(M, radius):
    points_env = dict()  # {point: (neighbors, value)}
    relevant_points = list(M.keys())

    for point in relevant_points:
        points_env[point] = env_of_point(point, radius, M)

    return points_env, relevant_points


def relevant_env(env, covered_points):
    return set(env).isdisjoint(covered_points)


def find_next_max_point_env(points_env, relevant_points, covered_points):
    max_point = None

    for point in relevant_points:
        neighbors, value = points_env[point]
        if not relevant_env(neighbors, covered_points):
            continue
        if max_point==None or value>max_point[1]:
            max_point = (point, value)

    return max_point


def update_relevant(points_env, relevant_points, new_center):
    env = points_env[new_center][0]
    env_border = find_border(env)
    points_to_remove = set()
    for point in env_border:
        point_env = set(points_env[point][0])
        points_to_remove.update(point_env)

    relevant_points[:] = [p for p in relevant_points if p not in points_to_remove]


def determine_all_centers(M, radius):
    points_env, original_points = env_of_points(M, radius)
    relevant_points = copy.deepcopy(original_points)
    covered_points = set()

    neighborhoods = dict()  # {point: (neighbors, value)}
    max_point = find_next_max_point_env(points_env, relevant_points, covered_points)

    while max_point is not None:
        point = max_point[0]
        neighbors, value = points_env[point]
        covered_points|=set(neighbors)
        covered_points.add(point)
        neighborhoods[point] = (neighbors, value)
        update_relevant(points_env, relevant_points, point)

        max_point = find_next_max_point_env(points_env, relevant_points, covered_points)
    uncovered_points = list(set(original_points)-covered_points)
    return neighborhoods, uncovered_points, points_env


def assign_uncovered_points(neighborhoods, uncovered_points, M):
    for point in uncovered_points:
        closest_center = None
        for center in neighborhoods.keys():
            dist = cartesian(point, center)
            if closest_center is None or dist<closest_center[1]:
                closest_center = (center, dist)
        new_neighborhood = neighborhoods[closest_center[0]][0] + [point]
        new_value = neighborhoods[closest_center[0]][1] + M[point]
        neighborhoods[closest_center[0]] = (new_neighborhood, new_value)


def in_border(point, group):
    i, j = point
    up, right, down, left = (i-1, j), (i, j+1), (i+1, j), (i, j-1)
    return up not in group or right not in group or down not in group or left not in group


def is_isolated(point, group):
    i, j = point
    up, right, down, left = (i-1, j), (i, j+1), (i+1, j), (i, j-1)
    return up not in group and right not in group and down not in group and left not in group


def find_one_point_in_border(group):
    for point in group:
        if in_border(point, group):
            return point


def find_next_border_point(point, group, from_nbr = None):
    i, j = point
    neighbors = [(i - 1, j), (i - 1, j + 1), (i, j + 1), (i + 1, j + 1), (i + 1, j), (i + 1, j - 1), (i, j - 1), (i - 1, j - 1)]
    if from_nbr is not None:
        h = neighbors.index(from_nbr)
        neighbors = neighbors[h+1:] + neighbors[:h+1]
    for k in range(8):
        if neighbors[k] in group and neighbors[k-1] not in group:
            return neighbors[k]


IN_4 = [False]

def find_border(group):
    first_point = find_one_point_in_border(group)
    border = [first_point]

    if is_isolated(first_point, group):
        return border

    prev_prev = None
    prev_point = first_point
    next_point = None

    while next_point!=first_point:
        next_point = find_next_border_point(prev_point, group, prev_prev)
        border.append(next_point)
        prev_prev = prev_point
        prev_point = next_point

    return border


def perimeter(group):
    border = find_border(group)
    length = 0
    for i in range(len(border)):
        length+=cartesian(border[i-1], border[i])
    return length


# OLD
# def inner_points(group, points_env):
#     inner_list = []
#     for point in group:
#         neighbors = points_env[point][0]
#         outer_neighbors = set(neighbors)-set(group)
#         if len(outer_neighbors)==0:
#             inner_list.append(point)
#     return inner_list


def find_inner_border(outer_border, center, points_env):
    inner_border = []
    for point in outer_border:
        point_env = points_env[point][0]
        closest_to_center = min(point_env, key=lambda p: simple_cartesian(p, center))
        if len(inner_border)>0 and closest_to_center==inner_border[-1]:
            continue
        inner_border.append(closest_to_center)
    return inner_border


def border_length(border):
    length = 0
    for i in range(len(border)):
        length += cartesian(border[i - 1], border[i])
    return length


def orient(a, b, c):
    """2D orientation (cross product sign)."""
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def polygon_orientation(points):
    area2 = 0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area2 += x1 * y2 - x2 * y1
    return 1 if area2 > 0 else -1   # +1 = CCW, -1 = CW


def make_polygon_convex(points):
    """
    points: ordered vertices of a simple polygon (CW or CCW)

    Returns:
        Ordered vertices of the convex hull,
        obtained only by removing vertices.
    """
    P = list(points)
    if len(P) < 3:
        return P

    poly_sign = polygon_orientation(P)

    changed = True
    while changed and len(P) >= 3:
        changed = False
        n = len(P)
        to_remove = []

        for i in range(n):
            a = P[i - 1]
            b = P[i]
            c = P[(i + 1) % n]

            turn = orient(a, b, c)

            # reflex (concave) vertex
            if turn * poly_sign < 0:
                to_remove.append(i)

        if to_remove:
            changed = True
            for i in reversed(to_remove):
                P.pop(i)

    print(points, P)

    return P


def map_to_graph(M, radius, remove_zeroes=True):
    # return: graph, original_neighborhoods
    print("stage 1")
    neighborhoods, uncovered_points, points_env = determine_all_centers(M, radius)
    print("stage 2")
    original_neighborhoods = copy.deepcopy(neighborhoods)  # for plotting
    print("stage 3")
    assign_uncovered_points(neighborhoods, uncovered_points, M)

    # compute inner perimeter
    to_delete = []
    for center in neighborhoods.keys():
        neighbors, value = neighborhoods[center]
        outer_border = find_border(neighbors)               # outer border
        print("outer border", outer_border)
        inner_border = find_inner_border(outer_border, center, points_env)      # inner border
        print("inner border", inner_border)
        inner_border = make_polygon_convex(inner_border)    # convex, for minimizing
        inner_perimeter = border_length(inner_border)       # length
        if value>0 or not remove_zeroes:
            neighborhoods[center] = (neighbors, value, inner_perimeter)
        else:
            to_delete.append(center)

    for center in to_delete:
        del neighborhoods[center]

    print("Graph size =", len(neighborhoods))
    return neighborhoods, original_neighborhoods


# print the graph

def plot_borders(M, neighborhoods, original_neighborhoods, text):
    c = list(neighborhoods.keys())
    b = []
    inner_points = []
    for center in c:
        neighbors, _, _ = neighborhoods[center]
        border = find_border(neighbors)
        b+=border
        inner_neighborhood, _ = original_neighborhoods[center]
        inner_points+=inner_neighborhood

    plot_map_with_borders(M, b, c, text=text)
    plot_map_with_borders(inner_points, b, c, map_flag=False, text=text)


def plot_map_with_borders(M, b, c, map_flag=True, text=""):
    circle_size = 1

    if map_flag:
        ys = [p[0] for p in M.keys()]
        xs = [p[1] for p in M.keys()]

        min_y, max_y = min(ys), max(ys)
        min_x, max_x = min(xs), max(xs)

        height = max_y - min_y + 1
        width = max_x - min_x + 1

        # Build image array
        img = np.full((height, width), np.nan)

        for (y, x), value in M.items():
            img[y - min_y, x - min_x] = value

        plt.figure(figsize=(6, 6))

        # 1. Plot scalar map
        plt.imshow(img, cmap="gray", origin="upper")
        file_name = f"map_with_borders__{text}.png"

        # 2. Plot b points (blue pixels)
        if b:
            by = [p[0] - min_y for p in b]
            bx = [p[1] - min_x for p in b]
            plt.scatter(bx, by, c="blue", s=0.6, marker="s")

    else:
        b_set = set(b)
        c_set = set(c)

        # Background points: r minus (b ∪ c)
        M_bg = [p for p in M if p not in b_set and p not in c_set]

        plt.figure(figsize=(6, 6))

        # 1. Plot background (gray)
        if M_bg:
            My = [p[0] for p in M_bg]
            Mx = [p[1] for p in M_bg]
            plt.scatter(Mx, My, c="gray", s=1, marker="s")

        min_y = 0
        min_x = 0

        file_name = f"borders_with_radius__{text}"

    # 3. Plot c points (red circles)
    if c:
        cy = [p[0] - min_y for p in c]
        cx = [p[1] - min_x for p in c]
        plt.scatter(cx, cy, facecolors="none", edgecolors="red",
                    s=circle_size, linewidths=1)

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(file_name)
    plt.clf()





