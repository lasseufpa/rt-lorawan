import os
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
    type=str, required=True
)

args = parser.parse_args()

ROOT_DIR = "results" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}/figures"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)


def _plot_relationship(cover):
    G = nx.Graph()

    # Add nodes
    for d in D_index:
        G.add_node(f"D{d}", bipartite=0)

    for g in G_index:
        G.add_node(f"G{g}", bipartite=1)

    # Add edges based on cover matrix
    for d in D_index:
        for g in G_index:
            if cover[(d, g)] == 1:
                G.add_edge(f"D{d}", f"G{g}")

    plt.figure(figsize=(10, 6))

    nx.draw(
        G,
        with_labels=True,
        node_size=900,
        font_size=9
    )

    plt.title("Device - Gateway Coverage Graph")
    plt.savefig("Graph.pdf")

def _get_path_gain(path_gain_type: str):
    path_gain_db = []
    if path_gain_type == "sionna":
        files = sorted(os.listdir(f"path_gains/{path_gain_type}/npy"), key=extract_number)
        for fname in files:
            filename = f"path_gains/{path_gain_type}/npy/{fname}"
            data = np.load(filename)
            path_gain_db.append(data)
    else:
        files = sorted(os.listdir(f"path_gains/ns3/{path_gain_type}/"), key=extract_number)
        for fname in files:
            df = pd.read_csv(f"path_gains/ns3/{path_gain_type}/{fname}", header=None)
            path_gain_db.append(df)

    return np.array(path_gain_db)

# Defining the numpy seed
np.random.seed(42)

# read CSV
devices_df = pd.read_csv("path_gains/coordinates.csv", header=None)

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
PATH_GAIN_COLUMN = 3

for d, (ix, iy) in enumerate(end_devices_cells):
    for p_gateway in range(G): # Power that a ED receivers from each gateway in all positions available
        if path_gain_type == "sionna":
            rx_power[(d, p_gateway)] = float(path_gain_db[p_gateway][ix][iy]) 
        else:
            rx_power[(d, p_gateway)] = float(path_gain_db[p_gateway][d][PATH_GAIN_COLUMN])

# Solving -inf problem
NO_SIGNAL = -1000

for key, v in list(rx_power.items()):
    if v is None or math.isnan(v) or math.isinf(v):
        rx_power[key] = NO_SIGNAL # NO_SIGNAL replaces -inf values

G_index = list(range(G))       # 0..G-1
Nd = len(end_devices_cells)
D_index = list(range(Nd))      # 0..Nd-1

P_min = min([x for x in rx_power.values() if x != -1000]) + 20 # threshold in dBm
print("Minimum threshold power: ", P_min)

# Defining an cover dict
cover = {}
for d in D_index:
    for p_gateway in G_index:
        # This indicates whether the power threshold is being reached in each
        # end-device for each gateway -> simplification to 0 or 1
        cover[(d, p_gateway)] = 1 if rx_power[(d, p_gateway)] >= P_min else 0

#_plot_relationship(cover)

model = ConcreteModel()
model.P = Set(initialize=G_index)   # all gateways positions = all positions
model.D = Set(initialize=D_index)   # devices

# Cover parameter as shown before
model.cover = Param(model.D, model.P, initialize=cover, within=Binary)

# Gateway positions (Set or Not)
model.x = Var(model.P, domain=Binary)

def coverage_rule(m, d):
    # At least one gateway must cover each end-device
    return sum(m.cover[d, p_gateway] * m.x[p_gateway] for p_gateway in m.P) >= 1

model.coverage = Constraint(model.D, rule=coverage_rule)

def obj_rule(m):
    return sum(m.x[p_gateway] for p_gateway in m.P)

model.obj = Objective(rule=obj_rule, sense=minimize)

# initialize solver parameters
solver = SolverFactory("glpk")
result = solver.solve(model) #, tee=True)

# Chosen gateways
chosen_gateways = [p for p in model.P if value(model.x[p]) > 0.5]

# debub info
print("\nChosen gateways (details):")
for p in chosen_gateways:
    print(f"  p = {p}, coords = {coordinates[p]}")

received_power = np.zeros(len(D_index))
for d in D_index:
    total_mW = 0.0
    for p in G_index:
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

# chosen gateways positions
xs_chosen = [coordinates[p][0] for p in chosen_gateways]
ys_chosen = [coordinates[p][1] for p in chosen_gateways]

# end-devices color by received power
sc = plt.scatter(dev_x, dev_y, c=received_power, alpha=0.8, label="End-devices")

# gateways escolhidos (destaque)
plt.scatter(xs_chosen, ys_chosen, marker='s', color="orange", edgecolors='k', s=80, label='Chosen gateway position')

# saving receiver power for each end-device
np.savez(f"results/receiver_power_{path_gain_type}.npz", received_power)

plt.xlabel("x (m)")
plt.ylabel("y (m)")
plt.title(f"Gateway positioning optimal solution ({path_gain_type.title()})")
plt.colorbar(sc, label="Received power (dBm)")
plt.gca().set_aspect('equal', 'box')
plt.grid(True)
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.1, -0.1), ncol=3)
plt.savefig(f"results/figures/gateway_positioning_{path_gain_type}.pdf", bbox_inches="tight")
plt.show()
