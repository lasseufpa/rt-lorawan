"""
Script to plot tradeoff between MSE and simulation time

LASSE
Authors:
- Cláudio Modesto
"""


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
scenarios = ["etoile", "canyon"]

plt.figure(figsize=(5, 5))  # width, height in inches
counter = 0
for scenario in scenarios:
    plt.subplot(2, 1, counter+1)
    sionna_time = np.mean(np.load(f"../time_results/{scenario}/sionna.npz")["arr_0"])
    okumura_time = np.mean(np.array(pd.read_csv(f"../time_results/{scenario}/okumura.csv",
                                                                        header=None)))
    log_time = np.mean(np.array(pd.read_csv(f"../time_results/{scenario}/log.csv",
                                                                        header=None)))
    threegpp_time = np.mean(np.array(pd.read_csv(f"../time_results/{scenario}/threegpp.csv",
                                                                        header=None)))
    cost_time = np.mean(np.array(pd.read_csv(f"../time_results/{scenario}/cost.csv",
                                                                        header=None)))
    full3d_time = np.mean(np.array(pd.read_csv(f"../time_results/{scenario}/full3d.csv",
                                                                        header=None)))
    x3d_time = np.mean(np.array(pd.read_csv(f"../time_results/{scenario}/x3d.csv",
                                                                        header=None)))

    std_sionna_time = np.std(np.load(f"../time_results/{scenario}/sionna.npz")["arr_0"]/60)
    std_okumura_time = np.std(np.array(pd.read_csv(f"../time_results/{scenario}/okumura.csv",
                                                                        header=None))/60)
    std_log_time = np.std(np.array(pd.read_csv(f"../time_results/{scenario}/log.csv",
                                                                        header=None))/60)
    std_threegpp_time = np.std(np.array(pd.read_csv(f"../time_results/{scenario}/threegpp.csv",
                                                                        header=None))/60)
    std_cost_time = np.std(np.array(pd.read_csv(f"../time_results/{scenario}/cost.csv",
                                                                        header=None))/60)
    std_full3d_time = np.std(np.array(pd.read_csv(f"../time_results/{scenario}/full3d.csv",
                                                                        header=None))/60)
    std_x3d_time = np.std(np.array(pd.read_csv(f"../time_results/{scenario}/x3d.csv",
                                                                        header=None))/60)

    avg_time = [okumura_time, cost_time, log_time, threegpp_time,
                                                sionna_time, full3d_time, x3d_time]

    std_time = [std_okumura_time, std_cost_time, std_log_time, std_threegpp_time,
                                                std_sionna_time, std_full3d_time, std_x3d_time]

    mses = np.load(f"../results/{scenario}/mses_gt_wix.npz")["arr_0"]

    if scenario == "etoile":
        FANCY_TITLE = "Etoile"
    elif scenario == "canyon":
        FANCY_TITLE = "St. Canyon"

    labels = ["Okumura-Hata", "COST-231", "Log-distance",
                                "3GPP-UMa", "Sionna", "WI (Full 3D)"]
    markers = ['o', 's', '^', 'D', 'P', 'X']

    avg_time = np.array(avg_time)/60
    plt.xlim(0, 1000)
    plt.title(f"MSE x simulation time in grid {counter+1} ({FANCY_TITLE})")
    plt.gcf().supylabel("Average simulation time (minutes)", fontsize=14)
    for i in range(len(labels)):
        plt.scatter(mses[i],
                    avg_time[:-1][i],
                    marker=markers[i],
                    label=labels[i],
                    color=colors[i])
    counter += 1
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=12)
    plt.legend()

plt.tight_layout()
plt.xlabel("MSE", fontsize=14)
plt.savefig(f"figures/tradeoff.pdf", bbox_inches='tight')
