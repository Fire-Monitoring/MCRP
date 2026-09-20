from maps import *
from Util.map_functions import *

file_name = "full_risks.py"
with open(file_name, 'a') as f:
    f.write("[")

for i in range(70):
    reset_globals()
    create_map(i, None, None)
    risk = sum(MAP_DYNAMIC[0].values())
    with open(file_name, 'a') as f:
        f.write(str(risk))
        f.write(", ")
with open(file_name, 'a') as f:
    f.write("]")

