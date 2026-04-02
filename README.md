# LoRaWAN Gateway Placement for Network Planning Using Ray Tracing-based Channel Models

Network planning is a fundamental task in wireless communications, primarily focused on guaranteeing adequate coverage for every network device. In this context, the quality of any planning effort strongly depends on the channel model adopted in the design process of the simulations. Given this motivation, this work investigates how different channel models influence the placement of Long Range Wide Area Network (LoRaWAN) gateways (GWs), formulating an optimization problem that contrasts stochastic and empirical models with ray-tracing-based models. To this end, we developed a framework that integrates ray tracing (RT) simulators with a discrete-event network simulator. Using this framework to generate long range wide area network (LoRaWAN) wireless data metrics, we employ an optimization model that determines the optimized GW placement under different channel models and power constraints. Our results show that the optimized solution is highly sensitive to the chosen channel model, even when considering the same scenarios with different RT simulators, revealing a clear trade-off between computational cost and the fidelity of the solution to real-world conditions. 

## Compiling ns-3 LoRaWAN
The first step to use our framework, is compiling the ns-3 LoRaWAN module. You can follow the steps defined in this [link](https://github.com/signetlabdei/lorawan) to do this. 

## Installing the Python environment for Sionna RT
Afte compile the ns-3 module, you need to configure python environment for Sionna RT. To do so, you need to execute the following command to install the conda environment

```bash
conda env create -f environemnt.yml
```

## Generating realistic channels (path gain) using Sionna RT
With all set, you can generate new path gains data for further optimization, considering a grid with 100 positions equally spaced, executing the following script:

```python
python3 path_loss_generator.py
```

## Generating stochastic or emprical channel using ns3-LoRaWAN
To generate stochastic or empirical channel models, you should move the source code `lorawan_general_energy_simulation.cc` to the `ns-3-dev/scratch`. After that in the ns-3-dev/scratch folder, you should run the following command:

```bash
./ns3 run scratch/lorawan_general_energy_simulation.cc -- --spreadingFactor=7 --channelType=okumura
```

The available flags are:
- `--spreadingFactor`: The number of spreading factor, vary between [7, 12].
- `--channelType`: Type of channel to used. The options are log-distance, Okumura-Hata, COST-231, Nakagami, two ray, 3gpp-UMa, WI (x3D), WI (Full 3D), Sionna. To use one of these channel you should use the following options: `log`, `okumura`, `cost`, `nakagami` `twoRay`, `threegpp`, `wix`, `wif`, `sionna`.
- `simulationTime`: Time of the simulation.
-

## Gateway placement optimization
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
