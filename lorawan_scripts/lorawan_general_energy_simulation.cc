#include "ns3/basic-energy-source-helper.h"
#include "ns3/energy-module.h"
#include "ns3/lora-radio-energy-model-helper.h"
#include "ns3/class-a-end-device-lorawan-mac.h"
#include "ns3/command-line.h"
#include "ns3/file-helper.h"
#include "ns3/constant-position-mobility-model.h"
#include "ns3/propagation-module.h"
#include "ns3/three-gpp-propagation-loss-model.h"
#include "ns3/channel-condition-model.h"
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
#include<vector>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <filesystem>
namespace fs = std::filesystem;

using namespace ns3;
using namespace lorawan;
using namespace std;

NS_LOG_COMPONENT_DEFINE("ComplexLorawanNetworkExample");

// Network settings
int nDevices = 100;           //!< Number of end device nodes to create
int nGateways = 1;            //!< Number of gateway nodes to create
int gatewaysNumberPositions = 99;  //!< Number of possibles gateway positions
double radiusMeters = 6400;         //!< Radius (m) of the deployment
int spreadingFactor = 7;         //!< Radius (m) of the deployment
double simulationTimeSeconds = 600; //!< Scenario duration (s) in simulated time
string channelType = "nakagami"; //!< type of stochastic channel


// Channel model
bool realisticChannelModel = false; //!< Whether to use a more realistic channel model with
                                    //!< Buildings and correlated shadowing

int appPeriodSeconds = 60; //!< Duration (s) of the inter-transmission time of end devices

// Energy settings
double totalNetworkEnergy = 0;

static ofstream rxPowerResult;
static ofstream edEnergy;
static ofstream packetReceived;
static ofstream packetSent;
bool stochasticChannel = true;

uint32_t totalReceived = 0;
uint32_t totalSent = 0;

void 
RemainingEnergy(double oldValue, double remainingEnergy)
{
    std::cout << Simulator::Now().GetSeconds()
              << " Node "
              << Simulator::GetContext()
              << " E=" << remainingEnergy
              << " J\n";
}

void
RxCallback(Ptr<const Packet> packet, unsigned int iface)
{ 
    totalReceived++;
}

void
TxPacketSent(Ptr<const Packet> packet, unsigned int iface)
{
    totalSent++;

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
    cmd.AddValue("channelType",
                 "Type of stochastic channel that will be used in the simulation",
                 channelType);
    cmd.AddValue("spreadingFactor",
                 "Spreading factor number that will be used in the simulation",
                 spreadingFactor);
    cmd.Parse(argc, argv);

    // Set up logging
    LogComponentEnable("ComplexLorawanNetworkExample", LOG_LEVEL_ALL);

    /***********
     *  Setup  *
     ***********/

    string energy_results_dir = "../energy_results/sf_" + to_string(spreadingFactor);
    if (!fs::exists(energy_results_dir)) {
        fs::create_directories(energy_results_dir);
    }

    string path_gain_results_dir = "../path_gain_results/ns3/" + channelType;
    if (!fs::exists(path_gain_results_dir)) {
        fs::create_directories(path_gain_results_dir);
    }

    // Cleaning the outputs csv
    std::ofstream clearFile("../energy_results/sf_" + to_string(spreadingFactor) + "/energies.csv", std::ios::trunc);
    clearFile.close();

    for (int i = 0; i <= gatewaysNumberPositions; i++)
    {
        int gatewayNumber = i; // Gateway positions; need to be different from the end-device positions
        std::cout << "---------------------------------------------"<< std::endl;
        std::cout << "Gateway number: " << i << std::endl;
        // positions / path_gain
        string path_gain_results = "../path_gain_results/ns3/" + channelType + '/' 
                                                        + std::to_string(gatewayNumber) + ".csv";
        string energy_per_device = "../energy_results/sf_" + to_string(spreadingFactor) + '/'
                                                        + std::to_string(gatewayNumber) + ".csv";
        rxPowerResult.open(path_gain_results);
        edEnergy.open(energy_per_device);

        // Create the time value from the period
        Time appPeriod = Seconds(appPeriodSeconds); 
        cout << "simulation " << simulationTimeSeconds << endl;
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

        ifstream file("../path_gain_results/coordinates.csv");
        string line;

        // Make it so that nodes are at a certain height > 0 
        // Change file positions to match the gateway positions file
        float positions[4] = {0, 0, 0, 0};
        for (auto j = endDevices.Begin(); j != endDevices.End(); ++j)
        {
            getline(file, line);
            stringstream ss(line);
            string value;
            for (int k = 0; k < 4; ++k) {
                    if (!getline(ss, value, ',')) {
                        cerr << "Line " << line << "does not have 4 values!" << endl;
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

        std::ifstream file2("../path_gain_results/coordinates.csv");
        std::string line2;

        // Vectors
        std::vector<float> grid_positions_x;
        std::vector<float> grid_positions_y;
        std::vector<float> grid_positions_z;
        std::vector<int> cell_index_x;
        std::vector<int> cell_index_y;

        while (std::getline(file2, line2)) {

            if (line2.empty()) 
                continue;  // pula linhas vazias

            // trocar vírgulas por espaço
            for (char &c : line2) {
                if (c == ',') c = ' ';
            }

            float x, y, z;
            int idx_x, idx_y;

            std::stringstream ss(line2);

            if (!(ss >> x >> y >> z >> idx_x >> idx_y)) {
                std::cerr << "Error at line: " << line2 << std::endl;
                continue;
            }

            grid_positions_x.push_back(x);
            grid_positions_y.push_back(y);
            grid_positions_z.push_back(z);
            cell_index_x.push_back(idx_x);
            cell_index_y.push_back(idx_y);
        }

        Vector gatewayPosition = Vector(
            grid_positions_x[gatewayNumber],
            grid_positions_y[gatewayNumber],
            grid_positions_z[gatewayNumber]
        );

        file2.close();

        Ptr<ListPositionAllocator> allocator = CreateObject<ListPositionAllocator>();
        // Make it so that nodes are at a certain height > 0
        allocator->Add(gatewayPosition);
        mobility.SetPositionAllocator(allocator);
        mobility.Install(gateways);

        /***********************
        *  Create the channel  *
        ************************/
        int ed_index = 0;
        ifstream file3("../path_gain_results/coordinates.csv");
        std::string line3;

        Ptr<PropagationLossModel> loss;
        // Create the lora channel object
        if (channelType == "log") 
        {
            Ptr<LogDistancePropagationLossModel> lossDist = CreateObject<LogDistancePropagationLossModel>();
            lossDist->SetPathLossExponent(3.76);
            lossDist->SetReference(1, 7.7);
            loss = lossDist;
        } else if (channelType == "nakagami") {
            Ptr<NakagamiPropagationLossModel> nakagami = CreateObject<NakagamiPropagationLossModel> ();
            nakagami->SetAttribute ("m0", DoubleValue (1.0));    // d < d0
            nakagami->SetAttribute ("m1", DoubleValue (1.5));    // d0 ≤ d < d1
            nakagami->SetAttribute ("m2", DoubleValue (3.0));    // d ≥ d1
            nakagami->SetAttribute ("Distance1", DoubleValue (80.0));
            nakagami->SetAttribute ("Distance2", DoubleValue (200.0));
            loss = nakagami;
        } else if (channelType == "twoRay") {
            Ptr<TwoRayGroundPropagationLossModel> tworay = CreateObject<TwoRayGroundPropagationLossModel> ();
            tworay->SetAttribute ("SystemLoss", DoubleValue (1.0));
            tworay->SetAttribute ("HeightAboveZ", DoubleValue (1.5)); // antenna height
            loss = tworay;
        } else if (channelType == "okumura") {
            Ptr<OkumuraHataPropagationLossModel> okumura = CreateObject<OkumuraHataPropagationLossModel> ();
            loss = okumura;
        } else if (channelType == "threegpp") {
            Ptr<ThreeGppUmaPropagationLossModel> threeGpp = CreateObject<ThreeGppUmaPropagationLossModel>();
            loss = threeGpp;
        } else if (channelType == "cost") {
            Ptr<Cost231PropagationLossModel> cost231 = CreateObject<Cost231PropagationLossModel>();
            loss = cost231;
        } else if (channelType == "rt") {
            // Informations from the radio map
            int num_tx = 100;
            size_t dim1 = 677;
            size_t dim2 = 854;

            // Create a 3D vector: tx x rows x columns
            std::vector<std::vector<std::vector<float>>> all_tx(num_tx,
                std::vector<std::vector<float>>(dim1, std::vector<float>(dim2)));

            // Saving the path gains / binaries for each gateway 
            for (int tx = 0; tx < num_tx; ++tx) {
                std::string filename = "../path_gain_results/sionna/bin/tx_" + std::to_string(tx) + ".bin";
                std::ifstream file(filename, std::ios::binary);

                if (!file.is_open()) {
                    std::cerr << "File not found " << filename << std::endl;
                    continue;
                }

                std::vector<float> data(dim1*dim2);
                file.read(reinterpret_cast<char*>(data.data()), dim1*dim2*sizeof(float));

                for (size_t i = 0; i < dim1; ++i) {
                    for (size_t j = 0; j < dim2; ++j) {
                        all_tx[tx][i][j] = data[i*dim2 + j];
                    }
                }
            }

            Ptr<MatrixPropagationLossModel> matrixLoss = CreateObject<MatrixPropagationLossModel> ();
            for (auto gw = gateways.Begin(); gw != gateways.End(); ++gw)
            {
                Ptr<MobilityModel> gw_mobility = (*gw)->GetObject<MobilityModel>();
                Vector gw_position = gw_mobility->GetPosition();
                cout << "Gateway: " << gatewayNumber << "  gw_position:" << gw_position << endl;
                std::cout << "--------------------------------" << std::endl;
                for (auto k = endDevices.Begin(); k != endDevices.End(); ++k, ++ed_index)
                {
                    Ptr<MobilityModel> mobility = (*k)->GetObject<MobilityModel>();
                    Vector position = mobility->GetPosition();
                    position.z = 1.2;

                    float px = position.x;
                    float py = position.y;

                    // Find the end-device position in all grid positions
                    int foundIndex = -1;
                    for (size_t i = 0; i < grid_positions_x.size(); i++)
                    {
                        if (grid_positions_x[i] == px && grid_positions_y[i] == py)
                        {
                            foundIndex = i;
                            break;
                        }
                    }

                    if (foundIndex == -1)
                    {
                        std::cerr << "ERROR: position (" << px << ", " << py << ") not found!" << std::endl;
                    }
                    else
                    {
                        std::cout << "End-device: " << ed_index << std::endl;
                        std::cout << "Match found at line: " << foundIndex << std::endl;
                        std::cout << "Cell index X = " << cell_index_x[foundIndex] 
                                << " | Cell index Y = " << cell_index_y[foundIndex] << std::endl;
                        std::cout << "position.x= " << position.x << "  position.y= " << position.y << std::endl;

                        float path_gain = all_tx[gatewayNumber][cell_index_x[foundIndex]][cell_index_y[foundIndex]];
                        std::cout << "path_gain= " << path_gain << std::endl;
                        std::cout << "--------------------------------" << std::endl;
                        mobility->SetPosition(position);
                        matrixLoss->SetLoss(gw_mobility, mobility, -path_gain); // Is the path gain for the end-device positions ?
                    }
                }
            }
            loss = matrixLoss;
        }

        Ptr<PropagationDelayModel> delay = CreateObject<ConstantSpeedPropagationDelayModel>();
        Ptr<LoraChannel> channel = CreateObject<LoraChannel>(loss, delay);

        // Create the LoraPhyHelper
        LoraPhyHelper phyHelper = LoraPhyHelper();
        phyHelper.SetChannel(channel);
        // phyHelper.Set("TxPower", DoubleValue(14));

        // Create the LoraNetDevices of the end devices
        uint8_t nwkId = 54;
        uint32_t nwkAddr = 1864;
        Ptr<LoraDeviceAddressGenerator> addrGen =
            CreateObject<LoraDeviceAddressGenerator>(nwkId, nwkAddr);

        // Create the LoraNetDevices of the end devices
        macHelper.SetAddressGenerator(addrGen);
        phyHelper.SetDeviceType(LoraPhyHelper::ED);
        macHelper.SetDeviceType(LorawanMacHelper::ED_A);
        NetDeviceContainer endDevicesNetDevices = helper.Install(phyHelper, macHelper, endDevices);

        // =====================
        // Energy (End Devices)
        // =====================

        // Defining the battery helper
        GenericBatteryModelHelper batteryHelper;

        // Using the Li-Ion preset
        EnergySourceContainer energySources = batteryHelper.Install(endDevices, PANASONIC_CGR18650DA_LION);
        batteryHelper.SetCellPack(energySources, 2, 2); // 2S 2P

        // Using SX1276 as a base
        LoraRadioEnergyModelHelper radioEnergyHelper;
        radioEnergyHelper.Set("TxCurrentA", DoubleValue(0.044));
        radioEnergyHelper.Set("RxCurrentA", DoubleValue(0.0112));
        radioEnergyHelper.Set("StandbyCurrentA", DoubleValue(0.0014));
        radioEnergyHelper.Set("SleepCurrentA", DoubleValue(0.0000015));

        // Connect the radio energy model to the end devices netdevices
        DeviceEnergyModelContainer deviceModels =
            radioEnergyHelper.Install(endDevicesNetDevices, energySources);

        // Connect trace sources
        for (auto j = endDevices.Begin(); j != endDevices.End(); ++j)
        {
            Ptr<Node> node = *j;
            Ptr<LoraNetDevice> loraNetDevice = DynamicCast<LoraNetDevice>(node->GetDevice(0));
            Ptr<LoraPhy> phy = loraNetDevice->GetPhy();
            Ptr<LorawanMac> mac = loraNetDevice->GetMac();
            mac->SetAttribute("DataRate", UintegerValue(12-spreadingFactor)); // set spreading factor
            phy->TraceConnectWithoutContext("StartSending", MakeCallback(&TxPacketSent));
            
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
            for (auto k = endDevices.Begin(); k != endDevices.End(); ++k)
            {
                Ptr<MobilityModel> mobility = (*k)->GetObject<MobilityModel>();
                Vector position = mobility->GetPosition();
                position.z = 30;
                mobility->SetPosition(position);
                rxPower = channel->GetRxPower(10, gw_mobility, mobility);
                rxPowerResult << to_string(position.x) + "," + to_string(position.y) + "," + 
                                                        to_string(position.z) + "," + to_string(rxPower) << endl;
            }
        }

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
            gwPhy->TraceConnectWithoutContext("ReceivedPacket", MakeCallback(&RxCallback));
        }

        // Create a network server for the network
        nsHelper.SetGatewaysP2P(gwRegistration);
        nsHelper.SetEndDevices(endDevices);
        nsHelper.Install(networkServer);

        // Create a forwarder for each gateway
        forHelper.Install(gateways);

        // Getting the initial energy through the remaining energy function because the GetInitialEnergy is inconsistent
        std::vector<double> initialEnergy(energySources.GetN());
        for (uint32_t i = 0; i < energySources.GetN(); ++i){
            initialEnergy[i] = energySources.Get(i)->GetRemainingEnergy();
        }

        ////////////////
        // Simulation //
        ////////////////

        Simulator::Stop(appStopTime + Hours(1));

        NS_LOG_INFO("Running simulation...");
        Simulator::Run();

        packetReceived.open("../path_gain_results/" + channelType + "/packet_received-" + channelType + ".txt" , std::ios::app);
        packetReceived << to_string(totalReceived) + ",";
        packetReceived.close();

        packetSent.open("../path_gain_results/ns3/" + channelType + "/packet_sent-" + channelType + ".txt", std::ios::app);
        packetSent << to_string(totalSent) + ",";
        packetSent.close();
        file3.close();
        rxPowerResult.close();

        // Energy debug
        double totalConsumedByEDs = 0.0;
        for (uint32_t i = 0; i < energySources.GetN(); ++i){
            // double initialEnergy = energySources.Get(i)->GetInitialEnergy();
            double remaining = energySources.Get(i)->GetRemainingEnergy();
            double totalConsumedByEDi = 0;
            totalConsumedByEDi += (initialEnergy[i] - remaining);
            cout << "ED: " << i << ", " << "Energy used: " << totalConsumedByEDi << " J" << std::endl;
            edEnergy << totalConsumedByEDi << std::endl;
            totalConsumedByEDs += totalConsumedByEDi;
        }
        edEnergy.close();
        Simulator::Destroy();

        //////////////////////////////////
        // Print results to file or not //
        /////////////////////////////////
        NS_LOG_INFO("Computing performance metrics...");

        LoraPacketTracker& tracker = helper.GetPacketTracker();
        std::cout << tracker.CountMacPacketsGlobally(Time(0), appStopTime + Hours(1)) << std::endl;
        float pdr = float(totalReceived)/float(totalSent);
        std::cout << "PDR: " << pdr << std::endl;
        std::cout << "Total run energy used: " << totalConsumedByEDs << " J" << std::endl;
        std::ofstream runTotalEnergy;
        runTotalEnergy.open("../energy_results/sf_" + to_string(spreadingFactor) + "/energies.csv", std::ios::app);
        runTotalEnergy << "GW:" << gatewayNumber;
        runTotalEnergy << ", ";
        runTotalEnergy << totalConsumedByEDs << "\n";
        runTotalEnergy.close();
        totalNetworkEnergy += totalConsumedByEDs;
    }
    std::cout << "----------------------------------------" << std::endl;
    std::cout << "Total network energy used: " << totalNetworkEnergy << " J" << std::endl;
    return 0;
}
