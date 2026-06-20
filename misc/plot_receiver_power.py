import os
import argparse
import pathlib
from matplotlib import pyplot as plt
import numpy as np

ROOT_DIR = "figures" # path to root database directory
# Create the output directory
OUTPUT_PATH_NAME = f"{ROOT_DIR}"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--scenario", "-s", type=str)
args = parser.parse_args()

receiver_power_sionna = np.load(f"../results/{args.scenario}/receiver_power_sionna.npz")["arr_0"]
receiver_power_sionna = [x for x in receiver_power_sionna if x < 0]
receiver_power_3gpp = np.load(f"../results/{args.scenario}/receiver_power_threegpp.npz")["arr_0"]
receiver_power_3gpp = [x for x in receiver_power_3gpp if x < 0]
receiver_power_log = np.load(f"../results/{args.scenario}/receiver_power_log.npz")["arr_0"]
receiver_power_log = [x for x in receiver_power_log if x < 0]
receiver_power_cost = np.load(f"../results/{args.scenario}/receiver_power_cost.npz")["arr_0"]
receiver_power_cost = [x for x in receiver_power_cost if x != 0]
receiver_power_okumura = np.load(f"../results/{args.scenario}/receiver_power_okumura.npz")["arr_0"]
receiver_power_okumura = [x for x in receiver_power_okumura if x < 0]
receiver_power_wix = np.load(f"../results/{args.scenario}/receiver_power_wix.npz")["arr_0"]
receiver_power_wix = [x for x in receiver_power_wix if x < 0]
receiver_power_wif = np.load(f"../results/{args.scenario}/receiver_power_wif.npz")["arr_0"]
receiver_power_wif = [x for x in receiver_power_wif if x < 0.0]

all_receiver_power = np.array([receiver_power_okumura, receiver_power_cost, receiver_power_log,
                        receiver_power_3gpp, receiver_power_sionna, receiver_power_wif])
baseline = np.array(receiver_power_wix)

mses = []
for i in range(all_receiver_power.shape[0]):
    mses.append(np.square(np.subtract(baseline, all_receiver_power[i])).mean())

np.savez(f"../results/{args.scenario}/mses_gt_wix.npz", mses)

print("okumura", "cost", "log", "3gpp", "sionna", "wif")    
print(mses)

print("Sionna avg. received power: ", np.mean(receiver_power_sionna))
print("Sionna std. received power: ", np.std(receiver_power_sionna))
print("3GPP avg. received power: ", np.mean(receiver_power_3gpp))
print("3GPP std. received power: ", np.std(receiver_power_3gpp))
print("Log avg. received power: ", np.mean(receiver_power_log))
print("Log std. received power: ", np.std(receiver_power_log))
print("Okumura avg. received power: ", np.mean(receiver_power_okumura))
print("Okumura std. received power: ", np.std(receiver_power_okumura))
print("COST-231 avg. received power: ", np.mean(receiver_power_cost))
print("COST-231 std. received power: ", np.std(receiver_power_cost))
print("WI (X3D) avg. received power: ", np.mean(receiver_power_wix))
print("WI (X3D) std. received power: ", np.std(receiver_power_wix))
print("WI (Full 3D) avg. received power: ", np.mean(receiver_power_wif))
print("WI (Full 3D): std. received power ", np.std(receiver_power_wif))

sorted_rec_power_sionna = np.sort(receiver_power_sionna)
sorted_rec_power_3gpp = np.sort(receiver_power_3gpp)
sorted_rec_power_log = np.sort(receiver_power_log)
sorted_rec_power_okumura = np.sort(receiver_power_okumura)
sorted_rec_power_cost = np.sort(receiver_power_cost)
sorted_rec_power_wix = np.sort(receiver_power_wix)
sorted_rec_power_wif = np.sort(receiver_power_wif)

rec_power_cdf_sionna = np.arange(1, len(sorted_rec_power_sionna) + 1) / len(sorted_rec_power_sionna)
rec_power_cdf_3gpp = np.arange(1, len(sorted_rec_power_3gpp) + 1) / len(sorted_rec_power_3gpp)
rec_power_cdf_log = np.arange(1, len(sorted_rec_power_log) + 1) / len(sorted_rec_power_log)
rec_power_cdf_okumura = np.arange(1, len(sorted_rec_power_okumura) + 1) / len(sorted_rec_power_okumura)
rec_power_cdf_cost = np.arange(1, len(sorted_rec_power_cost) + 1) / len(sorted_rec_power_cost)
rec_power_cdf_wix = np.arange(1, len(sorted_rec_power_wix) + 1) / len(sorted_rec_power_wix)
rec_power_cdf_wif = np.arange(1, len(sorted_rec_power_wif) + 1) / len(sorted_rec_power_wif)

if args.scenario == "canyon":
    fancy_title = "St. Canyon"
elif args.scenario == "etoile":
    fancy_title = "Etoile"

plt.title(f"CDF of received power across all EDs ({fancy_title})")
plt.plot(sorted_rec_power_sionna, rec_power_cdf_sionna, lw=2,
                linestyle="-", label="Sionna", color="red")
plt.plot(sorted_rec_power_wix, rec_power_cdf_wix,
                linestyle="-", lw=2, label="WI (X3D)", color="purple")
plt.plot(sorted_rec_power_3gpp, rec_power_cdf_3gpp, lw=1.5,
                linestyle="-", label="3GPP UMa", color="goldenrod")
plt.plot(sorted_rec_power_log, rec_power_cdf_log, lw=1.5,
                linestyle="-", label="Log-distance", color="skyblue")
plt.plot(sorted_rec_power_okumura, rec_power_cdf_okumura, lw=1.5,
                linestyle="-", label="Okumura-Hata", color="green")
plt.plot(sorted_rec_power_cost, rec_power_cdf_cost, lw=1.5,
                linestyle="-", label="COST-231", color="brown")
plt.plot(sorted_rec_power_wif, rec_power_cdf_wif, lw=2,
                linestyle="-", label="WI (Full 3D)", color="blue")
plt.ylabel("CDF", fontsize=14)
plt.xlabel("Received power (dBm)", fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.legend()
plt.grid(axis='y')   # only horizontal lines
plt.savefig(f"figures/rec_power_cdf_{args.scenario}.pdf")
