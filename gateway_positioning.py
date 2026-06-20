"""
Script to perform gateway plcament optimization

Authors:
- Cláudio Modesto
- Lucas Mozart
"""

import os
import math
import glob
import argparse
import re
import pathlib
import pandas as pd
import numpy as np
from pyomo.environ import *

parser = argparse.ArgumentParser()

parser.add_argument(
    "--channel-type", "-c", help="Type of channel",
    type=str, required=False, default="sionna"
)

parser.add_argument(
    "--threshold", "-t", help="Threshold in dBm",
    type=float, required=False, default=-110
)

parser.add_argument(
    "--scenario", "-s", help="3D scenario/grid to be used",
    type=str, required=False, default="etoile"
)

args = parser.parse_args()


ROOT_DIR = "results" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}/{args.scenario}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

def _get_path_gain(path_gain_type: str):
    """
    Function to process path gain from .csv files
    """
    path_gain_db = []
    if path_gain_type == "sionna":
        files = sorted(
            glob.glob(f"path_gain_results/{path_gain_type}/{args.scenario}/*.csv"),
            key=lambda x: int(os.path.splitext(os.path.basename(x))[0])
        )
        for fname in files:
            if not os.path.basename(fname).split(".")[0].isdigit():
                continue
            df = pd.read_csv(f"{fname}", header=None)
            path_gain_db.append(df)
    elif path_gain_type == "wix" or path_gain_type == "wif":
        files = sorted(
            glob.glob(f"path_gain_results/{path_gain_type}/{args.scenario}/*.csv"),
            key=lambda x: int(os.path.splitext(os.path.basename(x))[0])
        )
        for fname in files:
            df = pd.read_csv(f"{fname}", header=None)
            path_gain_db.append(df)
    else:
        files = sorted(
            glob.glob(f"path_gain_results/ns3/{path_gain_type}/{args.scenario}/*.csv"),
            key=lambda x: int(os.path.splitext(os.path.basename(x))[0])
        )
        for fname in files:
            df = pd.read_csv(f"{fname}", header=None)
            path_gain_db.append(df)

    return np.array(path_gain_db)

# Defining the numpy seed
np.random.seed(42)

# read CSV
devices_df = pd.read_csv(f"path_gain_results/{args.scenario}_coordinates.csv",
                                            header=None)

# end_device positions -> cell indexes
end_devices_cells = list(zip(devices_df[3], devices_df[4]))

def extract_number(filename):
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else 999999

G = len(devices_df.to_numpy()) # Possibles gateway positions
coordinates = devices_df.to_numpy()

rx_power = {}

path_gain_type = args.channel_type
path_gain_db = _get_path_gain(path_gain_type)
print(path_gain_db.shape)
PATH_GAIN_COLUMN = -1

g_index = list(range(G))
Nd = len(end_devices_cells)
if args.scenario == "etoile":
    d_index = [1, 2, 4, 9, 10, 12, 14, 18,
                19, 20, 22, 23, 26, 27, 28,
                30, 31, 32, 33, 34, 35, 36,
                40, 41, 42, 43, 44, 50, 51,
                52, 53, 54, 55, 59, 60, 61,
                62, 63, 64, 68, 69, 70, 71,
                72, 73, 74, 75, 81, 82, 83,
                86, 87, 91, 98]
elif args.scenario == "canyon":
    d_index = [3, 4, 8, 9, 16, 17, 21, 22, 29,
               30, 34, 35, 39, 40, 41, 42, 43,
               44, 45, 46, 47, 48, 49, 50, 51,
               52, 53, 54, 55, 56, 57, 58, 59,
               60, 61, 62, 63, 64, 68, 69, 73,
               74, 81, 82, 86, 87, 94, 95, 99,
               100]


invalid_d_index = np.zeros(100)
print("Number of ED: ", len(d_index))

for p_gateway in range(G): # Power that a ED receivers from each gateway in all positions available
    for d, (ix, iy) in enumerate(end_devices_cells):
        rx_power[(d, p_gateway)] = float(path_gain_db[p_gateway][d][PATH_GAIN_COLUMN])

print(d_index)

# Solving -inf problem
NO_SIGNAL = -1000

for key, v in list(rx_power.items()):
    if v is None or math.isnan(v) or math.isinf(v):
        rx_power[key] = NO_SIGNAL # NO_SIGNAL replaces -inf values

if args.threshold is None:
    rho = min([x for x in rx_power.values() if x != -1000]) + 20 # threshold in dBm
else:
    rho = args.threshold
print("List of power thresholds: ", rho)

all_received_power = []
all_dev_x, all_dev_y = [], []
all_xs_chosen, all_ys_chosen = [], []

# Defining an cover dict
cover = {}

for d in d_index:
    for p_gateway in g_index:
        # This indicates whether the power threshold is being reached in each
        # end-device for each gateway -> simplification to 0 or 1
        if (d, p_gateway) in rx_power:
            cover[(d, p_gateway)] = 1 if rx_power[(d, p_gateway)] >= rho else 0

# Optimization
model = ConcreteModel()
model.P = Set(initialize=g_index)
model.D = Set(initialize=d_index)

# Cover parameter as shown before
model.cover = Param(model.D, model.P, initialize=cover, within=Binary, default=0)

# Gateway positions (Set or Not)
model.x = Var(model.P, domain=Binary)

def coverage_rule(m, d):
    # At least one gateway must cover each end-device
    return sum(m.cover[d, p_gateway] * m.x[p_gateway] for p_gateway in m.P) >= 1

model.coverage = Constraint(model.D, rule=coverage_rule)

def obj_rule(m):
    """
    Objective function to be optimized
    """
    return sum(m.x[p_gateway] for p_gateway in m.P)

model.obj = Objective(rule=obj_rule, sense=minimize)

# initialize solver parameters
solver = SolverFactory("glpk")
result = solver.solve(model)

received_power = np.zeros(len(g_index))
if (result.solver.status == SolverStatus.ok and
        result.solver.termination_condition == TerminationCondition.optimal):
    # Chosen gateways
    chosen_gateways = [p for p in model.P if value(model.x[p]) > 0.5]

    print("\nChosen gateways (details):")
    for p in chosen_gateways:
        print(f"  p = {p}, coords = {coordinates[p]}")
    for d in d_index:
        total_mW = 0.0
        for p in g_index:
            if (d, p) not in rx_power:
                continue
            if value(model.x[p]) > 0.5:   # chosen gateway
                rp_dbm = rx_power[(d, p)]

                # converting dBm -> mW
                rp_mw = 10**(rp_dbm / 10.0)

                total_mW += rp_mw
        # avoiding problem with log(0)
        if total_mW > 0:
            received_power[d] = 10 * np.log10(total_mW) # back to dBm
        else:
            received_power[d] = NO_SIGNAL # very negative value

    dev_x = devices_df[0].values
    dev_y = devices_df[1].values

    # gateways positions
    xs_gate = [coordinates[p][0] for p in g_index]
    ys_gate = [coordinates[p][1] for p in g_index]

    # end devices positions
    xs_ed = [coordinates[p][0] for p in d_index]
    ys_ed = [coordinates[p][1] for p in d_index]

    # chosen gateways positions
    xs_chosen = [coordinates[p][0] for p in chosen_gateways]
    ys_chosen = [coordinates[p][1] for p in chosen_gateways]

    print("Number of gateways: ", len(xs_chosen))
    # saving receiver power for each end-device
    np.savez(f"{OUTPUT_PATH_NAME}/receiver_power_{path_gain_type}.npz", received_power)
    # saving all position coordinates
    np.savez(f"{OUTPUT_PATH_NAME}/all_position.npz", dev_x, dev_y)
    # saving gateway positioning coordinates
    np.savez(f"{OUTPUT_PATH_NAME}/chosen_position_{path_gain_type}.npz", xs_chosen, ys_chosen)
    # saving end devices positioning coordinates
    np.savez(f"{OUTPUT_PATH_NAME}/ed_position.npz", xs_ed, ys_ed)
    # saving chosen gateways
    np.savez(f"{OUTPUT_PATH_NAME}/chosen_gateways_{path_gain_type}.npz", chosen_gateways)
else:
    print(f"Solver did not find a feasible solution for threshold {rho}")
    print("Status:", result.solver.status)
    print("Termination:", result.solver.termination_condition)
