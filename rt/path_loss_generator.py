"""
Script to generate ray tracing datasets
"""

import os
import pathlib
import numpy as np
import sionna

from sionna.rt import load_scene, Transmitter, PlanarArray, RadioMapSolver, Camera
from matplotlib import pyplot as plt

rm_solver = RadioMapSolver()

z = 30  # fixed height for each device

# Create the output directory
OUTPUT_PATH_NAME = "../path_gains/sionna/bin"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)

OUTPUT_PATH_NAME = "../path_gains/sionna/npy"
if not os.path.isdir(OUTPUT_PATH_NAME):
    pathlib.Path(OUTPUT_PATH_NAME).mkdir(parents=True, exist_ok=True)


def config_scene(num_rows, num_cols):
    """Load and configure a scene"""
    scene = load_scene(sionna.rt.scene.etoile)
    scene.bandwidth = 100e6

    # Configure antenna arrays for all transmitters and receivers
    scene.tx_array = PlanarArray(
        num_rows=num_rows,
        num_cols=num_cols,
        pattern="iso",
        polarization="V"
    )

    scene.rx_array = PlanarArray(
        num_rows=1,
        num_cols=1,
        pattern="iso",
        polarization="V"
    )

    num_tx = 100
    spacing = 50  # meters between transmitters (adjust)
    grid_size = int(np.ceil(np.sqrt(num_tx)))

    positions = []
    look_ats = []

    for i in range(num_tx):
        row = i // grid_size
        col = i % grid_size

        x = -200 + col * spacing
        y = -200 + row * spacing

        positions.append([x, y, z])
        look_ats.append([0, 0, 0]) # all look toward center

    positions = np.array(positions)
    look_ats = np.array(look_ats)

    # Fixed power for all TX
    power_dbms = [14] * num_tx

    # Add all transmitters to scene
    for i in range(num_tx):
        scene.add(
            Transmitter(
                name=f"tx{i}",
                position=positions[i],
                look_at=look_ats[i],
                power_dbm=power_dbms[i]
            )
        )

    return scene

# Load and configure scene
num_rows=8
num_cols=2
scene = config_scene(num_rows, num_cols)

# Compute the path gain map
rm = rm_solver(scene,
               max_depth=5,
               samples_per_tx=10**7,
               cell_size=(1, 1))

cam = Camera(position=[0,0,1000],
                    orientation=np.array([0,np.pi/2,-np.pi/2]))
scene.render(camera=cam,
                    radio_map=rm,
                    rm_metric="path_gain",
                    rm_vmin=-160,
                    rm_vmax=-70,
                    rm_show_color_bar=True,
                    rm_tx=1)

plt.savefig("3D_preview.pdf")
plt.close()

plt.close()
rm.show(metric="path_gain")
plt.savefig("2D_preview.pdf")
plt.close()

print(rm.path_gain.shape)
# Save the radio map (dB) into a npy
path_gain_db = 10*np.log10(rm.path_gain)
for i in range(path_gain_db.shape[0]):
    filename_bin = f"../path_gains/sionna/bin/tx_{i}.bin"
    filename_npy = f"../path_gains/sionna/npy/tx_{i}.npy"
    path_gain_db[i].tofile(filename_bin)
    np.save(filename_npy, path_gain_db[i])

coordinates = []
for y in range(rm.tx_cell_indices.shape[1]):
    base = rm.cell_centers[rm.tx_cell_indices[0][y]][rm.tx_cell_indices[1][y]]
    extra1 = rm.tx_cell_indices[0][y]
    extra2 = rm.tx_cell_indices[1][y]
    coordinates.append([*base, extra1, extra2])
    
# Saving the path gain in .txt files
with open("../path_gains/coordinates.csv", "w") as f:
    for c in coordinates:
        f.write(f"{c[1]},{c[0]},{z},{c[4]},{c[3]}\n") # Saving in the format (x, y) -> indexes