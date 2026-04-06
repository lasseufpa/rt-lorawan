import os
import pathlib
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd

ROOT_DIR = "figures" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

colors = ["green", "brown", "skyblue", "goldenrod", "red", "blue", "purple"]
channels = ["okumura", "cost", "log", "threegpp", "sionna", "wix", "wif"]
labels = ["Okumura-Hata", "COST-231", "Log-distance", "3GPP-UMa", 
                                        "Sionna", "WI (Full 3D)", "WI (X3D)"]
avg_all_pdr = []
std_all_pdr = []
chosen_gateways = []
for channel in channels:
    chosen_gateways = np.load(f"../results/chosen_gateways_{channel}.npz")["arr_0"]
    channel_pdr = []
    for gw_id in chosen_gateways:
        df = pd.read_csv(f"../pdr_results/sf_7/{channel}/{gw_id}.csv", header=None)
        channel_pdr.append(df)
    avg_all_pdr.append(np.mean(channel_pdr))
    std_all_pdr.append(np.std(channel_pdr))

avg_all_pdr = np.array(avg_all_pdr) * 100

plt.ylim(0, 110)
plt.yticks(fontsize=12)
plt.xticks(rotation=45)
plt.title(r"Average PDR across different channel models ($\rho$ = -90)")
plt.xlabel("Channel models", fontsize=14)
plt.ylabel("Average PDR (%)", fontsize=14)
bars = plt.bar(labels, avg_all_pdr, capsize=5, width=0.6, color=colors)
plt.bar_label(bars, fmt="%0.2f", padding=3, fontweight='bold')
plt.savefig(f"figures/avg_pdr.pdf", bbox_inches='tight')
