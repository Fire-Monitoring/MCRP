"""
Compact exact Gurobi optimizer for the time-dependent OP.

Expected globals already defined/imported by the calling script:

    N
    NODES
    MAP_OUTBREAK
    PIXEL_WIDTH
    DRONE_SPEED
    K
    T
    cartesian(i, j)

Node indexing:
    0 = depot
    1,...,N = selected monitoring nodes for the current graph.

The runtime mapping from selected graph nodes to the original map is already
reflected in NODES[0], so this optimizer only uses the reduced indices 0..N.

Visit value:
    V_i(t) = pb(i) / 2 * dt * (2*T - dt)

where

    dt = min(T, time_to_next_visit, time_to_end_of_mission).

The formulation uses a backward "time until next visit" state. This avoids
creating a variable for every pair of route positions.

Because

    V_i(dt) = pb(i) * (T*dt - dt^2/2)

is concave and increasing for 0 <= dt <= T, the model can maximize the
quadratic objective directly as a convex MIQP (maximization of a concave
quadratic objective). No binary expansion of dt is required.
"""

import math
import gurobipy as gp
from gurobipy import GRB
from Util.util import *
from Util.map_functions import *
import pickle
import json


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

N_SORTIES = 5
MAP_INDEX = 0
N_NODES = 20

DEPOT = 0

# None = use a safe bound calculated from the actual reduced graph.
# You can set this to a smaller value only if you know it is safe.
MAX_POSITIONS_PER_SORTIE = None

TIME_LIMIT = None
MIP_GAP = 0.0
MIP_GAP_ABS = 1e-9
OUTPUT_FLAG = 1

T = TIME_TO_MAX_RISK
K = MAXIMUM_SORTIE_TIME[0]

# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------

def _prepare_data():
    n_nodes = N_NODES + 1

    create_map((MAP_INDEX, N_NODES), None, None)

    if len(NODES[0]) < n_nodes:
        raise ValueError(
            f"NODES[0] contains {len(NODES[0])} nodes, but N={N_NODES} "
            f"requires {n_nodes} nodes indexed 0..N."
        )

    if len(MAP_OUTBREAK[0]) < n_nodes:
        raise ValueError(
            f"MAP_OUTBREAK[0] contains {len(MAP_OUTBREAK[0])} values, "
            f"but N={N_NODES} requires {n_nodes} nodes."
        )

    speed = float(DRONE_SPEED[0])
    if speed <= 0:
        raise ValueError("DRONE_SPEED[0] must be positive.")

    K_int = int(K)
    T_int = int(T)

    if K_int != K:
        raise ValueError("K must be an integer number of seconds.")

    if T_int != T:
        raise ValueError("T must be an integer number of seconds.")

    if K_int <= 0:
        raise ValueError("K must be positive.")

    if T_int <= 0:
        raise ValueError("T must be positive.")

    mission_end = N_SORTIES * K_int

    travel_time = [[0] * n_nodes for _ in range(n_nodes)]

    for i in range(n_nodes):
        for j in range(n_nodes):
            if i == j:
                travel_time[i][j] = 0
            else:
                travel_time[i][j] = int(
                    math.ceil(cartesian_by_indices(i, j) / speed)
                )

    pb = [float(MAP_OUTBREAK[0][NODES[0][i]]) for i in range(n_nodes)]
    pb[DEPOT] = 0.0

    monitoring_nodes = [
        i for i in range(n_nodes)
        if i != DEPOT and pb[i] > 0
    ]

    if not monitoring_nodes:
        raise ValueError("There are no positive-profit monitoring nodes.")

    return (
        n_nodes,
        K_int,
        T_int,
        mission_end,
        travel_time,
        pb,
        monitoring_nodes,
    )


def _get_safe_position_bound(n_nodes, travel_time, K_int):
    """
    Safe number of route positions per sortie.

    A monitoring-node transition always takes at least the shortest positive
    travel time. Self transitions i->i are not allowed for monitoring nodes.
    The depot->depot transition is allowed only to represent waiting after
    the drone has returned.

    A sortie can contain at most floor(K / min_travel) travel legs, hence
    at most that many + 1 route positions.
    """

    positive_times = [
        travel_time[i][j]
        for i in range(n_nodes)
        for j in range(n_nodes)
        if i != j and travel_time[i][j] > 0
    ]

    if not positive_times:
        raise ValueError("Could not determine a positive travel time.")

    min_travel = min(positive_times)
    max_legs = K_int // min_travel

    return max_legs + 1, min_travel


# ---------------------------------------------------------------------------
# Exact solver
# ---------------------------------------------------------------------------

def solve_exact_op():
    (
        n_nodes,
        K_int,
        T_int,
        mission_end,
        travel_time,
        pb,
        monitoring_nodes,
    ) = _prepare_data()

    safe_P, min_travel = _get_safe_position_bound(
        n_nodes,
        travel_time,
        K_int,
    )

    if MAX_POSITIONS_PER_SORTIE is None:
        P = safe_P
    else:
        P = int(MAX_POSITIONS_PER_SORTIE)

        if P < 2:
            raise ValueError(
                "MAX_POSITIONS_PER_SORTIE must be at least 2."
            )

        if P < safe_P:
            raise ValueError(
                f"MAX_POSITIONS_PER_SORTIE={P} is not a safe bound. "
                f"The calculated safe bound is {safe_P}."
            )

    model = gp.Model("exact_time_dependent_OP")

    model.Params.OutputFlag = OUTPUT_FLAG
    model.Params.MIPGap = MIP_GAP
    model.Params.MIPGapAbs = MIP_GAP_ABS

    if TIME_LIMIT is not None:
        model.Params.TimeLimit = TIME_LIMIT

    # -----------------------------------------------------------------------
    # Route variables
    # -----------------------------------------------------------------------

    # x[s,k,i] = 1 if route position k of sortie s is node i.
    x = model.addVars(
        N_SORTIES,
        P,
        n_nodes,
        vtype=GRB.BINARY,
        name="x",
    )

    # y[s,k,i,j] = 1 if the transition from position k to k+1 is i -> j.
    # Monitoring-node self transitions are excluded.
    arcs = [
        (i, j)
        for i in range(n_nodes)
        for j in range(n_nodes)
        if i != j or i == DEPOT
    ]

    y = model.addVars(
        N_SORTIES,
        P - 1,
        arcs,
        vtype=GRB.BINARY,
        name="y",
    )

    # t[s,k] = arrival time at position k, relative to sortie start.
    t = model.addVars(
        N_SORTIES,
        P,
        vtype=GRB.INTEGER,
        lb=0,
        ub=K_int,
        name="t",
    )

    # -----------------------------------------------------------------------
    # Backward next-visit state
    # -----------------------------------------------------------------------

    # next_time[s,k,i] =
    #
    #   time from position (s,k) until the next visit to i at or after
    #   position (s,k).
    #
    # Therefore:
    #
    #   x[s,k,i] = 1  => next_time[s,k,i] = 0
    #
    # Otherwise:
    #
    #   next_time[s,k,i] =
    #       travel_time(k,k+1) + next_time[s,k+1,i]
    #
    # This is the key compact representation of the future dependence.
    next_time = model.addVars(
        N_SORTIES,
        P,
        monitoring_nodes,
        vtype=GRB.INTEGER,
        lb=0,
        ub=mission_end,
        name="next_time",
    )

    # dt[s,k,i] is the value-determining interval for a visit to i at
    # position (s,k).
    dt = model.addVars(
        N_SORTIES,
        P - 1,
        monitoring_nodes,
        vtype=GRB.INTEGER,
        lb=0,
        ub=T_int,
        name="dt",
    )

    # -----------------------------------------------------------------------
    # Route structure
    # -----------------------------------------------------------------------

    for s in range(N_SORTIES):

        # Every sortie starts at the depot.
        model.addConstr(
            x[s, 0, DEPOT] == 1,
            name=f"start_depot_{s}",
        )

        # The final route position is the depot.
        model.addConstr(
            x[s, P - 1, DEPOT] == 1,
            name=f"end_depot_{s}",
        )

        # One node per route position.
        for k in range(P):
            model.addConstr(
                gp.quicksum(x[s, k, i] for i in range(n_nodes)) == 1,
                name=f"one_node_{s}_{k}",
            )

        # Once the drone reaches the depot after the sortie, all remaining
        # route positions are depot positions. These positions represent
        # waiting at the depot.
        for k in range(1, P - 1):
            model.addConstr(
                x[s, k, DEPOT] <= x[s, k + 1, DEPOT],
                name=f"depot_absorbing_{s}_{k}",
            )

        # Exactly one transition between consecutive positions.
        for k in range(P - 1):

            model.addConstr(
                gp.quicksum(y[s, k, i, j] for i, j in arcs) == 1,
                name=f"one_arc_{s}_{k}",
            )

            for i, j in arcs:
                model.addConstr(
                    y[s, k, i, j] <= x[s, k, i],
                    name=f"arc_from_{s}_{k}_{i}_{j}",
                )

                model.addConstr(
                    y[s, k, i, j] <= x[s, k + 1, j],
                    name=f"arc_to_{s}_{k}_{i}_{j}",
                )

        # Exact arrival times. No waiting is permitted between nodes.
        for k in range(P - 1):

            travel_expr = gp.quicksum(
                travel_time[i][j] * y[s, k, i, j]
                for i, j in arcs
            )

            model.addConstr(
                t[s, k + 1] == t[s, k] + travel_expr,
                name=f"arrival_time_{s}_{k}",
            )

        model.addConstr(
            t[s, P - 1] <= K_int,
            name=f"sortie_duration_{s}",
        )

        model.addConstr(
            t[s, 0] == 0,
            name=f"sortie_start_time_{s}",
        )

    # -----------------------------------------------------------------------
    # Backward next-visit recurrence
    # -----------------------------------------------------------------------

    BIG_M = mission_end + K_int + 1

    for s in range(N_SORTIES):
        for k in range(P - 1):

            transition_time = gp.quicksum(
                travel_time[i][j] * y[s, k, i, j]
                for i, j in arcs
            )

            for i in monitoring_nodes:

                # If the current position visits i, the next visit at-or-after
                # this position is now, so next_time = 0.
                model.addConstr(
                    next_time[s, k, i]
                    <= BIG_M * (1 - x[s, k, i]),
                    name=f"next_zero_{s}_{k}_{i}",
                )

                # If the current position is not i, the next visit is found
                # by moving to the next route position.
                model.addConstr(
                    next_time[s, k, i]
                    >= transition_time
                    + next_time[s, k + 1, i]
                    - BIG_M * x[s, k, i],
                    name=f"next_lower_{s}_{k}_{i}",
                )

                model.addConstr(
                    next_time[s, k, i]
                    <= transition_time
                    + next_time[s, k + 1, i]
                    + BIG_M * x[s, k, i],
                    name=f"next_upper_{s}_{k}_{i}",
                )

    # At the end of a sortie, continue counting through the waiting time at
    # the depot and then into the next sortie.
    for s in range(N_SORTIES - 1):
        for i in monitoring_nodes:
            model.addConstr(
                next_time[s, P - 1, i]
                ==
                (K_int - t[s, P - 1])
                + next_time[s + 1, 0, i],
                name=f"next_across_sorties_{s}_{i}",
            )

    # After the final sortie, the next event for a node that is not visited
    # again is the end of the mission.
    for i in monitoring_nodes:
        model.addConstr(
            next_time[N_SORTIES - 1, P - 1, i]
            ==
            K_int - t[N_SORTIES - 1, P - 1],
            name=f"next_mission_end_{i}",
        )

    # -----------------------------------------------------------------------
    # dt and objective
    # -----------------------------------------------------------------------

    objective = gp.QuadExpr()

    for s in range(N_SORTIES):
        for k in range(P - 1):

            transition_time = gp.quicksum(
                travel_time[i][j] * y[s, k, i, j]
                for i, j in arcs
            )

            for i in monitoring_nodes:

                # dt is relevant only when position (s,k) actually visits i.
                model.addConstr(
                    dt[s, k, i] <= T_int * x[s, k, i],
                    name=f"dt_only_if_visit_{s}_{k}_{i}",
                )

                # Time from the current position to the next visit to i.
                #
                # If x[s,k,i]=1, next_time[s,k+1,i] describes the next visit
                # strictly after the current position.
                #
                # If the next visit is in a later sortie, the boundary
                # recurrence has already included the depot waiting time.
                next_gap = (
                    transition_time
                    + next_time[s, k + 1, i]
                )

                model.addConstr(
                    dt[s, k, i]
                    <= next_gap
                    + BIG_M * (1 - x[s, k, i]),
                    name=f"dt_next_visit_{s}_{k}_{i}",
                )

                # Exact objective:
                #
                #   pb/2 * dt * (2T-dt)
                # = pb*T*dt - pb/2*dt^2.
                #
                # Since 0 <= dt <= T, this function is increasing.
                # Therefore the maximization automatically makes dt equal
                # to the required minimum.
                objective.add(
                    pb[i] * T_int * dt[s, k, i]
                    - 0.5 * pb[i] * dt[s, k, i] * dt[s, k, i]
                )

    model.setObjective(objective, GRB.MAXIMIZE)

    # -----------------------------------------------------------------------
    # Solve
    # -----------------------------------------------------------------------

    print()
    print("Exact OP model")
    print("--------------")
    print(f"Nodes:                         {n_nodes}")
    print(f"Monitoring nodes:              {len(monitoring_nodes)}")
    print(f"Sorties:                       {N_SORTIES}")
    print(f"K:                             {K_int}")
    print(f"T:                             {T_int}")
    print(f"Mission duration:              {mission_end}")
    print(f"Shortest positive travel time: {min_travel}")
    print(f"Positions per sortie:          {P}")
    print()

    model.update()

    print(f"Variables:   {model.NumVars:,}")
    print(f"Constraints: {model.NumConstrs:,}")
    print()
    print("Starting Gurobi...")
    print()

    model.optimize()

    # -----------------------------------------------------------------------
    # Status
    # -----------------------------------------------------------------------

    if model.Status == GRB.INFEASIBLE:
        model.computeIIS()
        model.write("exact_OP_infeasible.ilp")
        raise RuntimeError(
            "The exact OP model is infeasible. "
            "IIS written to exact_OP_infeasible.ilp."
        )

    if model.Status == GRB.UNBOUNDED:
        raise RuntimeError("The exact OP model is unbounded.")

    if model.SolCount == 0:
        raise RuntimeError(
            f"Gurobi finished with status {model.Status} and found no solution."
        )

    # -----------------------------------------------------------------------
    # Extract routes
    # -----------------------------------------------------------------------

    routes = []
    visit_times = []

    for s in range(N_SORTIES):

        route = []
        visits = []

        for k in range(P):

            chosen_node = max(
                range(n_nodes),
                key=lambda i: x[s, k, i].X,
            )

            local_time = int(round(t[s, k].X))
            global_time = s * K_int + local_time

            route.append((chosen_node, global_time))

            if (
                chosen_node != DEPOT
                and k < P - 1
            ):
                visits.append(
                    {
                        "node": chosen_node,
                        "time": global_time,
                        "sortie": s,
                        "position": k,
                    }
                )

            # Once the route has returned to the depot, later positions are
            # only waiting positions and do not need to be printed.
            if k > 0 and chosen_node == DEPOT:
                break

        routes.append(route)
        visit_times.append(visits)

    # -----------------------------------------------------------------------
    # Recompute the objective independently
    # -----------------------------------------------------------------------

    all_visits = []

    for visits in visit_times:
        all_visits.extend(visits)

    all_visits.sort(key=lambda v: v["time"])

    by_node = {i: [] for i in monitoring_nodes}

    for v in all_visits:
        by_node[v["node"]].append(v["time"])

    verified_objective = 0.0
    visit_details = []

    for i in monitoring_nodes:

        times = by_node[i]

        for q, current_time in enumerate(times):

            if q + 1 < len(times):
                next_visit_time = times[q + 1]
            else:
                next_visit_time = mission_end

            raw_dt = next_visit_time - current_time
            dt_value = min(T_int, raw_dt)

            value = (
                pb[i]
                * dt_value
                * (2.0 * T_int - dt_value)
                / 2.0
            )

            verified_objective += value

            visit_details.append(
                {
                    "node": i,
                    "time": current_time,
                    "next_visit_time": (
                        times[q + 1]
                        if q + 1 < len(times)
                        else None
                    ),
                    "dt": dt_value,
                    "value": value,
                }
            )

    # -----------------------------------------------------------------------
    # Output
    # -----------------------------------------------------------------------

    print()
    print("========== RESULT ==========")

    print("Path by order:")
    for s, route in enumerate(routes, start=1):
        nodes = [node for node, _ in route]
        print(f"Sortie {s}: {nodes}")

    print()
    print(f"Total profit:       {model.ObjVal:.12g}")
    print(f"Verified profit:    {verified_objective:.12g}")
    print(f"Runtime:             {model.Runtime:.6f} seconds")
    print(f"MIP gap:             {model.MIPGap:.12g}")

    if abs(model.ObjVal - verified_objective) > 1e-5:
        raise RuntimeError(
            "The independently recomputed objective differs from the "
            "Gurobi objective."
        )

    if model.Status == GRB.OPTIMAL:
        print("Optimality:          PROVEN")
    else:
        print("Optimality:          NOT PROVEN")

    # -----------------------------------------------------------------------
    # Return result dictionary
    # -----------------------------------------------------------------------

    result = {
        "status": int(model.Status),
        "objective": float(model.ObjVal),
        "verified_objective": float(verified_objective),
        "runtime": float(model.Runtime),
        "mip_gap": float(model.MIPGap),
        "routes": routes,
        "visit_times": visit_times,
        "visit_details": visit_details,
        "travel_time": travel_time,
        "positions_per_sortie": P,
        "safe_positions_per_sortie": safe_P,
        "mission_end": mission_end,
        "n_nodes": n_nodes,
        "T": T_int,
        "K": K_int,
        "depot": DEPOT,
        "model": model,
    }

    return result


# ---------------------------------------------------------------------------
# Optional direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = solve_exact_op()
    print("\n========== RESULT ==========")

    print("Path by order:")
    for sortie_num, route in enumerate(result["routes"], start=1):
        nodes = [node for node, time in route]
        print(f"Sortie {sortie_num}: {nodes}")

    print(f"\nTotal profit: {result['objective']:.6f}")
    print(f"Runtime:      {result['runtime']:.3f} seconds")
    print(f"MIP gap:      {result['mip_gap']:.6g}")

    # Complete result
    with open(f"exact_OP_result_{MAP_INDEX}_{N_NODES}.pkl", "wb") as f:
        pickle.dump(result, f)

    # Human-readable result
    summary = {
        "objective": result["objective"],
        "verified_objective": result["verified_objective"],
        "runtime_seconds": result["runtime"],
        "mip_gap": result["mip_gap"],
        "routes": result["routes"],
        "visit_details": result["visit_details"],
        "positions_per_sortie": result["positions_per_sortie"],
        "mission_end": result["mission_end"],
    }

    with open("exact_OP_result_{MAP_INDEX}_{N_NODES}.json", "w") as f:
        json.dump(summary, f, indent=2)


