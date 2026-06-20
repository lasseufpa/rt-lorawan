"""
Script to plot end-device grid positions

LASSE
Authors:
- Cláudio Modesto
"""


import os
import pathlib
import argparse
from matplotlib import pyplot as plt
import numpy as np

ROOT_DIR = "figures" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--scenario", type=str)
args = parser.parse_args()

all_positions = np.load(f"../results/{args.scenario}/all_position.npz")
x_coord = all_positions["arr_0"]
y_coord = all_positions["arr_1"]

plt.scatter(x_coord, y_coord, alpha=0.8, color="gray", marker="x")

ed_positions = np.load(f"../results/{args.scenario}/ed_position.npz")
x_coord = ed_positions["arr_0"]
y_coord = ed_positions["arr_1"]

color = "blue"
if args.scenario == "etoile":
    color = "cadetblue"
    legend_position = ((0.48, -0.23))
elif args.scenario == "munich":
    color = "darkred"
elif args.scenario == "canyon":
    color = "rebeccapurple"
    legend_position = (0.48, -0.33)

plt.scatter(x_coord, y_coord, marker='D',
            color=color,
            s=80,
            label="End-device")

plt.xlabel("x (m)", fontsize=14)
plt.ylabel("y (m)", fontsize=14)
plt.title(f"Position of all end-devices (D = {len(x_coord)})")
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
plt.savefig(f"figures/ed_position_{args.scenario}.pdf", bbox_inches="tight")
