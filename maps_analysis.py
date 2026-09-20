from Util.util import *
from Util.map_functions import *

# det_map
maps_differences = {0: 0.00599-0.00619,
                    1: 0.00614-0.00633,
                    2: 0.00632-0.00633,
                    3: 0.00625-0.00623,
                    4: 0.00675-0.00678,
                    5: 0.00599-0.00604,
                    6: 0.00641-0.00652,
                    7: 0.00628-0.00653,
                    8: 0.00632-0.00633,
                    9: 0.00595-0.00595}


def score_percentile(map, location):
    y, x = location
    location_factor = int(284 / 15)
    y, x = int(y / location_factor), int(x / location_factor)

    location_value = map[y][x]
    count = 0
    for row in map:
        for val in row:
            if val>=location_value:
                count += 1
    map_size = len(map)*len(map[0])
    return 100*count/map_size


scoring_functions = {"simple": score_percentile}

def plot_difference_and_score(scoring_name, location=CHARGE_STATION[0]):
    X = []
    Y = list(maps_differences.values())
    scoring_function = scoring_functions[scoring_name]
    for map_index in maps_differences.keys():
        map, _ = get_generated_map(map_index)
        score = scoring_function(map, location)
        X.append(score)
    plt.plot(X, Y, 'o', markerfacecolor='blue')
    plt.grid(True)
    plt.show()


plot_difference_and_score("simple", location=CHARGE_STATION[0])