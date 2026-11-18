from collections import deque
from datetime import datetime
import json
import os
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import uuid

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

# Main storage variables 
devices = {}
farm_data = []
messages = []
alerts = []
network = nx.Graph()

# Offline JSON save files 
FARM_DATA_FILE = "farm_data.json"
MESSAGES_FILE = "messages.json"
ALERTS_FILE = "alerts.json"
NETWORK_FILE = "network_data.json"


# Helper: Finds the shortest path between two offline devices (BFS)
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


# Helper: Loads saved data from JSON files when the app opens
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

            network.clear()
            for dev_id, dev_name in devices.items():
                network.add_node(dev_id, name=dev_name)
            for u, v in connections:
                if u in devices and v in devices:
                    network.add_edge(u, v)


# Helper: Saves all data to the 4 JSON files
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


# ================= TKINTER GUI APPLICATION =================
class EcoFarmGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("ECO FARM OFFLINE CONTROL PANEL")
        self.root.geometry("1020x680")
        self.root.configure(bg="#bf009f")

        # Initialize data gaya ng nasa main() mo
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

        # Top Header Bar
        header = tk.Frame(root, bg="#1b4332", pady=12)
        header.pack(fill="x")
        tk.Label(
            header,
            text="ECO FARM OFFLINE CONTROL PANEL",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#1b4332",
        ).pack()

        self.status_lbl = tk.Label(
            header,
            text="",
            font=("Arial", 10),
            fg="#b7e4c7",
            bg="#1b4332",
        )
        self.status_lbl.pack()
        self.update_header_stats()

        # Main Body Frame
        body = tk.Frame(root, bg="#edf2f4")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        # Left Sidebar Menu (9 Options gaya ng menu mo)
        sidebar = tk.Frame(body, bg="#f3d8ee", width=210, bd=1, relief="solid")
        sidebar.pack(side="left", fill="y", padx=(0, 10))

        menu_items = [
            ("1. Monitor Farm", self.ui_monitor_farm),
            ("2. Add Farm Data", self.ui_add_farm_data),
            ("3. Send Offline Message", self.ui_send_offline_message),
            ("4. View Alerts", self.ui_view_alerts),
            ("5. View Data History", self.ui_view_data_history),
            ("6. Manage Devices", self.ui_manage_devices),
            ("7. View Mesh Network", self.ui_view_mesh_network),
            ("8. View Messages", self.ui_view_messages),
            ("9. Exit", self.ui_exit),
        ]

        for label, command in menu_items:
            btn = tk.Button(
                sidebar,
                text=label,
                command=command,
                font=("Arial", 10, "bold"),
                bg="#2d6a4f" if "Exit" not in label else "#b00020",
                fg="white",
                width=22,
                pady=8,
                relief="flat",
                cursor="hand2",
            )
            btn.pack(pady=5, padx=10)

        # Right Content Area
        self.content = tk.Frame(body, bg="white", bd=1, relief="solid")
        self.content.pack(side="right", fill="both", expand=True)

        self.ui_monitor_farm()

    def update_header_stats(self):
        self.status_lbl.config(
            text=(
                f"Connected Devices: {len(devices)} | Mesh Links:"
                f" {network.number_of_edges()} | Saved Readings:"
                f" {len(farm_data)} | Active Alerts: {len(alerts)}"
            )
        )

    def clear_content(self):
        plt.close("all")  # Para hindi maipon sa memory ang lumang Matplotlib figures
        for widget in self.content.winfo_children():
            widget.destroy()

    # 1. MONITOR FARM
    def ui_monitor_farm(self):
        self.clear_content()
        tk.Label(
            self.content,
            text="========== FARM MONITORING ==========",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#1b4332",
        ).pack(pady=10)

        if len(farm_data) > 0:
            latest = farm_data[-1]
            latest_txt = (
                f"LATEST READINGS  |  Device: {latest['device_id']}  |  "
                f"Temp: {latest['temperature']} °C  |  "
                f"Moisture: {latest['soil_moisture']}%  |  "
                f"Water: {latest['water_level']}%  |  "
                f"Time: {latest['timestamp']}"
            )
            tk.Label(
                self.content,
                text=latest_txt,
                font=("Arial", 9, "bold"),
                bg="#e9f5db",
                pady=8,
                padx=10,
            ).pack(fill="x", padx=15)

            df = pd.DataFrame(farm_data)

            fig, axes = plt.subplots(3, 1, figsize=(7, 5), sharex=True)
            fig.suptitle(
                "ECO FARM - Sensor Condition Trends",
                fontsize=11,
                fontweight="bold",
            )

            axes[0].plot(
                df["timestamp"],
                df["temperature"],
                marker="o",
                color="tab:red",
                label="Temperature (°C)",
            )
            axes[0].axhline(
                35, color="red", linestyle="--", linewidth=1, label="Limit (>35°C)"
            )
            axes[0].set_ylabel("Temp (°C)", fontsize=8)
            axes[0].legend(loc="upper right", fontsize=7)
            axes[0].grid(True, linestyle=":", alpha=0.6)

            axes[1].plot(
                df["timestamp"],
                df["soil_moisture"],
                marker="s",
                color="tab:green",
                label="Soil Moisture (%)",
            )
            axes[1].axhline(
                30,
                color="orange",
                linestyle="--",
                linewidth=1,
                label="Limit (<30%)",
            )
            axes[1].set_ylabel("Moisture (%)", fontsize=8)
            axes[1].legend(loc="upper right", fontsize=7)
            axes[1].grid(True, linestyle=":", alpha=0.6)

            axes[2].plot(
                df["timestamp"],
                df["water_level"],
                marker="^",
                color="tab:blue",
                label="Water Level (%)",
            )
            axes[2].axhline(
                30,
                color="purple",
                linestyle="--",
                linewidth=1,
                label="Limit (<30%)",
            )
            axes[2].set_ylabel("Water (%)", fontsize=8)
            axes[2].legend(loc="upper right", fontsize=7)
            axes[2].grid(True, linestyle=":", alpha=0.6)

            plt.xticks(rotation=25, ha="right", fontsize=7)
            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.content)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)
        else:
            tk.Label(
                self.content,
                text="No farm readings available.\nPlease add farm data first.",
                font=("Arial", 12),
                bg="white",
                fg="gray",
            ).pack(expand=True)

    # 2. ADD FARM DATA
    def ui_add_farm_data(self):
        self.clear_content()
        tk.Label(
            self.content,
            text="========== ADD FARM DATA ==========",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#891061",
        ).pack(pady=15)

        form = tk.Frame(self.content, bg="white")
        form.pack(pady=10)

        device_options = [f"{dev_id} - {name}" for dev_id, name in devices.items()]

        tk.Label(form, text="Select Device:", bg="white", font=("Romans", 10)).grid(
            row=0, column=0, sticky="w", pady=8
        )
        dev_cb = ttk.Combobox(
            form, values=device_options, state="readonly", width=30
        )
        dev_cb.grid(row=0, column=1, pady=8, padx=10)
        if device_options:
            dev_cb.current(0)

        tk.Label(
            form, text="Temperature (°C):", bg="white", font=("Arial", 10)
        ).grid(row=1, column=0, sticky="w", pady=8)
        temp_entry = tk.Entry(form, width=33)
        temp_entry.grid(row=1, column=1, pady=8, padx=10)

        tk.Label(
            form, text="Soil Moisture (%):", bg="white", font=("Arial", 10)
        ).grid(row=2, column=0, sticky="w", pady=8)
        soil_entry = tk.Entry(form, width=33)
        soil_entry.grid(row=2, column=1, pady=8, padx=10)

        tk.Label(
            form, text="Water Level (%):", bg="white", font=("Arial", 10)
        ).grid(row=3, column=0, sticky="w", pady=8)
        water_entry = tk.Entry(form, width=33)
        water_entry.grid(row=3, column=1, pady=8, padx=10)

        def submit():
            if not dev_cb.get():
                messagebox.showerror("Error", "Device not found.")
                return
            selected_device = dev_cb.get().split(" - ")[0]

            try:
                temperature = float(temp_entry.get())
                soil_moisture = float(soil_entry.get())
                water_level = float(water_entry.get())

                if not (
                    0 <= soil_moisture <= 100
                    and 0 <= water_level <= 100
                    and -50 <= temperature <= 100
                ):
                    messagebox.showerror("Error", "Invalid sensor readings.")
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

                generated_alerts = []
                if temperature > 35:
                    temp_alert = {
                        "type": "HIGH TEMPERATURE",
                        "device_id": selected_device,
                        "message": (
                            f"High temperature ({temperature}°C > 35°C) on"
                            f" {devices[selected_device]}"
                        ),
                        "timestamp": timestamp,
                    }
                    alerts.append(temp_alert)
                    generated_alerts.append(temp_alert["message"])

                if soil_moisture < 30:
                    moisture_alert = {
                        "type": "LOW SOIL MOISTURE",
                        "device_id": selected_device,
                        "message": (
                            f"Low soil moisture ({soil_moisture}% < 30%) on"
                            f" {devices[selected_device]}"
                        ),
                        "timestamp": timestamp,
                    }
                    alerts.append(moisture_alert)
                    generated_alerts.append(moisture_alert["message"])

                if water_level < 30:
                    water_alert = {
                        "type": "LOW WATER LEVEL",
                        "device_id": selected_device,
                        "message": (
                            f"Low water level ({water_level}% < 30%) on"
                            f" {devices[selected_device]}"
                        ),
                        "timestamp": timestamp,
                    }
                    alerts.append(water_alert)
                    generated_alerts.append(water_alert["message"])

                connected_peers = list(network.neighbors(selected_device))
                peer_names = [f"{devices[p]} ({p})" for p in connected_peers]

                save_all_data()
                self.update_header_stats()

                msg = "Farm data saved and shared with connected devices."
                if peer_names:
                    msg += f"\n\nShared with: {', '.join(peer_names)}"
                if generated_alerts:
                    msg += "\n\nALERTS GENERATED:\n- " + "\n- ".join(
                        generated_alerts
                    )

                messagebox.showinfo("Success", msg)
                self.ui_monitor_farm()

            except ValueError:
                messagebox.showerror(
                    "Error", "Invalid sensor readings. Please enter numbers only."
                )

        tk.Button(
            self.content,
            text="Save & Share Farm Data",
            command=submit,
            bg="#a60b51",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=8,
        ).pack(pady=15)

    # 3. SEND OFFLINE MESSAGE
    def ui_send_offline_message(self):
        self.clear_content()
        tk.Label(
            self.content,
            text="========== SEND OFFLINE MESSAGE ==========",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#1b4332",
        ).pack(pady=15)

        form = tk.Frame(self.content, bg="white")
        form.pack(pady=10)

        device_options = [f"{dev_id} - {name}" for dev_id, name in devices.items()]

        tk.Label(form, text="Sender Device:", bg="white", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", pady=8
        )
        sender_cb = ttk.Combobox(
            form, values=device_options, state="readonly", width=30
        )
        sender_cb.grid(row=0, column=1, pady=8, padx=10)

        tk.Label(
            form, text="Receiver Device:", bg="white", font=("Arial", 10)
        ).grid(row=1, column=0, sticky="w", pady=8)
        receiver_cb = ttk.Combobox(
            form, values=device_options, state="readonly", width=30
        )
        receiver_cb.grid(row=1, column=1, pady=8, padx=10)

        tk.Label(form, text="Message:", bg="white", font=("Arial", 10)).grid(
            row=2, column=0, sticky="w", pady=8
        )
        msg_entry = tk.Entry(form, width=33)
        msg_entry.grid(row=2, column=1, pady=8, padx=10)

        def send():
            if not sender_cb.get() or not receiver_cb.get():
                messagebox.showerror("Error", "Device not found.")
                return

            sender = sender_cb.get().split(" - ")[0]
            receiver = receiver_cb.get().split(" - ")[0]
            message = msg_entry.get().strip()

            if not message:
                messagebox.showwarning("Warning", "Please enter a message.")
                return

            path = bfs_communication_path(network, sender, receiver)
            if path is not None:
                route_display = " -> ".join(
                    [f"{devices[node]} ({node})" for node in path]
                )
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                messages.append({
                    "sender": sender,
                    "receiver": receiver,
                    "message": message,
                    "path": path,
                    "timestamp": timestamp,
                })
                save_all_data()
                messagebox.showinfo(
                    "Message Sent",
                    "Message sent successfully!\n\nCommunication Path"
                    f" (BFS):\n{route_display}",
                )
                msg_entry.delete(0, tk.END)
            else:
                messagebox.showerror(
                    "Error", "No communication path available."
                )

        tk.Button(
            self.content,
            text="Send Offline Message",
            command=send,
            bg="#eeacdf",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=8,
        ).pack(pady=15)

    # 4. VIEW ALERTS
    def ui_view_alerts(self):
        self.clear_content()
        tk.Label(
            self.content,
            text="========== FARM ALERTS ==========",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#ea80bb",
        ).pack(pady=15)

        box = scrolledtext.ScrolledText(
            self.content, width=80, height=24, font=("Consolas", 10)
        )
        box.pack(padx=20, pady=10, fill="both", expand=True)

        if len(alerts) > 0:
            for idx, alert in enumerate(alerts, start=1):
                box.insert(
                    tk.END,
                    f"{idx}. [{alert['timestamp']}] {alert['type']} |"
                    f" {alert['message']}\n\n",
                )
        else:
            box.insert(tk.END, "No alerts available.")
        box.config(state="disabled")

    # 5. VIEW DATA HISTORY
    def ui_view_data_history(self):
        self.clear_content()
        tk.Label(
            self.content,
            text="========== FARM DATA HISTORY ==========",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#dc2b8f",
        ).pack(pady=15)

        box = scrolledtext.ScrolledText(
            self.content, width=85, height=25, font=("Consolas", 9)
        )
        box.pack(padx=20, pady=10, fill="both", expand=True)

        if len(farm_data) > 0:
            df = pd.DataFrame(farm_data)
            box.insert(tk.END, "--- ALL PREVIOUS FARM READINGS ---\n")
            box.insert(tk.END, df.to_string(index=False))
            box.insert(tk.END, "\n\n--- DATA SUMMARY (PANDAS) ---\n")
            box.insert(
                tk.END,
                df[["temperature", "soil_moisture", "water_level"]]
                .describe()
                .to_string(),
            )
        else:
            box.insert(tk.END, "No farm history available.")
        box.config(state="disabled")

    # 6. MANAGE DEVICES
    def ui_manage_devices(self):
        self.clear_content()
        tk.Label(
            self.content,
            text="===== MANAGE DEVICES =====",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#1b4332",
        ).pack(pady=10)

        # List of current devices
        info_box = scrolledtext.ScrolledText(
            self.content, height=6, font=("Consolas", 9), bg="#f8f9fa"
        )
        info_box.pack(fill="x", padx=20, pady=5)
        info_box.insert(tk.END, "REGISTERED DEVICES:\n")
        for did, dname in devices.items():
            info_box.insert(tk.END, f" - {dname} (ID: {did})\n")
        info_box.config(state="disabled")

        grid = tk.Frame(self.content, bg="white")
        grid.pack(pady=10, padx=20, fill="both", expand=True)

        # 1. Add Device
        f1 = tk.LabelFrame(
            grid, text="1. Add Device", bg="white", padx=10, pady=10
        )
        f1.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")
        tk.Label(f1, text="Device Name:", bg="white").pack(anchor="w")
        add_name = tk.Entry(f1, width=26)
        add_name.pack(pady=5)

        def add_dev():
            device_name = add_name.get().strip()
            if not device_name:
                return
            new_id = str(uuid.uuid4())[:8]
            devices[new_id] = device_name
            network.add_node(new_id, name=device_name)
            save_all_data()
            self.update_header_stats()
            messagebox.showinfo(
                "Success",
                f"Device successfully added.\n(Name: {device_name}, ID: {new_id})",
            )
            self.ui_manage_devices()

        tk.Button(
            f1, text="Add Device", command=add_dev, bg="#2d6a4f", fg="white"
        ).pack()

        # 2. Remove Device
        f2 = tk.LabelFrame(
            grid, text="2. Remove Device", bg="white", padx=10, pady=10
        )
        f2.grid(row=0, column=1, padx=10, pady=8, sticky="nsew")
        tk.Label(f2, text="Device ID:", bg="white").pack(anchor="w")
        rem_id = tk.Entry(f2, width=26)
        rem_id.pack(pady=5)

        def rem_dev():
            device_id = rem_id.get().strip()
            if device_id in devices:
                del devices[device_id]
                if network.has_node(device_id):
                    network.remove_node(device_id)
                save_all_data()
                self.update_header_stats()
                messagebox.showinfo("Success", "Device successfully removed.")
                self.ui_manage_devices()
            else:
                messagebox.showerror("Error", "Device not found.")

        tk.Button(
            f2, text="Remove Device", command=rem_dev, bg="#b00020", fg="white"
        ).pack()

        # 3. Add Connection
        f3 = tk.LabelFrame(
            grid, text="3. Add Connection", bg="white", padx=10, pady=10
        )
        f3.grid(row=1, column=0, padx=10, pady=8, sticky="nsew")
        tk.Label(f3, text="First Device ID:", bg="white").pack(anchor="w")
        c1_add = tk.Entry(f3, width=26)
        c1_add.pack(pady=2)
        tk.Label(f3, text="Second Device ID:", bg="white").pack(anchor="w")
        c2_add = tk.Entry(f3, width=26)
        c2_add.pack(pady=2)

        def add_conn():
            u, v = c1_add.get().strip(), c2_add.get().strip()
            if u in devices and v in devices and u != v:
                network.add_edge(u, v)
                save_all_data()
                self.update_header_stats()
                messagebox.showinfo(
                    "Success", "Connection successfully added."
                )
                self.ui_manage_devices()
            else:
                messagebox.showerror("Error", "Invalid device.")

        tk.Button(
            f3, text="Add Connection", command=add_conn, bg="#2d6a4f", fg="white"
        ).pack(pady=5)

        # 4. Remove Connection
        f4 = tk.LabelFrame(
            grid, text="4. Remove Connection", bg="white", padx=10, pady=10
        )
        f4.grid(row=1, column=1, padx=10, pady=8, sticky="nsew")
        tk.Label(f4, text="First Device ID:", bg="white").pack(anchor="w")
        c1_rem = tk.Entry(f4, width=26)
        c1_rem.pack(pady=2)
        tk.Label(f4, text="Second Device ID:", bg="white").pack(anchor="w")
        c2_rem = tk.Entry(f4, width=26)
        c2_rem.pack(pady=2)

        def rem_conn():
            u, v = c1_rem.get().strip(), c2_rem.get().strip()
            if network.has_edge(u, v):
                network.remove_edge(u, v)
                save_all_data()
                self.update_header_stats()
                messagebox.showinfo(
                    "Success", "Connection successfully removed."
                )
                self.ui_manage_devices()
            else:
                messagebox.showerror("Error", "Connection not found.")

        tk.Button(
            f4,
            text="Remove Connection",
            command=rem_conn,
            bg="#dc3d9a",
            fg="white",
        ).pack(pady=5)

    # 7. VIEW MESH NETWORK
    def ui_view_mesh_network(self):
        self.clear_content()
        tk.Label(
            self.content,
            text="========== MESH NETWORK ==========",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#9a2053",
        ).pack(pady=10)

        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        pos = nx.spring_layout(network, seed=42)
        labels = {
            node_id: f"{devices.get(node_id, '')}\n({node_id})"
            for node_id in network.nodes()
        }

        nx.draw(
            network,
            pos,
            ax=ax,
            with_labels=True,
            labels=labels,
            node_color="#c674b8",
            node_size=2400,
            font_size=8,
            font_weight="bold",
            edge_color="#e83485",
            width=2,
        )
        ax.set_title(
            "ECO FARM - Offline Mesh Network", fontsize=11, fontweight="bold"
        )
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.content)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=5)

    # 8. VIEW MESSAGES
    def ui_view_messages(self):
        self.clear_content()
        tk.Label(
            self.content,
            text="========== OFFLINE MESSAGES ==========",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#d223a7",
        ).pack(pady=15)

        box = scrolledtext.ScrolledText(
            self.content, width=80, height=24, font=("Consolas", 10)
        )
        box.pack(padx=20, pady=10, fill="both", expand=True)

        if len(messages) > 0:
            for idx, msg in enumerate(messages, start=1):
                sender_name = devices.get(msg["sender"], msg["sender"])
                receiver_name = devices.get(msg["receiver"], msg["receiver"])
                box.insert(
                    tk.END,
                    f"{idx}. [{msg['timestamp']}] {sender_name} ->"
                    f" {receiver_name}: {msg['message']}\n\n",
                )
        else:
            box.insert(tk.END, "No offline messages sent yet.")
        box.config(state="disabled")

    # 9. EXIT
    def ui_exit(self):
        save_all_data()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = EcoFarmGUI(root)
    root.mainloop()