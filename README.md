# LoRaWAN Gateway Placement for Network Planning Using Ray Tracing-based Channel Models

![graphical_abstract](https://github.com/lasseufpa/rt-lorawan/blob/main/figures/graphical_abstract.png)

Network planning for long range wide area networks (LoRaWAN) relies heavily on the channel models used to estimate wireless coverage and connectivity. Consequently, the quality of gateway (GW) deployment decisions may be strongly affected by the propagation assumptions adopted during the planning process. Given this motivation, this work investigates how different channel models influence the placement of LoRaWAN GWs,formulating an optimization problem that contrasts stochastic and empirical models with ray-tracing-based models. To this end, we developed a framework that integrates ray tracing (RT) simulators with a discrete-event network simulator. Using this framework to generate LoRaWAN data metrics, we employ an optimization model that determines the optimal GW placement under different channel models, received power constraints, and network scenarios. Our results show that the optimized solution is highly sensitive to the chosen channel model, even when considering the same scenarios with different RT simulators, revealing a clear trade-off between computational cost and the fidelity of the solution to real-world conditions.
 
## Compiling ns-3 LoRaWAN
The first step to use our framework, is compiling the ns-3 LoRaWAN module. You can follow the steps defined in this [link](https://github.com/signetlabdei/lorawan) to do this. 

## :writing_hand: Installing the Python environment for Sionna RT
Afte compile the ns-3 module, you need to configure python environment for Sionna RT. To do so, you need to execute the following command to install the conda environment

```bash
conda env create -f environemnt.yml
```

## :test_tube: Generating realistic channels (path gain) using Sionna RT
With all set, you can generate new path gains data for further optimization, considering a grid with 100 positions equally spaced, executing the following script:

```python
python3 path_loss_generator.py
```

## Generating stochastic or emprical channel using ns3-LoRaWAN
To generate stochastic or empirical channel models, you should move the source code `lorawan_general_energy_simulation.cc` to the `ns-3-dev/scratch`. After that in the ns-3-dev/scratch folder, you should run the following command:

```bash
./ns3 run scratch/lorawan_general_energy_simulation.cc -- --spreadingFactor=7 --channelType=cost --scenario=etoile
```

The available flags are:
- `--spreadingFactor`: The number of spreading factor, vary between [7, 12].
- `--channelType`: Type of channel to used. The options are log-distance, Okumura-Hata, COST-231, Nakagami, two ray, 3gpp-UMa, WI (x3D), WI (Full 3D), Sionna. To use one of these channel you should use the following options: `log`, `okumura`, `cost`, `nakagami` `twoRay`, `threegpp`, `wix`, `wif`, `sionna`.
- `simulationTime`: Time of the simulation.
- `scenario`: Type of grid organization used. The availabe options are: `etoile` and `canyon`.

## :gear Gateway placement optimization
In order to perform a gateway placement optimization, with a fixed threshold you can use the following command:

```python
python3 gateway_positioning -c okumura -t -120
```

In this case, an optimization process will running with a scenario with Okumura-Hata channel and a power threshold of -120 dBm. Furthermore, the following flags can use to change the behavior of the optimization:

`--channel`: Type of channel can be `okumura`, `cost`, `nakagami`, `threegpp`, `sionna`, `log`, `wif`, `wix`.

`--threshold`: Power threshold in dBm.

If you would like to perform an optimization using an interval of power threshold, you can use the following command:

```python
python3 multi_rho_gateway_positions -c cost --max-rho -80 --min-rho -150
```

In this case, the power threshold interval consider a minimum power of -150 dBm and maximum power of -80, with a COST-231 channel. Furthermore, the following flags can use to change the behavior of the optimization:

`--channel`: Type of channel can be `okumura`, `cost`, `nakagami`, `threegpp`, `sionna`, `log`, `wif`, `wix`.

`--threshold`: Power threshold in dBm.

`--max-rho`: Maximum threshold power.

`--min-rho`: Minimum threshold power.

## :bar_chart: Result plots
`plot_position.py`: Plot the grid with each position obtained from the optimization model.

`plot_pdr.py`: Plot packet delivery ratio (PDR) bar char for different channel models.

`plot_time.py`: Plot bar chart related to the simulation time to obtain physical-level metrics for different channel models.

`plot_multi_threshold.py`: Plot line chart related to the number of gateways suggested for different received power thresholds.

`plot_ed_grid.py`: Plot the end-devices grid organization across different scenarios.

`plot_tradeoff.py`: Script to generate a scatter plot for depicting the relationship between the MSE of received power (considering WI received power as ground truth) and the simulation time.

`plot_receiver_power.py`: Script to plot the CDF of received power of all end-devices across different channel models.

## :information_source: Credits

If you benefit from this work, please cite on your publications using:

```
@ARTICLE{modesto2026,
  author={Modesto, Cláudio and Mozart, Lucas and Gonçalves, Glauco and Nahum, Cleverson and Castro, Bruno and Klautau, Aldebaro},
  journal={IEEE Open Journal of the Communications Society}, 
  title={LoRaWAN Gateway Placement for Network Planning Using Ray Tracing-Based Channel Models}, 
  year={2026},
  volume={},
  number={},
  pages={1-1},
  keywords={Modeling;Channel models;LoRaWAN;Simulation;Internet of Things;Optimization;Distance measurement;Planning;Ray tracing;Costing;Discrete-event simulators;internet of things (IoT);optimization;site-specific},
  doi={10.1109/OJCOMS.2026.3704345
```