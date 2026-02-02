import os
import pathlib
from matplotlib import pyplot as plt
import numpy as np

channels = ["cost", "log", "okumura", "threegpp", "sionna"]
colors = ["red", "orange", "blue", "green"]
labels = ["COST-231", "Log-distance", "Okumura-Hata", "3GPP-UMa", "Sionna"]
colors = ["blue", "red", "purple", "orange", "green"]

ROOT_DIR = "figures" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

counter = 0
for channel in channels:
    number_gws_data = np.load(f"../results/multi_number_of_gws_{channel}.npz")
    number_gws = number_gws_data["arr_0"]
    power_thresholds = number_gws_data["arr_1"]
    plt.plot(power_thresholds[:-1], number_gws[:-1], label=labels[counter], color=colors[counter])
    mask_inf = np.isinf(number_gws[:-1])
    mask_ok  = ~mask_inf

    # find last feasible index
    last_idx = np.where(mask_ok)[0][-1]
    
    number_of_unf = np.sum(mask_inf)
    if number_of_unf == 0:
        counter += 1
        continue
    else:
        # add X marker at cutoff
        plt.scatter(power_thresholds[:-1][-number_of_unf:],
                    [last_idx] * number_of_unf,
                    marker='x',
                    s=70,
                    color=colors[counter],
                    linewidths=2,
                    label="Infeasible beyond")
        counter += 1

plt.ylabel("Number of gateways", fontsize=14)
plt.xlabel(r"$\rho$", fontsize=14)
plt.title(r"Number of gateways across different values of $\rho$")
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.legend()
plt.savefig("figures/number_of_gws.pdf", bbox_inches="tight")
