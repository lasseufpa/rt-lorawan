"""
Script to plot the number of gateways considering
different received power threshold

LASSE
Authors:
- Cláudio Modesto
"""


import os
import argparse
import pathlib
from matplotlib import pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--scenario", type=str)
args = parser.parse_args()

si_channels = ["cost", "log", "okumura", "threegpp"]
sd_channels = ["wix", "sionna", "wif"]
si_labels = ["COST-231", "Log-distance", "Okumura-Hata", "3GPP-UMa"]
sd_labels = ["WI (X3D)", "Sionna", "WI (Full 3D)"]
colors = ["blue", "red", "purple", "orange", "green", "skyblue", "brown"]
markers = [":", "solid", "dashed",  "dashdot", "dotted", "--", "-"]

ROOT_DIR = "figures" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

all_number_of_gws = []
counter = 0

plt.subplot(2, 1, 1)
plt.title(r"Number of gateways across different values of $\rho$")
for channel in si_channels:
    number_gws_data = np.load(f"../results/{args.scenario}/multi_number_of_gws_{channel}.npz")
    number_gws = number_gws_data["arr_0"]
    all_number_of_gws.append(number_gws)
    power_thresholds = number_gws_data["arr_1"]
    linestyle = "-"
    if channel in ("threegpp"):
        linestyle = "--"
    else:
        linestyle = "solid"
    plt.step(power_thresholds, number_gws,
                                linestyle=linestyle,
                                label=si_labels[counter],
                                color=colors.pop(),
                                linewidth=2,
                                where="post")
    handles, labels = plt.gca().get_legend_handles_labels()

    plt.ylim(0, 24)
    # Adjust legend order
    last_row = [all_number_of_gws[i][-1] for i in range(len(all_number_of_gws))]
    order = np.argsort(last_row)
    order = np.flip(order)

    plt.legend([handles[i] for i in order], [labels[i] for i in order])

    counter += 1
    plt.ylim(0, 60)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

plt.subplot(2, 1, 2)
all_number_of_gws = []
counter = 0
for channel in sd_channels:
    number_gws_data = np.load(f"../results/{args.scenario}/multi_number_of_gws_{channel}.npz")
    number_gws = number_gws_data["arr_0"]
    all_number_of_gws.append(number_gws)
    power_thresholds = number_gws_data["arr_1"]
    linestyle = "-"
    if channel in ("wif"):
        linestyle = "--"
    else:
        linestyle = "solid"
    plt.step(power_thresholds, number_gws,
                                linestyle=linestyle,
                                label=sd_labels[counter],
                                color=colors.pop(),
                                linewidth=2,
                                where="post")

    # Adjust legend order
    last_row = [all_number_of_gws[i][-1] for i in range(len(all_number_of_gws))]
    order = np.argsort(last_row)
    order = np.flip(order)

    handles, labels = plt.gca().get_legend_handles_labels()

    # Create legend in sorted order
    plt.legend([handles[i] for i in order], [labels[i] for i in order])

    counter += 1
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    mask_inf = np.isinf(number_gws)
    mask_ok  = ~mask_inf

    # find last feasible index
    last_idx = np.where(mask_ok)[0][-1]
    number_of_unf = np.sum(mask_inf)
    if number_of_unf == 0:
        continue
    else:
        # add X marker at cutoff
        plt.scatter(power_thresholds[-number_of_unf:],
                    [number_gws[last_idx]] * number_of_unf,
                    marker='x',
                    color="red",
                    s=70,
                    linewidths=2)


plt.gcf().supylabel("Required number of gateways", fontsize=15)
plt.xlabel(r"$\rho$", fontsize=14)
plt.ylim(0, 24)
plt.tight_layout()
plt.savefig("figures/number_of_gws.pdf", bbox_inches="tight")
