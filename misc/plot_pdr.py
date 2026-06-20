"""
Script to plot average packet delivery ratio

LASSE
Authors:
- Cláudio Modesto
"""


import os
import pathlib
import numpy as np
from scipy.stats import t
from matplotlib import pyplot as plt
import pandas as pd

def confidence_interval(mean, std, n, confidence=0.95):
    alpha = 1 - confidence
    t_critical = t.ppf(1 - alpha/2, df=n-1)

    margin = t_critical * std / np.sqrt(n)

    lower = mean - margin
    upper = mean + margin

    return [lower, upper, margin]

ROOT_DIR = "figures" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

colors = ["green", "brown", "skyblue", "goldenrod", "red", "blue", "purple"]
scenarios = ["etoile", "canyon"]
channels = ["okumura", "cost", "log", "threegpp", "sionna", "wix", "wif"]
labels = ["Okumura-Hata", "COST-231", "Log-distance", "3GPP-UMa", 
                                        "Sionna", "WI (Full 3D)", "WI (X3D)"]

for i in range(len(scenarios)):
    if scenarios[i] == "etoile":
        fancy_title = "grid 1 and Etoile"
    elif scenarios[i] == "canyon":
        fancy_title = "grid 2 and St. Canyon"
    all_pdr = []
    chosen_gateways = []
    plt.subplot(2, 1, i+1)
    for channel in channels:
        chosen_gateways = np.load(f"../results/{scenarios[i]}/chosen_gateways_{channel}.npz")["arr_0"]
        channel_pdr = []
        for gw_id in chosen_gateways:
            df = pd.read_csv(f"../pdr_results/sf_7/{channel}/{scenarios[i]}/{gw_id}.csv", header=None)
            channel_pdr.append(np.array(df).flatten())
        all_pdr.append(list(channel_pdr))

    L = 0.167  # offered traffic
    collision_factor = np.exp(-2 * L)
    realizations = 10
    avg_all_pdr = []
    std_all_pdr = []
    for channel in range(len(all_pdr)):
        pdr_w_collision = []
        for realization in range(realizations):
            sum_pdr_lossless = 0
            for gw_id in range(len(all_pdr[channel])):
                sum_pdr_lossless += all_pdr[channel][gw_id][realization]
            avg_pdr_lossless = sum_pdr_lossless / len(all_pdr[channel])
            error = avg_pdr_lossless * collision_factor
            pdr_w_collision.append(error * 100)
        
        avg_all_pdr.append(np.mean(pdr_w_collision))
        std_all_pdr.append(np.std(pdr_w_collision))

    all_ci = []
    for j in range(len(avg_all_pdr)):
        all_ci.append(confidence_interval(avg_all_pdr[j], std_all_pdr[j], 10))

    print(f"STD: {scenarios[i]}: {std_all_pdr}")
    print(f"AVG: {scenarios[i]}: {avg_all_pdr}")
    print(f"CI: {scenarios[i]}: {all_ci}")

    plt.title(rf"Average PDR across all GWs in {fancy_title} ($\rho$ = -90)")
    bars = plt.bar(labels, avg_all_pdr, capsize=5, width=0.6, color=colors)
    plt.bar_label(bars, fmt="%0.2f", padding=3, fontweight='bold')
    plt.ylim(0, 135)
    plt.yticks(fontsize=12)
    plt.xticks(rotation=45)

print(labels)
plt.xlabel("Channel models", fontsize=14)
plt.gcf().supylabel("Average PDR (%)", fontsize=14)
plt.tight_layout()
plt.savefig(f"figures/avg_pdr.pdf", bbox_inches='tight')
