"""
Script to generate ray tracing datasets
"""

import os
import time
import pathlib
import numpy as np
import sionna
import argparse

from sionna.rt import load_scene, Transmitter, PlanarArray, RadioMapSolver, Camera, RadioMaterial
from matplotlib import pyplot as plt

parser = argparse.ArgumentParser()

parser.add_argument(
    "--scenario", "-s", help="3D scenario to be used",
    type=str, required=False, default="etoile"
)

parser.add_argument(
    "--realization", "-r", help="Number of realizations",
    type=int, required=False, default=1
)

args = parser.parse_args()

rm_solver = RadioMapSolver()


# Create the output directory
PG_PATH_NAME = f"../path_gain_results/sionna/{args.scenario}"
if not os.path.isdir(PG_PATH_NAME):
    pathlib.Path(PG_PATH_NAME).mkdir(parents=True, exist_ok=True)

TIME_PATH_NAME = f"../time_results/{args.scenario}"
if not os.path.isdir(TIME_PATH_NAME):
    pathlib.Path(TIME_PATH_NAME).mkdir(parents=True, exist_ok=True)

selected_gateways = [12, 13]
def config_scene(num_rows, num_cols):
    """Load and configure a scene"""
    grid_size = None
    if args.scenario == "etoile":
        scene = load_scene(sionna.rt.scene.etoile)
        intial_position_x = -200 
        intial_position_y = -200
        num_tx = 100
        z = 30  # fixed height for each device
        spacing = 50  # meters between transmitters (adjust)
        camera_position = [0, 0, 1000]
    elif args.scenario == "rosslyn":
        scene = load_scene("scenarios/rosslyn/rosslyn.xml")
        intial_position_x = 0 
        intial_position_y = 0
        num_tx = 100
        z = 60  # fixed height for each device
        spacing = 50
        camera_position = [0, 0, 1500]
    elif args.scenario == "canyon":
        scene = load_scene(sionna.rt.scene.simple_street_canyon)
        intial_position_x = -60
        intial_position_y = -33
        num_tx = 104
        z = 60   # fixed height for each device
        spacing = 10
        grid_size = 13
        camera_position = [0, 0, 250]
    scene.bandwidth = 1e6

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

    if grid_size is None:
        grid_size = int(np.ceil(np.sqrt(num_tx)))

    positions = []

    for i in range(num_tx):
        row = i // grid_size
        col = i % grid_size

        x = intial_position_x + col * spacing
        y = intial_position_y + row * spacing

        positions.append([x, y, z])

    positions = np.array(positions)

    # Add all transmitters to scene
    for i in range(num_tx):
        if i in selected_gateways:
            color = (0, 0, 0)
        else:
            color = (1, 0, 0)
        scene.add(
            Transmitter (
                name=f"tx{i}",
                position=positions[i],
                color=color,
            )
        )

    return scene, positions, z, camera_position

# Load and configure scene
num_rows=1
num_cols=1

REALIZATIONS = args.realization
all_times = []
for i in range(REALIZATIONS):
    start = time.perf_counter()
    scene, positions, z, camera_position = config_scene(num_rows, num_cols)
    # Compute the path gain map
    print(f"-> Realization {i}")
    rm = rm_solver(scene,
                max_depth=6,
                center=[0, 0, 1.4],
                size=[677, 854],
                orientation=[0, 0, 0],
                cell_size=[1, 1],
                diffraction=True,
                samples_per_tx=10**7)
    end = time.perf_counter()
    all_times.append(end-start)

np.savez(f"../time_results/{args.scenario}/sionna.npz", all_times)

cam = Camera(position=camera_position,
                    orientation=np.array([0,np.pi/2,-np.pi/2]))
fig = scene.render(camera=cam,
                    radio_map=rm,
                    rm_metric="path_gain",
                    rm_vmin=-160,
                    rm_vmax=-70,
                    rm_show_color_bar=True,
                    rm_tx=selected_gateways)

plt.savefig(f"3D_preview_{args.scenario}.pdf")

plt.close()

print(rm.path_gain.shape)
# Save the radio map (dB) into a npy
path_gain_db = 10*np.log10(rm.path_gain)
for i in range(path_gain_db.shape[0]):
    coord_counter = 0
    filename = f"../path_gain_results/sionna/{args.scenario}/{i}.csv"
    with open(filename, "w") as f:
        for j in range(path_gain_db.shape[0]):
            path_gain = path_gain_db[i][rm.tx_cell_indices[0][j]-1][rm.tx_cell_indices[1][j]-1]
            f.write(f"{positions[coord_counter][0]},{positions[coord_counter][1]},{z},{path_gain}\n") # 
            coord_counter += 1


coordinates = []
for y in range(rm.tx_cell_indices.shape[1]):
    base = rm.cell_centers[rm.tx_cell_indices[0][y]-1][rm.tx_cell_indices[1][y]-1]
    extra1 = rm.tx_cell_indices[0][y]
    extra2 = rm.tx_cell_indices[1][y]
    coordinates.append([*base, extra1, extra2])
    
# Saving the path gain in .txt files
coord_counter = 0
with open(f"../path_gain_results/{args.scenario}_coordinates.csv", "w") as f:
    for c in coordinates:
        f.write(f"{positions[coord_counter][0]},{positions[coord_counter][1]},{z},{c[4]},{c[3]}\n") # Saving in the format (x, y) -> indexes
        coord_counter += 1

with open(f"../path_gain_results/{args.scenario}_measured_position.csv", "w") as f:
    for c in coordinates:
        f.write(f"{c[1]},{c[0]},{z},{c[4]},{c[3]}\n") # Saving in the format (x, y) -> indexes
