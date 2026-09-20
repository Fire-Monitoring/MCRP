from configuration import *

configurations_for_cgw = {
    "default": [10, [0.1, 0.05], 20, 30, 0.99],
    "quick": [10, [0.05], 1, 1, 0.99]
}

configurations_for_ez = {   # single_time_value, relative_time_flag, penalty_version, n_improves, n_tails
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

configurations_for_myls = {
    "a/5": [1800/20],

    "a/20": [1800/20],
    "a/40": [1800/40],
    "a/80": [1800/80],
    "a/160": [1800/160],
    "a/320": [1800/320],

    "10s": [10],

    "step/2": [80.93525179856115/2],
    "step/4": [80.93525179856115/4],
    "step/7": [80.93525179856115/7],
    "step/10": [80.93525179856115/10],

    "bad interval": [80.93525179856115/2.05, 5]
}

configurations_for_myls_ez = {
    "a/5 5": [1800/5, 5],

    "a/20 5": [1800/20, 5],
    "a/40 5": [1800/40, 5],
    "a/50 5": [1800/50, 5],
    "a/80 5": [1800/80, 5],
    "a/160 5": [1800/160, 5],
    "a/320 5": [1800/320, 5],

    "step/2 5": [80.93525179856115/2, 5],
    "step/4 5": [80.93525179856115/4, 5],
    "step/7 5": [80.93525179856115/7, 5],
    "step/10 5": [80.93525179856115/10, 5],

    "bad interval": [80.93525179856115/2.05, 5],
    "bad interval agg": [80.93525179856115*3.95, 5],
}


configurations_for_myls_ez = {
    "a/5 5": [1800/5, 5],

    "a/20 5": [1800/20, 5],
    "a/40 5": [1800/40, 5],
    "a/50 5": [1800/50, 5],
    "a/80 5": [1800/80, 5],
    "a/160 5": [1800/160, 5],
    "a/320 5": [1800/320, 5],

    "step/2 5": [80.93525179856115/2, 5],
    "step/4 5": [80.93525179856115/4, 5],
    "step/7 5": [80.93525179856115/7, 5],
    "step/10 5": [80.93525179856115/10, 5],

    "bad interval": [80.93525179856115/2.05, 5],
    "bad interval agg": [80.93525179856115*3.95, 5],
}


configurations_for_myls_beam = {
    "a/40 10": [1800/40, 10, "self"],
    "a/80 10": [1800/80, 10, "self"],
}


configurations_for_myls_ez_beam = {
    "a/20 10 5": [1800/20, 10, "self", 5],
    "a/20 100 5": [1800/20, 100, "self", 5],
    "a/40 10 5": [1800/40, 10, "self", 5],
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


alg_configurations = {"cgw": configurations_for_cgw,
                      "cgw simultaneous": configurations_for_cgw,
                      "ez": configurations_for_ez,
                      "ez reorder": configurations_for_ez,
                      "myls": configurations_for_myls,
                      "iterative myls": configurations_for_myls,
                      "myls ez": configurations_for_myls_ez,
                      "myls ez multi visits": configurations_for_myls_ez,
                      "myls multi visits": configurations_for_myls,
                      "myls beam": configurations_for_myls_beam,
                      "myls ez beam": configurations_for_myls_ez_beam,
                      "lns": configurations_for_lns,
                      "choose path": {"default": None}}