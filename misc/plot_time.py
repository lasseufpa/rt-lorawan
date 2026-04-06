import os
import pathlib
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = "figures" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

labels = ["Okumura-Hata", "COST-231", "Log-distance", "3GPP-UMa", 
                                        "Sionna", "WI (Full 3D)", "WI (X3D)"]
colors = ["green", "brown", "skyblue", "goldenrod", "red", "blue", "purple"]

sionna_time = np.mean(np.load("../time_results/sionna.npz")["arr_0"])
okumura_time = np.mean(np.array(pd.read_csv("../time_results/okumura.csv", header=None)))
log_time = np.mean(np.array(pd.read_csv("../time_results/log.csv", header=None)))
threegpp_time = np.mean(np.array(pd.read_csv("../time_results/threegpp.csv", header=None)))
cost_time = np.mean(np.array(pd.read_csv("../time_results/cost.csv", header=None)))
full3d_time = np.mean(np.array(pd.read_csv("../time_results/full3d.csv", header=None)))
x3d_time = np.mean(np.array(pd.read_csv("../time_results/x3d.csv", header=None)))

avg_time = [okumura_time, cost_time, log_time, threegpp_time,
                                            sionna_time, full3d_time, x3d_time]

avg_time = np.array(avg_time)/60

plt.yticks(fontsize=12)
plt.xticks(rotation=45)
plt.ylim(0, 75)
plt.title(r"Simulation time considering all channel models")
plt.xlabel("Channel models", fontsize=14)
plt.ylabel("Average simulation time (minutes)", fontsize=14)
bars = plt.bar(labels, avg_time, capsize=5, width=0.6, color=colors)
plt.bar_label(bars, fmt="%0.2f", padding=3, fontweight='bold')
plt.savefig(f"figures/simulation_time.pdf", bbox_inches='tight')