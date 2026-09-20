from simulations import *
import warnings
import json
warnings.filterwarnings('ignore')

X = range(70)
DEC_PROCEDURE[0] = "future"
alg_name = "deterministic_doubled_path"
file_name = f'future_constant.txt'

DRONE_SPEED[0] = DRONE_SPEED[0]
res_dict = dict()
duration = max(MAXIMUM_SORTIE_TIME[0], TIME_TO_MAX_RISK)*N_SORTIES_IN_MISSION[0]
print("[", end="")
with open(file_name, 'a') as f:
            f.write("[")
speed_results = []
for x in X:
            res = simulate_path(width_of_map_for_dynamic=15, map_name=x, n_steps_or_sorties=1, algorithm_name=alg_name,
                          arguments=["ez", "mm 5", "static", 2, -1], by_steps=False, duration=duration, return_results=True)
            print(f"{res}, ", end="")
            with open(file_name, 'a') as f:
                f.write(str(res))
                f.write(", ")
with open(file_name, 'a') as f:
            f.write("]")
print("]")


