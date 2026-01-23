import os
import pathlib
from matplotlib import pyplot as plt
import numpy as np

ROOT_DIR = "figures" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

receiver_power_rt = np.load("../results/receiver_power_sionna.npz")["arr_0"]
receiver_power_3gpp = np.load("../results/receiver_power_threegpp.npz")["arr_0"]
receiver_power_log = np.load("../results/receiver_power_log.npz")["arr_0"]
receiver_power_cost = np.load("../results/receiver_power_cost.npz")["arr_0"]
receiver_power_okumura = np.load("../results/receiver_power_okumura.npz")["arr_0"]

sorted_rec_power_rt = np.sort(receiver_power_rt)
sorted_rec_power_3gpp = np.sort(receiver_power_3gpp)
sorted_rec_power_log = np.sort(receiver_power_log)
sorted_rec_power_okumura = np.sort(receiver_power_okumura)
sorted_rec_power_cost = np.sort(receiver_power_cost)

rec_power_cdf_rt = np.arange(1, len(sorted_rec_power_rt) + 1) / len(sorted_rec_power_rt)
rec_power_cdf_3gpp = np.arange(1, len(sorted_rec_power_3gpp) + 1) / len(sorted_rec_power_3gpp)
rec_power_cdf_log = np.arange(1, len(sorted_rec_power_log) + 1) / len(sorted_rec_power_log)
rec_power_cdf_okumura = np.arange(1, len(sorted_rec_power_okumura) + 1) / len(sorted_rec_power_okumura)
rec_power_cdf_cost = np.arange(1, len(sorted_rec_power_cost) + 1) / len(sorted_rec_power_cost)

plt.title("CDF of path gain across all end-devices")
plt.plot(sorted_rec_power_rt, rec_power_cdf_rt, lw=2, linestyle="--", label="From RT")
plt.plot(sorted_rec_power_3gpp, rec_power_cdf_3gpp, lw=2, label="3GPP UMa")
plt.plot(sorted_rec_power_log, rec_power_cdf_3gpp, lw=2, label="Log-distance")
plt.plot(sorted_rec_power_okumura, rec_power_cdf_okumura, lw=2, label="Okumura")
plt.plot(sorted_rec_power_cost, rec_power_cdf_okumura, lw=2, label="COST231")
plt.ylabel("CDF")
plt.xlabel("Path gain (dBm)")
plt.legend()
plt.grid(axis='y')   # only horizontal lines
plt.savefig("figures/rec_power_cdf.pdf")