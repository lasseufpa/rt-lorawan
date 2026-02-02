# Gateway Placement for Network Planning Using Ray Tracing Channel Models in LoRaWAN

## Generate new path gains using RT
In order to generate new path gains data, considering a grid with 100 positions equally spaced, you can run the following script:

```python
python3 path_loss_generator.py
```

## 
In order to perform a gateway placement optimization, with a fixed threshold you can use the following command:

```python
python3 gateway_positioning -c okumura -t -120
```

In this case, an optimization process will running with a scenario with Okumura-Hata channel and a power threshold of -120 dBm. Furthermore, the following flags can use to change the behavior of the optimization:

`--channel`: Type of channel can be `okumura | cost | nakagami | threegpp | sionna | log`.

`--threshold`: Power threshold in dBm.

If you would like to perform an optimization using an interval of power threshold, you can use the following command:

```python
python3 multi_rho_gateway_positions -c cost --max-rho -80 --min-rho -150
```

In this case, the power threshold interval consider a minimum power of -150 dBm and maximum power of -80, with a COST-231 channel. Furthermore, the following flags can use to change the behavior of the optimization:

`--channel`: Type of channel can be `okumura | cost | nakagami | threegpp | sionna | log`.

`--threshold`: Power threshold in dBm.

`--max-rho`: Maximum threshold power.

`--min-rho`: Minimum threshold power.
