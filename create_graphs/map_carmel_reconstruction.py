from numpy import asarray, ndarray
from PIL import Image
import os

from configuration import *

# Return matrix of pixels as grayscale, given image name

def separate_matrices(array):
    new_shape = (array.shape[0], array.shape[1])

    array1 = ndarray(new_shape)
    array2 = ndarray(new_shape)
    array3 = ndarray(new_shape)
    arrays = (array1, array2, array3)


    for i in range(new_shape[0]):
        for j in range(new_shape[1]):
            for k in range(3):
                arrays[k][i][j] = array[i][j][k]

    return arrays


def get_figure_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    figure_full_path = os.path.join(current_dir, map_carmel_name)
    return figure_full_path


def get_RGB():
    img = Image.open(get_figure_path())
    img = asarray(img)

    arrays = separate_matrices(img)

    return arrays


COLOUR_GROUPS_IDENTIFY = {
    "gray blue": [-14561/375911, -71/375911, -14700/375911, 3151968/375911],
    "red yellow": [1696/133995, -4/133995, 86/26799, -82003/44665],
    "green": [1859/20277, 409/40554, 1475/20277, -510106/20277],
}

COLOUR_TO_RISK_INSIDE_GROUP = {
    "red yellow": [-1823 / 4410, -149 / 4410, 1727 / 4410, 46323 / 490],
    "blue": [-207 / 53881, 7717 / 538810, -1253 / 53881, 1691128 / 269405],
    "green": [-3/85, 9/85, -4/85, -103/17]
}


def is_in_group(r,g,b, group_name):
    R_factor, G_factor, B_factor, a = COLOUR_GROUPS_IDENTIFY[group_name]
    return a+r*R_factor+g*G_factor+b*B_factor>0


def boolean_colour_group_map(R,G,B, group_name, negative_flag=False):
    if group_name=="blue":  # Return pixels that are not red-yellow and not gray-blue
        return boolean_colour_group_map(R,G,B, "red yellow", negative_flag=True) * boolean_colour_group_map(R,G,B, "gray blue", negative_flag=True)
    new_pic = ndarray(R.shape)
    for i in range(new_pic.shape[0]):
        for j in range(new_pic.shape[1]):
            new_pic[i][j] = int(is_in_group(R[i][j], G[i][j], B[i][j], group_name))
            if negative_flag:
                new_pic[i][j]=1-new_pic[i][j]
    return new_pic


def boolean_colour_group_map_repaired(R,G,B, group_name, negative_flag=False):
    new_pic = boolean_colour_group_map(R,G,B, group_name, negative_flag=False)
    # "green" is a sub-group of the non-repaired "red yellow" group. The repaired "red yellow" is the outer "red yellow" group minus "green" group.
    if group_name=="red yellow":
        new_pic = new_pic * boolean_colour_group_map(R, G, B, "green", negative_flag=True)
    if group_name=="green":
        new_pic = new_pic * boolean_colour_group_map(R, G, B, "red yellow", negative_flag=False)
    if negative_flag:
        new_pic=1-new_pic
    return new_pic


def paint_inside_group(R,G,B, group_name):
    R_factor, G_factor, B_factor, a = COLOUR_TO_RISK_INSIDE_GROUP[group_name]
    new_pic = ndarray(R.shape)
    for i in range(new_pic.shape[0]):
        for j in range(new_pic.shape[1]):
            r,g,b = R[i][j], G[i][j], B[i][j]
            new_pic[i][j] = a+r*R_factor+g*G_factor+b*B_factor

    return new_pic


def paint_only_group(R,G,B, group_name):
    only_group = boolean_colour_group_map_repaired(R,G,B, group_name)
    inside_group = paint_inside_group(R,G,B, group_name)
    return only_group*inside_group


def norm_matrix(map):
    min_v = map.min()
    max_v = map.max()

    new_map = ndarray(map.shape)
    for i in range(new_map.shape[0]):
        for j in range(new_map.shape[1]):
            new_map[i][j] = (map[i][j]-min_v)/(max_v-min_v)

    return new_map


def cut_negative(map, minimum=0):
    for i in range(map.shape[0]):
        for j in range(map.shape[1]):
            map[i][j] = max(map[i][j], minimum)


def cut_positive(map, maximum=16):
    for i in range(map.shape[0]):
        for j in range(map.shape[1]):
            map[i][j] = min(map[i][j], maximum)


def soft_cut_positive(map, maximum=16):
    for i in range(map.shape[0]):
        for j in range(map.shape[1]):
            if map[i][j]>maximum:
                map[i][j] = map[i-1][j-1]


def scale_color(arrays):
    R, G, B = arrays

    new_pic = paint_only_group(R,G,B, "blue")+paint_only_group(R,G,B, "red yellow")+paint_only_group(R,G,B, "green")
    cut_negative(new_pic)
    soft_cut_positive(new_pic, 17)
    soft_cut_positive(new_pic)
    new_pic*=boolean_colour_group_map(R,G,B, "gray blue", negative_flag=True)  # Remove gray-blue (no-risk areas)
    return new_pic


def get_map(outbreak=False):
    prob_unit = P_OUTBREAK if outbreak else P_APRIORI
    return scale_color(get_RGB())*prob_unit