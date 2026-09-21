from configuration import *

configurations_for_three_phase = {
    "nn 1": [1, 1, "nn"],
    "mm 1": [1, 1, "mm"],
    "nn 2": [1, 2, "nn"],
    "mm 2": [1, 2, "mm"],
    "mm 5": [1, 5, "mm"],
    "nn 5": [1, 5, "nn"],
    "mm 10": [1, 10, "mm"],
    "mn 10": [1, 10, "mn"],
    "nn 10": [1, 10, "nn"],
    "nm 10": [1, 10, "nm"],
}

configurations_for_lns = {
    "regular": {
        "temperature": 0.1,
        "cooling": 0.99975,
        "step_size": 50,
        "n_non_imp_to_increase_beta": 1000,
        "eta": 10,
        "max_nbrs": 25,
        "beta": 1,
        "beta_factor": 0.5,
        "max_beta": 15,
        "n_non_imp_to_stop": 100000,
        "max_iterations": 250000,
    },
    "short": {
        "temperature": 0.1,
        "cooling": 0.99975,
        "step_size": 50,
        "n_non_imp_to_increase_beta": 1000,
        "eta": 10,
        "max_nbrs": 25,
        "beta": 1,
        "beta_factor": 0.5,
        "max_beta": 15,
        "n_non_imp_to_stop": 10000,
        "max_iterations": 25000,
    }
}


alg_configurations = {
                      "three phase": configurations_for_three_phase,
                      "lns": configurations_for_lns,
                     }