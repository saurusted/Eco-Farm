import json        #Handles reading and writing data to offline JSON files
import os          #Checks if saved JSON files already exist on the computer
import uuid        #Generates unique IDs for newly created devices
from collections import deque        #Provides fast queue structure for Breadth-First Searcg(BFS)
from datetime import datetime        #Captures the current date and time for logs and alerts


import matplotlib.pyplot as plt      #Draws line charts and network topology graohs
import networkx as nx                #Creates and manages the offline mesh network (nodes and connections)
import pandas as pd                  #Organizes farm records into tables annd computes statistical summaries


# Main storage variables #json gagamitin
devices = {}               #Stores registered device as {device_id: device_name}
farm_data = []             #Stores a chronological list of all sensor reading dictionaries
messages = []              #Stores a list of all sent offline message records
alerts = []                #Stores warnings and alerts when readings exceed safe
network = nx.Graph()       #Initialzes an empty undirected graph for device connections


# Offline JSON save files #json
FARM_DATA_FILE = "farm_data.json" 
MESSAGES_FILE = "messages.json"
ALERTS_FILE = "alerts.json"
NETWORK_FILE = "network_data.json"




# Helper: Finds the shortest path between two offline devices (BFS) #networkx gagamitin
def bfs_communication_path(graph, start_device, target_device):
    visited = set([start_device])       #Tracks already-checked devices to avoid infinite loops
    queue = deque([[start_device]])     #Queue storing possible routes starting from the sender

    while queue:
        path = queue.popleft()          #Removes and inspects the oldest route in the queue
        current_device = path[-1]       #Gets the last device reached in the current route

        if current_device == target_device:    #Stops an dreturns the route once the receiver is reached
            return path

        for neighbor in graph.neighbors(current_device):    #Checks all directly connected devices
            if neighbor not in visited:
                visited.add(neighbor)        #Marks neighbor as visited
                new_path = list(path)        #Copies the current path
                new_path.append(neighbor)    #Extends the path to include the neighbor
                queue.append(new_path)       #Add the extemded path to the queue for further exploration
                
    return None

# Helper: Loads saved data from JSON files when the app opens #os gagamitin
def load_all_data():
    global devices, farm_data, messages, alerts, network    #Allows updating the main global variables


    if os.path.exists(FARM_DATA_FILE):            #Loads saved sensor readings if the file exists
        with open(FARM_DATA_FILE, "r") as f:
            farm_data = json.load(f)


    if os.path.exists(MESSAGES_FILE):             #Loads saved message history if the file exists
        with open(MESSAGES_FILE, "r") as f:
            messages = json.load(f)


    if os.path.exists(ALERTS_FILE):               #Loads saved alert logs if the file exists
        with open(ALERTS_FILE, "r") as f:
            alerts = json.load(f)


    if os.path.exists(NETWORK_FILE):              #Loads saved devices and rebuilds the NetworkX graph
        with open(NETWORK_FILE, "r") as f:
            saved_net = json.load(f)
            devices = saved_net.get("devices", {})            #Extracts saved device dictionary
            connections = saved_net.get("connections", [])    #extracts saved device links


            for dev_id, dev_name in devices.items():
                network.add_node(dev_id, name=dev_name)       #Re-adds each device as a node in the graph
            for u, v in connections:
                if u in devices and v in devices:
                    network.add_edge(u, v)                    #Reconnects valid device pairs in the graph



#pandas then return sa json
def monitor_farm(farm_data):
    latest_record = {}
    print("\n========== FARM MONITORING ==========")


    if len(farm_data) > 0:            #Runs only if at least one sensor reading has been recorded
        print("LATEST FARM READINGS")
        latest_record = farm_data[-1] #Fetches the most recently added record (last item in list)


        print("Device ID:", latest_record["device_id"])
        print("Temperature:", latest_record["temperature"], "°C")
        print("Soil Moisture:", latest_record["soil_moisture"], "%")
        print("Water Level:", latest_record["water_level"], "%")
        print("Date and Time:", latest_record["timestamp"])


        df = pd.DataFrame(farm_data)        #Converts the list of records into a Pandas table
        print("\n--- FARM DATA SUMMARY ---")
        print(df[["temperature", "soil_moisture", "water_level"]].describe())    #Shows count, mean, min, and max stats


        #Creates a 3-row stacked figure sharing the same timestamp x-axis
        fig, axes = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
        fig.suptitle("ECO FARM - Sensor Condition Trends", fontsize=14, fontweight="bold")


        #Plots Temperature trend and draws a red dahsed hreshold line at 35°
        axes[0].plot(df["timestamp"], df["temperature"], marker="o", color="tab:red", label="Temperature (°C)")
        axes[0].axhline(35, color="red", linestyle="--", linewidth=1, label="Alert Limit (>35°C)")
        axes[0].set_ylabel("Temp (°C)")
        axes[0].set_title("Temperature Over Time")
        axes[0].legend(loc="upper right")
        axes[0].grid(True, linestyle=":", alpha=0.6)


        #Plots Soil Moisture trend and draws an orange dahsed threshold line at 30%
        axes[1].plot(df["timestamp"], df["soil_moisture"], marker="s", color="tab:green", label="Soil Moisture (%)")
        axes[1].axhline(30, color="orange", linestyle="--", linewidth=1, label="Alert Limit (<30%)")
        axes[1].set_ylabel("Moisture (%)")
        axes[1].set_title("Soil Moisture Over Time")
        axes[1].legend(loc="upper right")
        axes[1].grid(True, linestyle=":", alpha=0.6)


        #Plost Water Level trend and draws a purple dashed threshold in line at 30%
        axes[2].plot(df["timestamp"], df["water_level"], marker="^", color="tab:blue", label="Water Level (%)")
        axes[2].axhline(30, color="purple", linestyle="--", linewidth=1, label="Alert Limit (<30%)")
        axes[2].set_ylabel("Water (%)")
        axes[2].set_xlabel("Date and Time")
        axes[2].set_title("Water Level Over Time")
        axes[2].legend(loc="upper right")
        axes[2].grid(True, linestyle=":", alpha=0.6)


        #FORMATTING LANG
        plt.xticks(rotation=30, ha="right") 
        plt.tight_layout()                  
        plt.show()


    else:
        print("No farm readings available.")
        print("Please add farm data first.")



#datetime
def add_farm_data():
    print("\n--- AVAILABLE DEVICES ---")
    for dev_id, dev_name in devices.items():
        print(f"ID: {dev_id} | Name: {dev_name}")


    selected_device = input("\nEnter Device ID: ").strip()

    
    if selected_device in devices:      #verifies that the entered device id exist
        try:
            #converts user text inputs into decimal numbers (floats)
            temperature = float(input("Enter Temperature (°C): "))
            soil_moisture = float(input("Enter Soil Moisture (%): "))
            water_level = float(input("Enter Water Level (%): "))

            #check that moisture/water are valid percentage and if temperature is realistic
            if not (0 <= soil_moisture <= 100 and 0 <= water_level <= 100 and -50 <= temperature <= 100):
                print("Invalid sensor readings.")
                return


            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            #packages all inputs and metadata into a single dictionary record
            farm_record = {
                "device_id": selected_device,
                "device_name": devices[selected_device],
                "temperature": temperature,
                "soil_moisture": soil_moisture,
                "water_level": water_level,
                "timestamp": timestamp,
            }
            farm_data.append(farm_record)    #saves the new record to the main farm_data list

            # check if temperature exceeds 35°C and logs a high temperature alert
            if temperature > 35:
                temp_alert = {
                    "type": "HIGH TEMPERATURE",
                    "device_id": selected_device,
                    "message": f"High temperature ({temperature}°C > 35°C) on {devices[selected_device]}",
                    "timestamp": timestamp,
                }
                alerts.append(temp_alert)
                print("ALERT GENERATED:", temp_alert["message"])

            # checks if soil moisture drop below 30% and logs a low soil moisture
            if soil_moisture < 30:
                moisture_alert = {
                    "type": "LOW SOIL MOISTURE",
                    "device_id": selected_device,
                    "message": f"Low soil moisture ({soil_moisture}% < 30%) on {devices[selected_device]}",
                    "timestamp": timestamp,
                }
                alerts.append(moisture_alert)
                print("ALERT GENERATED:", moisture_alert["message"])

            #checks water level
            if water_level < 30:
                water_alert = {
                    "type": "LOW WATER LEVEL",
                    "device_id": selected_device,
                    "message": f"Low water level ({water_level}% < 30%) on {devices[selected_device]}",
                    "timestamp": timestamp,
                }
                alerts.append(water_alert)
                print("ALERT GENERATED:", water_alert["message"])

            #finds all directly connected devices in the mesh to simulate offline data syncing
            connected_peers = list(network.neighbors(selected_device))
            if connected_peers:
                peer_names = [f"{devices[p]} ({p})" for p in connected_peers]
                print("Shared with connected devices:", ", ".join(peer_names))


            print("Farm data saved and shared with connected devices.")


        except ValueError:
            print("Invalid sensor readings. Please enter numbers only.")
    else:
        print("Device not found.")



#balik sa networkx
def send_offline_message():
    print("\n--- AVAILABLE DEVICES ---")
    for dev_id, dev_name in devices.items():
        print(f"ID: {dev_id} | Name: {dev_name}")


    sender = input("\nEnter Sender Device ID: ").strip()
    receiver = input("Enter Receiver Device ID: ").strip()
    message = input("Enter Message: ").strip()


    if sender in devices and receiver in devices:        #ensures both sender and receiver are valid devices
        path = bfs_communication_path(network, sender, receiver)    #finds shortest multi-hop route via BFS


        if path is not None:        #executes if a valid mesh route connects sender and receiver
            route_display = " -> ".join([f"{devices[node]} ({node})" for node in path])    #this will format the hop sequence
            print("Communication Path (BFS):", route_display)


            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message_record = {
                "sender": sender,
                "receiver": receiver,
                "message": message,
                "path": path,
                "timestamp": timestamp,
            }
            messages.append(message_record)        #saves message and route details to messages list
            print("Message sent successfully.")
        else:
            print("No communication path available.")
    else:
        print("Device not found.")

#kasama ng send offline messages
def view_messages():
    print("\n========== OFFLINE MESSAGES ==========")
    if len(messages) > 0:
        for idx, msg in enumerate(messages, start=1):            #loops through messages with a 1-based counter
            sender_name = devices.get(msg["sender"], msg["sender"])    #this will convert the senders id to a readable name
            receiver_name = devices.get(msg["receiver"], msg["receiver"])    #converts receiver id to readable name
            print(f"{idx}. [{msg['timestamp']}] {sender_name} -> {receiver_name}: {msg['message']}")
    else:
        print("No offline messages sent yet.")



# pag walang keywords, ilagay sa main (pero pwede rin ihiwalay)
def view_alerts():
    print("\n========== FARM ALERTS ==========")


    if len(alerts) > 0:
        for idx, alert in enumerate(alerts, start=1):        #displays every saved alert in numbered order
            print(f"{idx}. [{alert['timestamp']}] {alert['type']} | {alert['message']}")
    else:
        print("No alerts available.")



#balik sa pandas
def view_data_history(farm_data):
    print("\n========== FARM DATA HISTORY ==========")


    if len(farm_data) > 0:
        df = pd.DataFrame(farm_data)    #loads all the saved raedings into a pandas dataframe


        print("\n--- ALL PREVIOUS FARM READINGS ---")
        print(df.to_string(index=False))        #prints the complete table cleanly witjout row index numbers


        print("\n--- DATA SUMMARY (PANDAS) ---")
        print(df[["temperature", "soil_moisture", "water_level"]].describe())    #prints statistical summary
    else:
        print("No farm history available.")



#under ng uuid
def manage_devices():
    print("\n===== MANAGE DEVICES =====")
    print("1. Add Device")
    print("2. Remove Device")
    print("3. Add Connection")
    print("4. Remove Connection")


    device_choice = input("Enter choice (1-4): ").strip()


    if device_choice == "1":
        device_name = input("Enter Device Name: ").strip()
        new_id = str(uuid.uuid4())[:8]    #generates an 8-character unique id using uuid
        devices[new_id] = device_name    #registers the new device in the devices dictionary
        network.add_node(new_id, name=device_name)       #adds the device as a nde in the mesh group
        print(f"Device successfully added. (Name: {device_name}, ID: {new_id})")


    elif device_choice == "2":
        device_id = input("Enter Device ID to remove: ").strip()
        if device_id in devices:
            del devices[device_id]    #delete device from the device dictionary
            if network.has_node(device_id):
                network.remove_node(device_id) #removes the node and deletes its links
            print("Device successfully removed.")
        else:
            print("Device not found.")


    elif device_choice == "3":
        first_device = input("Enter First Device ID: ").strip()
        second_device = input("Enter Second Device ID: ").strip()


        if first_device in devices and second_device in devices:
            network.add_edge(first_device, second_device)    #creates a two way mesh link
            print("Connection successfully added.")
        else:
            print("Invalid device.")


    elif device_choice == "4":
        first_device = input("Enter First Device ID: ").strip()
        second_device = input("Enter Second Device ID: ").strip()


        if network.has_edge(first_device, second_device):    #checks of a link actually exists before removing
            network.remove_edge(first_device, second_device)    #disconnects the two devices 
            print("Connection successfully removed.")
        else:
            print("Connection not found.")


    else:
        print("Invalid choice.")



#networkx
def view_mesh_network():
    print("\n========== MESH NETWORK ==========")


    print("Registered Devices:")
    for node_id in network.nodes():    #lists every device node currently in the graph
        print(f" - {devices.get(node_id, 'Unknown')} (ID: {node_id})")


    print("\nNetwork Connections:")
    if network.number_of_edges() > 0:
        for u, v in network.edges():    #lists every active pair of connected devices
            print(f" - {devices.get(u, u)} ({u}) <---> {devices.get(v, v)} ({v})")
    else:
        print(" - No active connections.")


    plt.figure(figsize=(7, 5))        #creates a new window for the network diagram
    pos = nx.spring_layout(network, seed=42)    
    labels = {node_id: f"{devices.get(node_id, '')}\n({node_id})" for node_id in network.nodes()}


    nx.draw(
        network,
        pos,
        with_labels=True,
        labels=labels,
        node_color="#74c69d",
        node_size=2600,
        font_size=9,
        font_weight="bold",
        edge_color="#2d6a4f",
        width=2,                    #renders the mesh diagram window
    )
    plt.title("ECO FARM - Offline Mesh Network", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.show()



#json
def save_all_data():
    with open(FARM_DATA_FILE, "w") as f:    #overwrites farm_data.json with formatted data
        json.dump(farm_data, f, indent=4)


    with open(MESSAGES_FILE, "w") as f:    #overwrites messages.json with formatted data messages
        json.dump(messages, f, indent=4)


    with open(ALERTS_FILE, "w") as f:    #overwrites alerts.json with formatted alerts
        json.dump(alerts, f, indent=4)


    network_payload = {
        "devices": devices,
        "connections": [list(edge) for edge in network.edges()],
    }
    with open(NETWORK_FILE, "w") as f:
        json.dump(network_payload, f, indent=4)



def main():
    load_all_data()        #restores any previously saved data from json files on start up


    if len(devices) == 0:        #creates 4 default devices only on the very first run 
        default_names = ["Device A", "Device B", "Device C", "Device D"]
        created_ids = []


        for name in default_names:
            dev_id = str(uuid.uuid4())[:8]
            devices[dev_id] = name
            network.add_node(dev_id, name=name)
            created_ids.append(dev_id)

        #sets up initial ring mesh connections
        network.add_edge(created_ids[0], created_ids[1])  # A - B
        network.add_edge(created_ids[1], created_ids[2])  # B - C
        network.add_edge(created_ids[2], created_ids[3])  # C - D
        network.add_edge(created_ids[0], created_ids[3])  # A - D


        save_all_data()        #saves the initial default network immeediately

    #display startup system  status summary
    print("==========================================")
    print("      ECO FARM OFFLINE CONTROL PANEL      ")
    print("==========================================")
    print(f"Connected Devices : {len(devices)} | Mesh Links: {network.number_of_edges()}")
    print(f"Saved Readings    : {len(farm_data)} | Active Alerts: {len(alerts)}")


    running = True        #controls the main loop


    while running:
        print("\n========== ECO FARM ==========")
        print("1. Monitor Farm")
        print("2. Add Farm Data")
        print("3. Send Offline Message")
        print("4. View Alerts")
        print("5. View Data History")
        print("6. Manage Devices")
        print("7. View Mesh Network")
        print("8. View Messages")
        print("9. Exit")


        menu_choice = input("Enter choice (1-9): ").strip()    #reads user's menu selecction

        #calls the matching function based on the user's input
        if menu_choice == "1":
            monitor_farm(farm_data)
        elif menu_choice == "2":
            add_farm_data()
        elif menu_choice == "3":
            send_offline_message()
        elif menu_choice == "4":
            view_alerts()
        elif menu_choice == "5":
            view_data_history(farm_data)
        elif menu_choice == "6":
            manage_devices()
        elif menu_choice == "7":
            view_mesh_network()
        elif menu_choice == "8":
            view_messages()
        elif menu_choice == "9":
            running = False        #ends the while loop
            print("Exiting ECO FARM...")
        else:
            print("Invalid choice. Please try again.")


        save_all_data()


    print("Thank you for using ECO FARM!")        #automatically savves all changes to json after every menu action




if __name__ == "__main__":        #ensures main()  runs only when this file is executed directly
    main()
