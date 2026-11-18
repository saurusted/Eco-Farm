import json
import os
import uuid
from collections import deque
from datetime import datetime


import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


# Main storage variables #json gagamitin
devices = {}
farm_data = []
messages = []
alerts = []
network = nx.Graph()


# Offline JSON save files #json
FARM_DATA_FILE = "farm_data.json" 
MESSAGES_FILE = "messages.json"
ALERTS_FILE = "alerts.json"
NETWORK_FILE = "network_data.json"




# Helper: Finds the shortest path between two offline devices (BFS) #networkx gagamitin
def bfs_communication_path(graph, start_device, target_device):
    visited = set([start_device])
    queue = deque([[start_device]])


    while queue:
        path = queue.popleft()
        current_device = path[-1]


        if current_device == target_device:
            return path


        for neighbor in graph.neighbors(current_device):
            if neighbor not in visited:
                visited.add(neighbor)
                new_path = list(path)
                new_path.append(neighbor)
                queue.append(new_path)


    return None




# Helper: Loads saved data from JSON files when the app opens #os gagamitin
def load_all_data():
    global devices, farm_data, messages, alerts, network


    if os.path.exists(FARM_DATA_FILE):
        with open(FARM_DATA_FILE, "r") as f:
            farm_data = json.load(f)


    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, "r") as f:
            messages = json.load(f)


    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, "r") as f:
            alerts = json.load(f)


    if os.path.exists(NETWORK_FILE):
        with open(NETWORK_FILE, "r") as f:
            saved_net = json.load(f)
            devices = saved_net.get("devices", {})
            connections = saved_net.get("connections", [])


            for dev_id, dev_name in devices.items():
                network.add_node(dev_id, name=dev_name)
            for u, v in connections:
                if u in devices and v in devices:
                    network.add_edge(u, v)




def monitor_farm(farm_data):
    latest_record = {}
    print("\n========== FARM MONITORING ==========")


    if len(farm_data) > 0:
        print("LATEST FARM READINGS")
        latest_record = farm_data[-1]


        print("Device ID:", latest_record["device_id"])
        print("Temperature:", latest_record["temperature"], "°C")
        print("Soil Moisture:", latest_record["soil_moisture"], "%")
        print("Water Level:", latest_record["water_level"], "%")
        print("Date and Time:", latest_record["timestamp"])


        df = pd.DataFrame(farm_data)
        print("\n--- FARM DATA SUMMARY ---")
        print(df[["temperature", "soil_moisture", "water_level"]].describe())


        fig, axes = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
        fig.suptitle("ECO FARM - Sensor Condition Trends", fontsize=14, fontweight="bold")


        axes[0].plot(df["timestamp"], df["temperature"], marker="o", color="tab:red", label="Temperature (°C)")
        axes[0].axhline(35, color="red", linestyle="--", linewidth=1, label="Alert Limit (>35°C)")
        axes[0].set_ylabel("Temp (°C)")
        axes[0].set_title("Temperature Over Time")
        axes[0].legend(loc="upper right")
        axes[0].grid(True, linestyle=":", alpha=0.6)


        axes[1].plot(df["timestamp"], df["soil_moisture"], marker="s", color="tab:green", label="Soil Moisture (%)")
        axes[1].axhline(30, color="orange", linestyle="--", linewidth=1, label="Alert Limit (<30%)")
        axes[1].set_ylabel("Moisture (%)")
        axes[1].set_title("Soil Moisture Over Time")
        axes[1].legend(loc="upper right")
        axes[1].grid(True, linestyle=":", alpha=0.6)


        axes[2].plot(df["timestamp"], df["water_level"], marker="^", color="tab:blue", label="Water Level (%)")
        axes[2].axhline(30, color="purple", linestyle="--", linewidth=1, label="Alert Limit (<30%)")
        axes[2].set_ylabel("Water (%)")
        axes[2].set_xlabel("Date and Time")
        axes[2].set_title("Water Level Over Time")
        axes[2].legend(loc="upper right")
        axes[2].grid(True, linestyle=":", alpha=0.6)


        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.show()


    else:
        print("No farm readings available.")
        print("Please add farm data first.")




def add_farm_data():
    print("\n--- AVAILABLE DEVICES ---")
    for dev_id, dev_name in devices.items():
        print(f"ID: {dev_id} | Name: {dev_name}")


    selected_device = input("\nEnter Device ID: ").strip()


    if selected_device in devices:
        try:
            temperature = float(input("Enter Temperature (°C): "))
            soil_moisture = float(input("Enter Soil Moisture (%): "))
            water_level = float(input("Enter Water Level (%): "))


            if not (0 <= soil_moisture <= 100 and 0 <= water_level <= 100 and -50 <= temperature <= 100):
                print("Invalid sensor readings.")
                return


            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


            farm_record = {
                "device_id": selected_device,
                "device_name": devices[selected_device],
                "temperature": temperature,
                "soil_moisture": soil_moisture,
                "water_level": water_level,
                "timestamp": timestamp,
            }
            farm_data.append(farm_record)


            if temperature > 35:
                temp_alert = {
                    "type": "HIGH TEMPERATURE",
                    "device_id": selected_device,
                    "message": f"High temperature ({temperature}°C > 35°C) on {devices[selected_device]}",
                    "timestamp": timestamp,
                }
                alerts.append(temp_alert)
                print("ALERT GENERATED:", temp_alert["message"])


            if soil_moisture < 30:
                moisture_alert = {
                    "type": "LOW SOIL MOISTURE",
                    "device_id": selected_device,
                    "message": f"Low soil moisture ({soil_moisture}% < 30%) on {devices[selected_device]}",
                    "timestamp": timestamp,
                }
                alerts.append(moisture_alert)
                print("ALERT GENERATED:", moisture_alert["message"])


            if water_level < 30:
                water_alert = {
                    "type": "LOW WATER LEVEL",
                    "device_id": selected_device,
                    "message": f"Low water level ({water_level}% < 30%) on {devices[selected_device]}",
                    "timestamp": timestamp,
                }
                alerts.append(water_alert)
                print("ALERT GENERATED:", water_alert["message"])


            connected_peers = list(network.neighbors(selected_device))
            if connected_peers:
                peer_names = [f"{devices[p]} ({p})" for p in connected_peers]
                print("Shared with connected devices:", ", ".join(peer_names))


            print("Farm data saved and shared with connected devices.")


        except ValueError:
            print("Invalid sensor readings. Please enter numbers only.")
    else:
        print("Device not found.")




def send_offline_message():
    print("\n--- AVAILABLE DEVICES ---")
    for dev_id, dev_name in devices.items():
        print(f"ID: {dev_id} | Name: {dev_name}")


    sender = input("\nEnter Sender Device ID: ").strip()
    receiver = input("Enter Receiver Device ID: ").strip()
    message = input("Enter Message: ").strip()


    if sender in devices and receiver in devices:
        path = bfs_communication_path(network, sender, receiver)


        if path is not None:
            route_display = " -> ".join([f"{devices[node]} ({node})" for node in path])
            print("Communication Path (BFS):", route_display)


            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message_record = {
                "sender": sender,
                "receiver": receiver,
                "message": message,
                "path": path,
                "timestamp": timestamp,
            }
            messages.append(message_record)
            print("Message sent successfully.")
        else:
            print("No communication path available.")
    else:
        print("Device not found.")


def view_messages():
    print("\n========== OFFLINE MESSAGES ==========")
    if len(messages) > 0:
        for idx, msg in enumerate(messages, start=1):
            sender_name = devices.get(msg["sender"], msg["sender"])
            receiver_name = devices.get(msg["receiver"], msg["receiver"])
            print(f"{idx}. [{msg['timestamp']}] {sender_name} -> {receiver_name}: {msg['message']}")
    else:
        print("No offline messages sent yet.")




def view_alerts():
    print("\n========== FARM ALERTS ==========")


    if len(alerts) > 0:
        for idx, alert in enumerate(alerts, start=1):
            print(f"{idx}. [{alert['timestamp']}] {alert['type']} | {alert['message']}")
    else:
        print("No alerts available.")




def view_data_history(farm_data):
    print("\n========== FARM DATA HISTORY ==========")


    if len(farm_data) > 0:
        df = pd.DataFrame(farm_data)


        print("\n--- ALL PREVIOUS FARM READINGS ---")
        print(df.to_string(index=False))


        print("\n--- DATA SUMMARY (PANDAS) ---")
        print(df[["temperature", "soil_moisture", "water_level"]].describe())
    else:
        print("No farm history available.")




def manage_devices():
    print("\n===== MANAGE DEVICES =====")
    print("1. Add Device")
    print("2. Remove Device")
    print("3. Add Connection")
    print("4. Remove Connection")


    device_choice = input("Enter choice (1-4): ").strip()


    if device_choice == "1":
        device_name = input("Enter Device Name: ").strip()
        new_id = str(uuid.uuid4())[:8]
        devices[new_id] = device_name
        network.add_node(new_id, name=device_name)
        print(f"Device successfully added. (Name: {device_name}, ID: {new_id})")


    elif device_choice == "2":
        device_id = input("Enter Device ID to remove: ").strip()
        if device_id in devices:
            del devices[device_id]
            if network.has_node(device_id):
                network.remove_node(device_id)
            print("Device successfully removed.")
        else:
            print("Device not found.")


    elif device_choice == "3":
        first_device = input("Enter First Device ID: ").strip()
        second_device = input("Enter Second Device ID: ").strip()


        if first_device in devices and second_device in devices:
            network.add_edge(first_device, second_device)
            print("Connection successfully added.")
        else:
            print("Invalid device.")


    elif device_choice == "4":
        first_device = input("Enter First Device ID: ").strip()
        second_device = input("Enter Second Device ID: ").strip()


        if network.has_edge(first_device, second_device):
            network.remove_edge(first_device, second_device)
            print("Connection successfully removed.")
        else:
            print("Connection not found.")


    else:
        print("Invalid choice.")




def view_mesh_network():
    print("\n========== MESH NETWORK ==========")


    print("Registered Devices:")
    for node_id in network.nodes():
        print(f" - {devices.get(node_id, 'Unknown')} (ID: {node_id})")


    print("\nNetwork Connections:")
    if network.number_of_edges() > 0:
        for u, v in network.edges():
            print(f" - {devices.get(u, u)} ({u}) <---> {devices.get(v, v)} ({v})")
    else:
        print(" - No active connections.")


    plt.figure(figsize=(7, 5))
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
        width=2,
    )
    plt.title("ECO FARM - Offline Mesh Network", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.show()




def save_all_data():
    with open(FARM_DATA_FILE, "w") as f:
        json.dump(farm_data, f, indent=4)


    with open(MESSAGES_FILE, "w") as f:
        json.dump(messages, f, indent=4)


    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=4)


    network_payload = {
        "devices": devices,
        "connections": [list(edge) for edge in network.edges()],
    }
    with open(NETWORK_FILE, "w") as f:
        json.dump(network_payload, f, indent=4)




def main():
    load_all_data()


    if len(devices) == 0:
        default_names = ["Device A", "Device B", "Device C", "Device D"]
        created_ids = []


        for name in default_names:
            dev_id = str(uuid.uuid4())[:8]
            devices[dev_id] = name
            network.add_node(dev_id, name=name)
            created_ids.append(dev_id)


        network.add_edge(created_ids[0], created_ids[1])  # A - B
        network.add_edge(created_ids[1], created_ids[2])  # B - C
        network.add_edge(created_ids[2], created_ids[3])  # C - D
        network.add_edge(created_ids[0], created_ids[3])  # A - D


        save_all_data()


    print("==========================================")
    print("      ECO FARM OFFLINE CONTROL PANEL      ")
    print("==========================================")
    print(f"Connected Devices : {len(devices)} | Mesh Links: {network.number_of_edges()}")
    print(f"Saved Readings    : {len(farm_data)} | Active Alerts: {len(alerts)}")


    running = True


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


        menu_choice = input("Enter choice (1-9): ").strip()


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
            running = False
            print("Exiting ECO FARM...")
        else:
            print("Invalid choice. Please try again.")


        save_all_data()


    print("Thank you for using ECO FARM!")




if __name__ == "__main__":
    main()
