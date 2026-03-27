import os
import pathlib
from matplotlib import pyplot as plt
import numpy as np

ROOT_DIR = "figures" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

all_positions = np.load("../results/all_position.npz")
x_coord = all_positions["arr_0"]
y_coord = all_positions["arr_1"]

plt.scatter(x_coord, y_coord, alpha=0.8, color="gray", marker="x")

ed_positions = np.load("../results/ed_position.npz")
x_coord = ed_positions["arr_0"]
y_coord = ed_positions["arr_1"]

plt.scatter(x_coord, y_coord, marker='D',
            color="cadetblue",
            s=80,
            label="End-device")

plt.xlabel("x (m)", fontsize=14)
plt.ylabel("y (m)", fontsize=14)
plt.title(f"Position of all end-devices")
plt.gca().set_aspect('equal', 'box')
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(
    loc="lower center",
    bbox_to_anchor=(0.48, -0.23),
    ncol=5,
    alignment="center"
)# plt.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.1, -0.1), ncol=3)
plt.savefig(f"figures/ed_position.pdf", bbox_inches="tight")
