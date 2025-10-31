/*
 * Copyright (c) 2017 University of Padova
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * Author: Davide Magrin <magrinda@dei.unipd.it>
 */

/*
 * This script simulates a complex scenario with multiple gateways and end
 * devices. The metric of interest for this script is the throughput of the
 * network.
 */

#include "ns3/building-allocator.h"
#include "ns3/building-penetration-loss.h"
#include "ns3/buildings-helper.h"
#include "ns3/class-a-end-device-lorawan-mac.h"
#include "ns3/command-line.h"
#include "ns3/constant-position-mobility-model.h"
#include "ns3/correlated-shadowing-propagation-loss-model.h"
#include "ns3/double.h"
#include "ns3/end-device-lora-phy.h"
#include "ns3/forwarder-helper.h"
#include "ns3/gateway-lora-phy.h"
#include "ns3/gateway-lorawan-mac.h"
#include "ns3/log.h"
#include "ns3/lora-helper.h"
#include "ns3/mobility-helper.h"
#include "ns3/network-server-helper.h"
#include "ns3/node-container.h"
#include "ns3/periodic-sender-helper.h"
#include "ns3/pointer.h"
#include "ns3/position-allocator.h"
#include "ns3/random-variable-stream.h"
#include "ns3/simulator.h"

#include <algorithm>
#include <ctime>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>

using namespace ns3;
using namespace lorawan;
using namespace std;

NS_LOG_COMPONENT_DEFINE("ComplexLorawanNetworkExample");

// Network settings
int nDevices = 20;           //!< Number of end device nodes to create
int nGateways = 1;            //!< Number of gateway nodes to create
double radiusMeters = 6400;         //!< Radius (m) of the deployment
double simulationTimeSeconds = 600; //!< Scenario duration (s) in simulated time

// Channel model
bool realisticChannelModel = false; //!< Whether to use a more realistic channel model with
                                    //!< Buildings and correlated shadowing

int appPeriodSeconds = 60; //!< Duration (s) of the inter-transmission time of end devices

// Output control
bool printBuildingInfo = true; //!< Whether to print building information

static std::ofstream g_outFile;
bool stochasticChannel = true;

uint32_t totalReceived = 0;
uint32_t totalSent = 0;

void
RxCallback(Ptr<const Packet> packet, unsigned int iface)
{   
    std::cout << "Packet received" << std::endl;
    totalReceived++;
    std::cout << totalReceived << std::endl;
}

void
TxPacketSent(Ptr<const Packet> packet)
{
    std::cout << "packet sent" << std::endl;
    totalSent++;
    std::cout << totalSent << std::endl;
}

int
main(int argc, char* argv[])
{
    CommandLine cmd(__FILE__);
    cmd.AddValue("nDevices", "Number of end devices to include in the simulation", nDevices);
    cmd.AddValue("radius", "The radius (m) of the area to simulate", radiusMeters);
    cmd.AddValue("realisticChannel",
                 "Whether to use a more realistic channel model",
                 realisticChannelModel);
    cmd.AddValue("simulationTime", "The time (s) for which to simulate", simulationTimeSeconds);
    cmd.AddValue("appPeriod",
                 "The period in seconds to be used by periodically transmitting applications",
                 appPeriodSeconds);
    cmd.AddValue("print", "Whether or not to print building information", printBuildingInfo);
    cmd.Parse(argc, argv);

    // Set up logging
    LogComponentEnable("ComplexLorawanNetworkExample", LOG_LEVEL_ALL);
    // LogComponentEnable("LoraChannel", LOG_LEVEL_INFO);
    // LogComponentEnable("LoraPhy", LOG_LEVEL_ALL);
    // LogComponentEnable("EndDeviceLoraPhy", LOG_LEVEL_ALL);
    // LogComponentEnable("GatewayLoraPhy", LOG_LEVEL_ALL);
    // LogComponentEnable("LoraInterferenceHelper", LOG_LEVEL_ALL);
    // LogComponentEnable("LorawanMac", LOG_LEVEL_ALL);
    // LogComponentEnable("EndDeviceLorawanMac", LOG_LEVEL_ALL);
    // LogComponentEnable("ClassAEndDeviceLorawanMac", LOG_LEVEL_ALL);
    // LogComponentEnable("GatewayLorawanMac", LOG_LEVEL_ALL);
    // LogComponentEnable("LogicalLoraChannelHelper", LOG_LEVEL_ALL);
    // LogComponentEnable("LogicalLoraChannel", LOG_LEVEL_ALL);
    // LogComponentEnable("LoraHelper", LOG_LEVEL_ALL);
    // LogComponentEnable("LoraPhyHelper", LOG_LEVEL_ALL);
    // LogComponentEnable("LorawanMacHelper", LOG_LEVEL_ALL);
    // LogComponentEnable("PeriodicSenderHelper", LOG_LEVEL_ALL);
    // LogComponentEnable("PeriodicSender", LOG_LEVEL_ALL);
    // LogComponentEnable("LorawanMacHeader", LOG_LEVEL_ALL);
    // LogComponentEnable("LoraFrameHeader", LOG_LEVEL_ALL);
    // LogComponentEnable("NetworkScheduler", LOG_LEVEL_ALL);
    // LogComponentEnable("NetworkServer", LOG_LEVEL_ALL);
    // LogComponentEnable("NetworkStatus", LOG_LEVEL_ALL);
    // LogComponentEnable("NetworkController", LOG_LEVEL_ALL);

    /***********
     *  Setup  *
     ***********/

    g_outFile.open("lorawan-metrics.csv");

    // Create the time value from the period
    Time appPeriod = Seconds(appPeriodSeconds);

    // Mobility
    MobilityHelper mobility;
    mobility.SetPositionAllocator("ns3::UniformDiscPositionAllocator",
                                  "rho",
                                  DoubleValue(radiusMeters),
                                  "X",
                                  DoubleValue(0.0),
                                  "Y",
                                  DoubleValue(0.0));
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");

    // Create the LorawanMacHelper
    LorawanMacHelper macHelper = LorawanMacHelper();

    // Create the LoraHelper
    LoraHelper helper = LoraHelper();
    helper.EnablePacketTracking(); // Output filename
    // helper.EnableSimulationTimePrinting ();

    // Create the NetworkServerHelper
    NetworkServerHelper nsHelper = NetworkServerHelper();

    // Create the ForwarderHelper
    ForwarderHelper forHelper = ForwarderHelper();

    /************************
     *  Create End Devices  *
     ************************/

    // Create a set of nodes
    NodeContainer endDevices;
    endDevices.Create(nDevices);

    // Assign a mobility model to each node
    mobility.Install(endDevices);

    ifstream file("path_gain.csv");
    string line;

    // Make it so that nodes are at a certain height > 0
    for (auto j = endDevices.Begin(); j != endDevices.End(); ++j)
    {
        float positions[4] = {0, 0, 0, 0};
        getline(file, line);
        stringstream ss(line);
        string value;
        for (int k = 0; k < 4; ++k) {
                if (!getline(ss, value, ',')) {
                    cerr << "Line " << line << " does not have 4 values!" << endl;
                    break;
                }
                try {
                    positions[k] = stof(value);
                } catch (const std::invalid_argument& e) {
                    cerr << "Invalid float: " << value << endl;
                    positions[k] = 0.0f; // fallback
            }
        }
        Ptr<MobilityModel> mobility = (*j)->GetObject<MobilityModel>();
        Vector position = mobility->GetPosition();
        position.x = positions[0];
        position.y = positions[1];
        position.z = positions[2];
        mobility->SetPosition(position);
    }

    file.close();
    /*********************
     *  Create Gateways  *
     *********************/

    // Create the gateway nodes (allocate them uniformly on the disc)
    NodeContainer gateways;
    gateways.Create(nGateways);
    Vector gatewayPosition = Vector(8.5, 21, 27);

    Ptr<ListPositionAllocator> allocator = CreateObject<ListPositionAllocator>();
    // Make it so that nodes are at a certain height > 0
    allocator->Add(gatewayPosition);
    mobility.SetPositionAllocator(allocator);
    mobility.Install(gateways);

    /***********************
    *  Create the channel  *
    ************************/
    ifstream file2("path_gain.csv");

    Ptr<PropagationLossModel> loss;
    if (stochasticChannel) 
    {
        // Create the lora channel object
        // Ptr<LogDistancePropagationLossModel> lossDist = CreateObject<LogDistancePropagationLossModel>();
        //lossDist->SetPathLossExponent(3.76);
        //lossDist->SetReference(1, 7.7);

        // Ptr<NakagamiPropagationLossModel> nakagami = CreateObject<NakagamiPropagationLossModel> ();
        // // Configure Nakagami parameters (optional)
        // nakagami->SetAttribute ("m0", DoubleValue (1.0));    // d < d0
        // nakagami->SetAttribute ("m1", DoubleValue (1.5));    // d0 ≤ d < d1
        // nakagami->SetAttribute ("m2", DoubleValue (3.0));    // d ≥ d1
        // nakagami->SetAttribute ("Distance1", DoubleValue (80.0));
        // nakagami->SetAttribute ("Distance2", DoubleValue (200.0));

        Ptr<TwoRayGroundPropagationLossModel> tworay = CreateObject<TwoRayGroundPropagationLossModel> ();

        // Configure attributes (optional)
        tworay->SetAttribute ("SystemLoss", DoubleValue (1.0));
        tworay->SetAttribute ("HeightAboveZ", DoubleValue (1.5)); // antenna height

        // loss = lossDist;
        loss = tworay;
    } else {
        Ptr<MatrixPropagationLossModel> matrixLoss = CreateObject<MatrixPropagationLossModel> ();
        for (auto gw = gateways.Begin(); gw != gateways.End(); ++gw)
        {
            Ptr<MobilityModel> gw_mobility = (*gw)->GetObject<MobilityModel>();
            Vector gw_position = gw_mobility->GetPosition();
            cout << gw_position << endl;
            for (auto k = endDevices.Begin(); k != endDevices.End(); ++k)
            {
                float positions[4] = {0, 0, 0, 0};
                getline(file2, line);
                stringstream ss(line);
                string value;
                for (int k = 0; k < 4; ++k) 
                { 
                    if (!getline(ss, value, ',')) {
                            cerr << "Line " << line << " does not have 4 values!!" << endl;
                            break;
                    }
                    try 
                    {
                            positions[k] = stof(value);
                        } catch (const std::invalid_argument& e) {
                            cerr << "Invalid float: " << value << endl;
                            positions[k] = 0.0f; // fallback
                    }
                }

                Ptr<MobilityModel> mobility = (*k)->GetObject<MobilityModel>();
                Vector position = mobility->GetPosition();
                position.z = 1.2;
                mobility->SetPosition(position);
                matrixLoss->SetLoss(gw_mobility, mobility, -positions[3]);
            }
        }
        loss = matrixLoss;
    }

    Ptr<PropagationDelayModel> delay = CreateObject<ConstantSpeedPropagationDelayModel>();
    Ptr<LoraChannel> channel = CreateObject<LoraChannel>(loss, delay);

        // Create the LoraPhyHelper
    LoraPhyHelper phyHelper = LoraPhyHelper();
    phyHelper.SetChannel(channel);

    // Create the LoraNetDevices of the end devices
    uint8_t nwkId = 54;
    uint32_t nwkAddr = 1864;
    Ptr<LoraDeviceAddressGenerator> addrGen =
        CreateObject<LoraDeviceAddressGenerator>(nwkId, nwkAddr);

    // Create the LoraNetDevices of the end devices
    macHelper.SetAddressGenerator(addrGen);
    phyHelper.SetDeviceType(LoraPhyHelper::ED);
    macHelper.SetDeviceType(LorawanMacHelper::ED_A);
    helper.Install(phyHelper, macHelper, endDevices);

    // Connect trace sources
    for (auto j = endDevices.Begin(); j != endDevices.End(); ++j)
    {
        Ptr<Node> node = *j;
        Ptr<LoraNetDevice> loraNetDevice = DynamicCast<LoraNetDevice>(node->GetDevice(0));
        Ptr<LoraPhy> phy = loraNetDevice->GetPhy();
    }

    // Create a netdevice for each gateway
    phyHelper.SetDeviceType(LoraPhyHelper::GW);
    macHelper.SetDeviceType(LorawanMacHelper::GW);
    helper.Install(phyHelper, macHelper, gateways);

    // Retrieve receiver power for each end device
    for (auto gw = gateways.Begin(); gw != gateways.End(); ++gw)
    {
        Ptr<MobilityModel> gw_mobility = (*gw)->GetObject<MobilityModel>();
        double rxPower = 0.0;
        Vector gw_position = gw_mobility->GetPosition();
        cout << gw_position << endl;
        for (auto k = endDevices.Begin(); k != endDevices.End(); ++k)
        {
            Ptr<MobilityModel> mobility = (*k)->GetObject<MobilityModel>();
            Vector position = mobility->GetPosition();
            position.z = 1.2;
            mobility->SetPosition(position);
            rxPower = channel->GetRxPower(10, gw_mobility, mobility);
            g_outFile << to_string(position.x) + "," + to_string(position.y) + "," + to_string(position.z) + "," + to_string(rxPower) << endl;
        }
    }
    /**********************
     *  Handle buildings  *
    **********************/

    double xLength = 130;
    double deltaX = 32;
    double yLength = 64;
    double deltaY = 17;
    int gridWidth = 2 * radiusMeters / (xLength + deltaX);
    int gridHeight = 2 * radiusMeters / (yLength + deltaY);
    if (!realisticChannelModel)
    {
        gridWidth = 0;
        gridHeight = 0;
    }
    Ptr<GridBuildingAllocator> gridBuildingAllocator;
    gridBuildingAllocator = CreateObject<GridBuildingAllocator>();
    gridBuildingAllocator->SetAttribute("GridWidth", UintegerValue(gridWidth));
    gridBuildingAllocator->SetAttribute("LengthX", DoubleValue(xLength));
    gridBuildingAllocator->SetAttribute("LengthY", DoubleValue(yLength));
    gridBuildingAllocator->SetAttribute("DeltaX", DoubleValue(deltaX));
    gridBuildingAllocator->SetAttribute("DeltaY", DoubleValue(deltaY));
    gridBuildingAllocator->SetAttribute("Height", DoubleValue(6));
    gridBuildingAllocator->SetBuildingAttribute("NRoomsX", UintegerValue(2));
    gridBuildingAllocator->SetBuildingAttribute("NRoomsY", UintegerValue(4));
    gridBuildingAllocator->SetBuildingAttribute("NFloors", UintegerValue(2));
    gridBuildingAllocator->SetAttribute(
        "MinX",
        DoubleValue(-gridWidth * (xLength + deltaX) / 2 + deltaX / 2));
    gridBuildingAllocator->SetAttribute(
        "MinY",
        DoubleValue(-gridHeight * (yLength + deltaY) / 2 + deltaY / 2));
    BuildingContainer bContainer = gridBuildingAllocator->Create(gridWidth * gridHeight);

    BuildingsHelper::Install(endDevices);
    BuildingsHelper::Install(gateways);

    // Print the buildings
    if (printBuildingInfo)
    {
        std::ofstream myfile;
        myfile.open("buildings.txt");
        std::vector<Ptr<Building>>::const_iterator it;
        int j = 1;
        for (it = bContainer.Begin(); it != bContainer.End(); ++it, ++j)
        {
            Box boundaries = (*it)->GetBoundaries();
            myfile << "set object " << j << " rect from " << boundaries.xMin << ","
                   << boundaries.yMin << " to " << boundaries.xMax << "," << boundaries.yMax
                   << std::endl;
        }
        myfile.close();
    }

    /**********************************************
     *  Set up the end device's spreading factor  *
     **********************************************/

    LorawanMacHelper::SetSpreadingFactorsUp(endDevices, gateways, channel);

    NS_LOG_DEBUG("Completed configuration");

    /*********************************************
     *  Install applications on the end devices  *
     *********************************************/

    Time appStopTime = Seconds(simulationTimeSeconds);
    PeriodicSenderHelper appHelper = PeriodicSenderHelper();
    appHelper.SetPeriod(Seconds(appPeriodSeconds));
    appHelper.SetPacketSize(23);
    Ptr<RandomVariableStream> rv =
        CreateObjectWithAttributes<UniformRandomVariable>("Min",
                                                          DoubleValue(0),
                                                          "Max",
                                                          DoubleValue(10));
    ApplicationContainer appContainer = appHelper.Install(endDevices);

    appContainer.Start(Time(0));
    appContainer.Stop(appStopTime);

    /**************************
     *  Create network server  *
     ***************************/

    // Create the network server node
    Ptr<Node> networkServer = CreateObject<Node>();

    // PointToPoint links between gateways and server
    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue("5Mbps"));
    p2p.SetChannelAttribute("Delay", StringValue("2ms"));
    // Store network server app registration details for later
    P2PGwRegistration_t gwRegistration;
    for (auto gw = gateways.Begin(); gw != gateways.End(); ++gw)
    {
        auto container = p2p.Install(networkServer, *gw);
        auto serverP2PNetDev = DynamicCast<PointToPointNetDevice>(container.Get(0));
        gwRegistration.emplace_back(serverP2PNetDev, *gw);

        Ptr<Node> gwNode = *gw;
        Ptr<LoraNetDevice> gwDev = DynamicCast<LoraNetDevice>(gwNode->GetDevice(0));
        if (!gwDev)
        {
            NS_LOG_ERROR("Gateway device is not LoraNetDevice");
            continue;
        }

        Ptr<LoraPhy> gwPhy = gwDev->GetPhy();
        // gwPhy->TraceConnectWithoutContext("ReceivedPacket", MakeCallback(&RxCallback));
    }

    // Create a network server for the network
    nsHelper.SetGatewaysP2P(gwRegistration);
    nsHelper.SetEndDevices(endDevices);
    nsHelper.Install(networkServer);

    // Create a forwarder for each gateway
    forHelper.Install(gateways);

    ////////////////
    // Simulation //
    ////////////////

    Simulator::Stop(appStopTime + Hours(1));

    NS_LOG_INFO("Running simulation...");
    Simulator::Run();

    Simulator::Destroy();
    g_outFile.close();

    ///////////////////////////
    // Print results to file //
    ///////////////////////////
    NS_LOG_INFO("Computing performance metrics...");

    LoraPacketTracker& tracker = helper.GetPacketTracker();
    std::cout << tracker.CountMacPacketsGlobally(Time(0), appStopTime + Hours(1)) << std::endl;

    return 0;
}
