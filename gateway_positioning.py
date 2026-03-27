import os
import glob
import pathlib
import pandas as pd
import numpy as np
import re
import networkx as nx
import matplotlib.pyplot as plt
import math
from pyomo.environ import *
from matplotlib import pyplot as plt
import argparse

parser = argparse.ArgumentParser()

parser.add_argument(
    "--channel-type", "-c", help="Type of channel",
    type=str, required=False, default="sionna"
)

parser.add_argument(
    "--threshold", "-t", help="Threshold in dBm",
    type=float, required=False, default=-110
)

args = parser.parse_args()


ROOT_DIR = "results" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}/figures"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)


def _get_path_gain(path_gain_type: str):
    path_gain_db = []
    if path_gain_type == "sionna":
        files = sorted(glob.glob(f"path_gain_results/{path_gain_type}/*.csv"))
        for fname in files:
            df = pd.read_csv(f"{fname}", header=None)
            path_gain_db.append(df)
    elif path_gain_type == "wix" or path_gain_type == "wif":
        files = sorted(glob.glob(f"path_gain_results/{path_gain_type}/*.csv"))
        for fname in files:
            df = pd.read_csv(f"{fname}", header=None)
            path_gain_db.append(df)
    else:
        files = sorted(glob.glob(f"path_gain_results/ns3/{path_gain_type}/*.csv"))
        for fname in files:
            df = pd.read_csv(f"{fname}", header=None)
            path_gain_db.append(df)

    return np.array(path_gain_db)

def _get_energies(sf: int):
    energies = []
    energies_path = os.path.join("energy_results", f"sf_{sf}", "energies.csv")
    df = pd.read_csv(energies_path, header=None)
    for i in range(len(df)):
        energies.append(df.iloc[i, 1])
    return energies

# Defining the numpy seed
np.random.seed(42)

# read CSV
devices_df = pd.read_csv("path_gain_results/coordinates.csv", header=None)

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
PATH_GAIN_COLUMN = -1

G_index = list(range(G))       # 0..G-1
Nd = len(end_devices_cells)
D_index = [1, 2, 4, 9, 10, 12, 14, 18, 19, 20, 22, 23, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 40, 41, 42, 43, 44, 50, 51, 52, 53, 54, 55, 59, 60, 61, 62, 63, 64, 68, 69, 70, 71, 72, 73, 74, 75, 81, 82, 83, 86, 87, 91, 98]
invalid_d_index = np.zeros(100)

print("Number of ED: ", len(D_index))

for p_gateway in range(G): # Power that a ED receivers from each gateway in all positions available
    for d, (ix, iy) in enumerate(end_devices_cells):             
        rx_power[(d, p_gateway)] = float(path_gain_db[p_gateway][d][PATH_GAIN_COLUMN])

print("Number of ED: ", len(D_index))

# Solving -inf problem
NO_SIGNAL = -1000

for key, v in list(rx_power.items()):
    if v is None or math.isnan(v) or math.isinf(v):
        rx_power[key] = NO_SIGNAL # NO_SIGNAL replaces -inf values

<<<<<<< HEAD
=======
G_index = list(range(G))       # 0..G-1, gateways positions number
Nd = len(end_devices_cells)
D_index = list(range(Nd))      # 0..Nd-1, end-device positions number

>>>>>>> 206e46c6a9df8cbcb661b05126a713a749db6f37
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

for d in D_index:
    for p_gateway in G_index:
        # This indicates whether the power threshold is being reached in each
        # end-device for each gateway -> simplification to 0 or 1
        if (d, p_gateway) in rx_power:
            cover[(d, p_gateway)] = 1 if rx_power[(d, p_gateway)] >= rho else 0

# Energy variables
sf = 12
energies = _get_energies(sf)
E_index = list(range(len(energies)))
energies = dict(zip(E_index, energies))

# Optimization
model = ConcreteModel()
<<<<<<< HEAD
model.P = Set(initialize=G_index) # all gateways positions = all positions
model.D = Set(initialize=D_index) # devices
=======
model.P = Set(initialize=G_index)   # all gateways positions = all positions / Also energy
model.D = Set(initialize=D_index)   # devices
>>>>>>> 206e46c6a9df8cbcb661b05126a713a749db6f37

# Cover parameter as shown before
model.cover = Param(model.D, model.P, initialize=cover, within=Binary, default=0)

# Energy parameter
model.energy_per_gw_position = Param(model.P, initialize=energies)

# Gateway positions (Set or Not)
model.x = Var(model.P, domain=Binary)

def coverage_rule(m, d):
    # At least one gateway must cover each end-device
    return sum(m.cover[d, p_gateway] * m.x[p_gateway] for p_gateway in m.P) >= 1

#def energy_rule(m):
#    return sum(m.energy_per_gw_position[p_gateway] * m.x[p_gateway] for p_gateway in m.P) <= 2500

model.coverage = Constraint(model.D, rule=coverage_rule)
# model.energy = Constraint(rule=energy_rule)

def obj_rule(m):
    return sum(m.x[p_gateway]*m.energy_per_gw_position[p_gateway] for p_gateway in m.P)

model.obj = Objective(rule=obj_rule, sense=minimize)

# Debug of the model (in a .txt)
#with open("model.txt", "w") as f:
#    model.pprint(ostream=f)

# initialize solver parameters
solver = SolverFactory("glpk")
result = solver.solve(model) #, tee=True)

received_power = np.zeros(len(G_index))
if (result.solver.status == SolverStatus.ok and
        result.solver.termination_condition == TerminationCondition.optimal):
    # Chosen gateways
    chosen_gateways = [p for p in model.P if value(model.x[p]) > 0.5]

<<<<<<< HEAD
    # debub info
    print("\nChosen gateways (details):")
    for p in chosen_gateways:
        print(f"  p = {p}, coords = {coordinates[p]}")
    for d in D_index:
        total_mW = 0.0
        for p in G_index:
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
        # End-device positions

    dev_x = devices_df[0].values
    dev_y = devices_df[1].values

    # gateways positions
    xs_gate = [coordinates[p][0] for p in G_index]
    ys_gate = [coordinates[p][1] for p in G_index]

    # end devices positions

    xs_ed = [coordinates[p][0] for p in D_index]
    ys_ed = [coordinates[p][1] for p in D_index]

    # chosen gateways positions
    xs_chosen = [coordinates[p][0] for p in chosen_gateways]
    ys_chosen = [coordinates[p][1] for p in chosen_gateways]
        
    print("Number of gateways: ", len(xs_chosen))   
    # saving receiver power for each end-device
    np.savez(f"results/receiver_power_{path_gain_type}.npz", received_power)
    # saving all position coordinates
    np.savez(f"results/all_position.npz", dev_x, dev_y)
    # saving gateway positioning coordinates
    np.savez(f"results/chosen_position_{path_gain_type}.npz", xs_chosen, ys_chosen)
    # saving end devices positioning coordinates
    np.savez(f"results/ed_position.npz", xs_ed, ys_ed)
    # saving chosen gateways
    np.savez(f"results/chosen_gateways_{path_gain_type}.npz", chosen_gateways)

    # end-devices color by received power
    sc = plt.scatter(dev_x, dev_y, c=received_power, alpha=0.8, label="End-devices")

    # gateways escolhidos (destaque)
    plt.scatter(xs_chosen, ys_chosen, marker='s', color="black", edgecolors='k', s=80, label='Chosen gateway position')

else:
        print(f"Solver did not find a feasible solution for threshold {rho}")
        print("Status:", result.solver.status)
        print("Termination:", result.solver.termination_condition)
=======
# debug info
print("\nChosen gateways (details):")
for p in chosen_gateways:
    print(f"  p = {p}, coords = {coordinates[p]}, energy used (EDs) = {value(model.energy_per_gw_position[p])} J")

total_energy = value(sum(model.energy_per_gw_position[p] * model.x[p] for p in model.P))
print("\nTotal energy used:", total_energy)
>>>>>>> 206e46c6a9df8cbcb661b05126a713a749db6f37

