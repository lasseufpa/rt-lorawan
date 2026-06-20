"""
Script to plot gateway positions after optimization

LASSE
Authors:
- Cláudio Modesto
"""


import os
import argparse
import pathlib
from matplotlib.path import Path
from matplotlib import pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--channels", nargs="+", type=str)
parser.add_argument("--labels", nargs="+", type=str)
parser.add_argument("--colors", nargs="+", type=str)
parser.add_argument("--scenario", type=str)
args = parser.parse_args()

#channels = ["cost", "log", "okumura", "threegpp", "sionna", "wi"]
#colors = ["green", "blue", "orange", "red", "black", "purple"]
#labels = ["COST-231", "Log-distance", "Okumura-Hata", "3GPP-UMa", "WI", "Sionna"]

colors = args.colors
labels = args.labels

ROOT_DIR = "figures" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

if args.scenario == "grid1":
    scenario = "etoile"
elif args.scenario == "grid2":
    scenario = "canyon"
else:
    scenario = args.scenario

all_positions = np.load(f"../results/{scenario}/all_position.npz")
x_coord = all_positions["arr_0"]
y_coord = all_positions["arr_1"]

plt.scatter(x_coord, y_coord, alpha=0.8, color="gray")
counter = 0
all_xs_chosen = []
all_ys_chosen = []
for channel in args.channels:
    position_data = np.load(f"../results/{scenario}/chosen_position_{channel}.npz")
    xs_chosen = position_data["arr_0"]
    ys_chosen = position_data["arr_1"]
    plt.scatter(xs_chosen, ys_chosen, marker='s',
                color=colors[counter],
                edgecolors='k',
                s=80,    
                label=labels[counter])
    counter += 1

if args.scenario == "etoile":
    fancy_title = "Etoile"
    legend_position = ((0.48, -0.23))
elif args.scenario == "canyon":
    fancy_title = "St. Canyon"
    legend_position = (0.48, -0.33)
elif args.scenario == "grid1":
    fancy_title = "grid 1"
    legend_position = ((0.48, -0.23))
elif args.scenario == "grid2":
    fancy_title = "grid 2"
    legend_position = (0.48, -0.33)

plt.xlabel("x (m)", fontsize=14)
plt.ylabel("y (m)", fontsize=14)
plt.title(f"Optimized solution using different channels ({fancy_title})")
plt.gca().set_aspect('equal', 'box')
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(
    loc="lower center",
    bbox_to_anchor=legend_position,
    ncol=5,
    alignment="center"
)# plt.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.1, -0.1), ncol=3)
plt.savefig(f"figures/gateway_positioning_{args.scenario}.pdf", bbox_inches="tight")
