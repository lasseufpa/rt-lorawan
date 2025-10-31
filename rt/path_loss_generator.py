'''
Script to generate ray tracing datasets
'''
import os
import argparse
import numpy as np
import tensorflow as tf
from matplotlib import pyplot as plt

# Import Sionna RT ccmomponents
import sionna
from sionna.rt import load_scene, Transmitter, Receiver, PlanarArray, Camera

parser = argparse.ArgumentParser()

parser.add_argument(
"--scenario", "-s", help="Type of scenario [canyon | etoile | munich | modern]", 
                type=str, required=True
)   

args = parser.parse_args()

if args.scenario == 'canyon':
    scene = load_scene('rtr/sionna/rt/scenes/simple_street_canyon/simple_street_canyon.xml')
    cam_look_at=[0, 0, 0]
    cam_position=[0, 0, 150]
    tx_position = [-31, 10, 29]
    rx_position = [23.0, 1.1, 1.4]
    rx_interf_position = [-23.0, 4.1, 1.4]
elif args.scenario == 'etoile':
    scene = load_scene('rtr/sionna/rt/scenes/etoile/etoile.xml')
    cam_position = [94.1, 63.1, 300]
    cam_look_at = [94.1, 63.1, 0]
    tx_position = [58.1, 74.3, 2.4]
    rx_position = [130.1, 51.9, 1.4]
    rx_interf_position = [45, 51.9, 1.4]
elif args.scenario == 'munich':
    scene = load_scene(sionna.rt.scene.munich) # Try also sionna.rt.scene.etoile
    cam_position = [-250,250,150]
    cam_look_at = [-15,30,28]
    tx_position=[8.5, 21, 27]
    rx_position=[45, 25, 1.5]
elif args.scenario == 'modern':
    scene = load_scene('rtr/sionna/rt/scenes/modern_city/modern_city.xml')
    cam_position = [30, 20, 50]
    cam_look_at = [-10,20,28]
    tx_position=[8.38372,-35.8423, 14]
    rx_position=[-10.8001, 9.67042, 1.5]

scene.frequency = 1e9 # MHz
scene.synthetic_array = True

if not os.path.isdir('scenes_images'):
    os.mkdir('scenes_images')

# Transmitter (=basestation) has an antenna pattern from 3GPP 38.901
scene.tx_array = PlanarArray(num_rows=1,
                             num_cols=1,
                             vertical_spacing=0.5,
                             horizontal_spacing=0.5,
                             pattern="tr38901",
                             polarization="cross")
# Add transmitter instance to scene

scene.rx_array = PlanarArray(num_rows=1,
                             num_cols=1,
                             vertical_spacing=0.5,
                             horizontal_spacing=0.5,
                             pattern="tr38901",
                             polarization="cross")

# Create transmitter
tx = Transmitter(name="tx",
                color=(0, 0, 1),
                position=[8.5,21,27])

scene.add(tx)

max_depth = 3 # Defines max number of ray interactions

# Update coverage_map
print("running")
cm = scene.coverage_map(max_depth=max_depth,
                        diffraction=True,
                        cm_cell_size=(1., 1.),
                        combining_vec=None,
                        precoding_vec=None,
                        num_samples=int(10e6))


min_gain_db = -130 # in dB; ignore any position with less than -130 dB path gain
max_gain_db = 0 # in dB; ignore strong paths

# sample points in a 5-400m radius around the receiver
min_dist = 5 # in m
max_dist = 200 # in m
n_receivers = 20

#sample batch_size random user positions from coverage map
ue_pos, cell_index = cm.sample_positions(n_receivers,
                                metric="path_gain",
                                min_val_db=min_gain_db,
                                max_val_db=max_gain_db,
                                min_dist=min_dist,
                                max_dist=max_dist)
ue_pos = tf.squeeze(ue_pos)
cell_index = tf.squeeze(cell_index)

# Create batch_size receivers
for i in range(n_receivers):
    rx = Receiver(name=f"rx-{i}",
                  color=(1, 0, 0),
                  position=ue_pos[i], # Random position sampled from coverage map
                  )
    scene.add(rx)

global_coordinates = cm.cell_centers.numpy() # Coordinates in blender
power_levels = 10*np.log10(cm.path_gain) # path gain in dB

cmap_data_list = []
counter = 0
for index in cell_index:
    power_level = power_levels[0, index[1], index[0]]
    cmap_data_list.append([ue_pos[counter][0], ue_pos[counter][1], ue_pos[counter][2], power_level])
    counter += 1

cmap_data_list = np.array(cmap_data_list)

print(cmap_data_list)
resolution = [480, 320] # increase for higher quality of renderings

# Create new camera
tx_pos = scene.transmitters["tx"].position.numpy()
bird_pos = tx_pos.copy()
bird_pos[-1] = 1000 # Set height of coverage map to 1000m above tx
bird_pos[-2]-= 0.01 # Slightly move the camera for correct orientation

# Create new camera
bird_cam = Camera("birds_view", position=bird_pos, look_at=tx_pos)

scene.add(bird_cam)

scene.render(camera="birds_view", coverage_map=cm, num_samples=512, resolution=resolution, show_devices=True)

np.set_printoptions(suppress=True, precision=8)  # precision optional
np.savetxt("path_gain.csv", cmap_data_list, delimiter=",", fmt="%.8f")
plt.savefig("coverage_map.pdf")