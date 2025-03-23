import tkinter as tk
from tkinter import ttk
import requests
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import datetime
import base64
import io

SERVER_URL = "http://127.0.0.1:5000"
# SERVER_URL = "http://vcm-43744.vm.duke.edu:5001"


def fetch_rooms(room_menu):
    """
    Fetch the list of room numbers from the server.

    This function retrieves a list of available room numbers from a
    server endpoint and updates the dropdown menu with the fetched
    room numbers. The server response is expected to contain a JSON
    object with a key 'rooms', which maps to a list of integers
    representing room numbers.

    Args:
        room_menu (ttk.Combobox): Dropdown menu to populate with rooms.

    Returns:
        None
    """
    try:
        response = requests.get(f"{SERVER_URL}/rooms")
        response.raise_for_status()
        rooms = response.json().get("rooms", [])
        room_menu["values"] = rooms
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch rooms: {e}")


def display_image(base64_string, image_label,
                  target_width=60, target_height=20):
    """
    Decodes a base64 image string, resizes it, and displays it in the
    specified label. Adjusts the label size to match the resized image
    dimensions.

    Args:
        base64_string (str): The base64-encoded image data.
        image_label (tk.Label): The label to display the image.
        target_width (int): The target width of the displayed image.
        target_height (int): The target height of the displayed image.

    Returns:
        None
    """
    try:
        if not base64_string:
            placeholder = Image.new("RGB",
                                    (target_width, target_height),
                                    "lightgray")
            photo = ImageTk.PhotoImage(placeholder)
            image_label.config(image="", text="No image available",
                               bg="lightgray")
            image_label.image = None
            return

        # Decode and display the image
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))

        original_width, original_height = image.size
        aspect_ratio = original_width / original_height

        if original_width > original_height:
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = target_height
            new_width = int(new_height * aspect_ratio)

        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        image_label.config(image=photo, text="", bg="white")
        image_label.image = photo

        # image_label.config(width=new_width, height=new_height)
    except Exception:
        # Reset the label and show error message if an exception occurs
        placeholder = Image.new("RGB",
                                (target_width, target_height), "lightgray")
        photo = ImageTk.PhotoImage(placeholder)
        image_label.config(image=photo, text="Error loading image", bg="red")
        image_label.image = photo


def fetch_latest_data(selected_room, formatted_timestamp_label,
                      data_text, latest_image_label):
    """
    Fetches the latest patient name, CPAP pressure, breathing rate,
    apnea count, and a timestamp for a room. Displays the data and the
    latest flow image in the corresponding GUI components.

    Args:
        selected_room (str): The selected room number.
        formatted_timestamp_label (tk.Label):
            Label to display the formatted timestamp.
        data_text (tk.Text): Text widget to display the patient data.
        latest_image_label (tk.Label): Label to display the latest flow image.

    Returns:
        None
    """
    try:
        response = requests.get(
            f"{SERVER_URL}/room/{selected_room}/patient_data")
        response.raise_for_status()
        data = response.json()

        response = requests.get(
            f"{SERVER_URL}/room/{selected_room}/patient_info")
        response.raise_for_status()
        patient_info = response.json()

        name = patient_info.get("name")
        mrn = patient_info.get("mrn")
        cpap_pressure = data.get("cpap_pressure")
        breathing_rate = data.get("breathing_rate")
        apnea_count = data.get("apnea_count")
        timestamp = data.get("timestamp")
        flow_image_base64 = data.get("flow_image_base64")

        # Clear previous data and display only available information
        data_text.delete("1.0", tk.END)

        if name:
            data_text.insert(tk.END, f"Name: {name}\n")
        else:
            data_text.insert(tk.END, "Name: Unavailable\n")

        if mrn:
            data_text.insert(tk.END, f"MRN: {mrn}\n")
        else:
            data_text.insert(tk.END, "MRN: Unavailable\n")

        if cpap_pressure is not None:
            data_text.insert(tk.END, f"CPAP Pressure: {cpap_pressure}\n")
        else:
            data_text.insert(tk.END, "CPAP Pressure: Unavailable\n")

        if breathing_rate is not None:
            data_text.insert(tk.END, f"Breathing Rate: {breathing_rate}\n")
        else:
            data_text.insert(tk.END, "Breathing Rate: Unavailable\n")

        if apnea_count is not None:
            data_text.insert(tk.END, "Apnea Count: ")
            apnea_count_color = "red" if apnea_count >= 2 else "black"
            data_text.insert(tk.END, f"{apnea_count}\n", ("apnea_count",))
            data_text.tag_configure("apnea_count",
                                    foreground=apnea_count_color)
        else:
            data_text.insert(tk.END, "Apnea Count: Unavailable\n")

        if timestamp is not None:
            formatted_time = datetime.fromisoformat(timestamp).strftime(
                "%Y-%m-%d %H:%M:%S")
            formatted_timestamp_label.config(text=formatted_time)
        else:
            formatted_timestamp_label.config(text="Timestamp unavailable")

        if flow_image_base64:
            display_image(flow_image_base64, latest_image_label)
        else:
            latest_image_label.config(image="", text="No image available")

    except requests.RequestException as e:
        data_text.delete("1.0", tk.END)
        formatted_timestamp_label.config(text="Timestamp unavailable")
        latest_image_label.config(image="", text="No image available")
        messagebox.showerror("Error", f"Failed to fetch latest data: {e}")


timestamp_mapping = {}


def fetch_timestamps(selected_room, timestamp_menu):
    """
    Fetches all available timestamps for a given room,
    formats them for display, and populates the dropdown menu
    while mapping formatted timestamps to their unformatted
    ones for API requests.

    Args:
        selected_room (str): The selected room number.
        timestamp_menu (ttk.Combobox):
            Dropdown menu to populate with timestamps.

    Returns:
        None
    """
    global timestamp_mapping
    try:
        response = requests.get(
            f"{SERVER_URL}/room/{selected_room}/timestamps")
        response.raise_for_status()
        timestamps = response.json().get("timestamps", [])
        if timestamps:
            timestamp_mapping = {
                datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S"): ts
                for ts in timestamps
            }
            timestamp_menu["values"] = list(timestamp_mapping.keys())
            latest_formatted = list(timestamp_mapping.keys())[-1]
            timestamp_menu.set(latest_formatted)
        else:
            # Clear the menu and mapping if no timestamps exist
            timestamp_mapping = {}
            timestamp_menu["values"] = ["No timestamps available"]
            timestamp_menu.set("No timestamps available")
    except requests.RequestException as e:
        timestamp_mapping = {}
        timestamp_menu["values"] = ["No timestamps available"]
        timestamp_menu.set("No timestamps available")
        messagebox.showerror("Error", f"Failed to fetch timestamps: {e}")


def fetch_selected_image(selected_room,
                         selected_timestamp, selected_image_label):
    """
    Fetches and displays the flow image for
    a specific room and timestamp using the unformatted
    timestamp stored in the mapping. If no image is available,
    it updates the label accordingly.

    Args:
        selected_room (str): The selected room number.
        selected_timestamp (str): The selected (formatted) timestamp.
        selected_image_label (tk.Label): Label widget to display the image.

    Returns:
        None
    """
    global timestamp_mapping
    try:
        if not selected_timestamp:
            messagebox.showerror("Error", "No timestamp selected.")
            return

        unformatted_timestamp = timestamp_mapping.get(selected_timestamp)
        if not unformatted_timestamp:
            messagebox.showerror("Error", "Selected timestamp is invalid.")
            return

        response = requests.get(
            f"{SERVER_URL}/room/{selected_room}/image/{unformatted_timestamp}")
        response.raise_for_status()
        data = response.json()
        flow_image_base64 = data.get("flow_image_base64")

        if flow_image_base64:
            display_image(flow_image_base64, selected_image_label)
        else:
            selected_image_label.config(
                image="", text="No image for selected timestamp",
                bg="lightgray")
    except requests.HTTPError as e:
        messagebox.showerror("Error", f"Failed to fetch image: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")


def download_image(base64_string, filename):
    """
    Decodes a base64-encoded image string and saves it
    to a file on disk with the specified filename.
    This function allows the user to download and store images locally.
    Args:
        base64_string (str):
            The base64-encoded string representing the image data.
        filename (str):
            The filename for the saved image, including its extension.

    Returns:
        None
    """
    try:
        image_data = base64.b64decode(base64_string)
        with open(filename, "wb") as image_file:
            image_file.write(image_data)
        messagebox.showinfo("Success", f"Image saved as {filename}.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download image: {e}")


def download_latest_image(selected_room_var):
    """
    Fetches and downloads the latest flow image
    associated with the selected room from the server.

    Args:
        selected_room_var (tk.StringVar):
            The variable holding the selected room number.

    Returns:
        None
    """
    try:
        selected_room = selected_room_var.get()
        if not selected_room:
            messagebox.showerror("Error", "No room selected.")
            return
        response = requests.get(
            f"{SERVER_URL}/room/{selected_room}/patient_data")
        response.raise_for_status()
        data = response.json()
        flow_image_base64 = data.get("flow_image_base64")
        if flow_image_base64:
            filename = f"latest_flow_image_{selected_room}.png"
            download_image(flow_image_base64, filename)
        else:
            messagebox.showerror(
                "Error", "No latest image available to download.")
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch latest image: {e}")


def download_selected_image(selected_room_var, selected_timestamp_var):
    """
    Fetches and downloads the flow image corresponding to the selected
    timestamp for the chosen room. The image is saved locally using a
    filename constructed from the room number and the selected timestamp.
    If the timestamp is invalid, no image exists for the timestamp,
    or the server request fails, an error message is displayed to the user.

    Args:
        selected_room_var (tk.StringVar):
            The variable holding the selected room number.
        selected_timestamp_var (tk.StringVar):
            The variable holding the selected timestamp.

    Returns:
        None
    """
    try:
        selected_room = selected_room_var.get()
        selected_timestamp = selected_timestamp_var.get()
        if not selected_room:
            messagebox.showerror("Error", "No room selected.")
            return
        if not selected_timestamp:
            messagebox.showerror("Error", "No timestamp selected.")
            return

        unformatted_timestamp = timestamp_mapping.get(selected_timestamp)
        if not unformatted_timestamp:
            messagebox.showerror("Error", "Invalid timestamp selected.")
            return

        response = requests.get(
            f"{SERVER_URL}/room/{selected_room}/image/{unformatted_timestamp}"
        )
        response.raise_for_status()
        data = response.json()
        flow_image_base64 = data.get("flow_image_base64")
        if flow_image_base64:
            filename = (
                f"flow_image_{selected_room}_"
                f"{selected_timestamp.replace(':', '_').replace(' ', '_')}.jpg"
            )
            download_image(flow_image_base64, filename)
        else:
            messagebox.showerror(
                "Error", "No image available for the selected timestamp.")
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch selected image: {e}")


def update_cpap_pressure(selected_room, cpap_entry):
    """
    Updates the CPAP pressure for a specific room by validating the input
    and sending it to the server. Displays appropriate messages based on
    success or failure.

    Args:
        selected_room (str): Selected room number.
        cpap_entry (ttk.Entry): Entry widget containing the new CPAP pressure.

    Returns:
        None
    """
    pressure = cpap_entry.get()
    print(f"Sending CPAP pressure: {pressure} for room: {selected_room}")
    if not (4 <= int(pressure) <= 25):
        messagebox.showerror(
            "Error", "CPAP pressure must be an integer between 4 and 25.")
        return
    print("pressure is valid")
    print(f"{SERVER_URL}/room/{selected_room}/update_cpap")
    try:
        response = requests.post(
            f"{SERVER_URL}/room/{selected_room}/update_cpap",
            json={"cpap_pressure": int(pressure)}
        )
        response.raise_for_status()
        messagebox.showinfo("Success", "CPAP pressure updated successfully.")
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Failed to update CPAP pressure: {e}")


def periodic_update(selected_room_var, room_menu, timestamp_menu,
                    formatted_timestamp_label, data_text,
                    latest_image_label, status_label, root):
    """
    Fetches the latest patient data for the selected room and updates the
    relevant GUI components periodically. This ensures the interface remains
    updated with the server data.

    Args:
        selected_room_var (tk.StringVar):
            The variable holding the selected room number.
        room_menu (ttk.Combobox): Dropdown menu for room selection.
        timestamp_menu (ttk.Combobox): Dropdown menu for timestamp selection.
        formatted_timestamp_label (tk.Label):
            Label to display the formatted timestamp.
        data_text (tk.Text): Text widget to display the patient data.
        latest_image_label (tk.Label): Label to display the latest flow image.
        status_label (tk.Label):
            Label to display the status of the update process.
        root (tk.Tk): The main Tkinter window.

    Returns:
        None
    """
    fetch_rooms(room_menu)

    if selected_room_var.get():
        try:
            fetch_timestamps(selected_room_var.get(), timestamp_menu)

            fetch_latest_data(selected_room_var.get(),
                              formatted_timestamp_label,
                              data_text, latest_image_label)

            status_label.config(text="Update complete", fg="green")
        except Exception as e:
            status_label.config(text=f"Update failed: {e}", fg="red")
    else:
        status_label.config(text="No Updates", fg="orange")

    # Schedule the next periodic update (every 30 seconds)
    root.after(30000,
               lambda: periodic_update(selected_room_var, room_menu,
                                       timestamp_menu,
                                       formatted_timestamp_label,
                                       data_text, latest_image_label,
                                       status_label, root))


def main_window():
    root = tk.Tk()
    root.title("Monitoring Station")
    # root.resizable(False, False)

    selected_room = tk.StringVar()
    selected_timestamp = tk.StringVar()

    # Room Selection
    room_frame = ttk.LabelFrame(root, text="Room Number")
    room_frame.pack(fill="x", padx=10, pady=5)
    ttk.Label(room_frame, text="Select Room:").pack(
        side="left", padx=5, pady=5)
    room_menu = ttk.Combobox(
        room_frame, textvariable=selected_room, state="readonly")
    room_menu.pack(side="left", padx=5, pady=5)

    # Latest Patient Data
    data_frame = ttk.LabelFrame(root, text="Latest Patient Data")
    data_frame.pack(fill="x", padx=10, pady=5)
    data_text = tk.Text(data_frame, height=5, wrap="word")
    data_text.pack(fill="x", padx=5, pady=5)

    # Flow Images
    image_frame = ttk.LabelFrame(root, text="Flow Images")
    image_frame.pack(fill="both", expand=True, padx=10, pady=5)

    latest_timestamp_label = tk.Label(image_frame, text="Latest Timestamp:")
    latest_timestamp_label.grid(row=0, column=0, padx=5, pady=5, sticky="n")
    formatted_timestamp_label = tk.Label(image_frame, text="")
    formatted_timestamp_label.grid(row=1, column=0, padx=5, pady=5, sticky="n")
    formatted_timestamp_label.config(text="No timestamp available")

    timestamp_label = tk.Label(image_frame, text="Select Timestamp:")
    timestamp_label.grid(row=0, column=1, padx=5, pady=5, sticky="n")
    timestamp_menu = ttk.Combobox(
        image_frame, textvariable=selected_timestamp, state="readonly")
    timestamp_menu.grid(row=1, column=1, padx=5, pady=5, sticky="n")
    timestamp_menu["values"] = ["No timestamps available"]
    timestamp_menu.set("No timestamps available")

    latest_image_label = tk.Label(image_frame, text="Latest Flow Image",
                                  width=60, height=20, bg="lightgray")
    latest_image_label.grid(row=2, column=0, padx=10, pady=10, sticky="n")
    latest_image_label.config(image="",
                              text="No flow image available", bg="lightgray")
    selected_image_label = tk.Label(image_frame, text="Selected Flow Image",
                                    width=60, height=20, bg="lightgray")
    selected_image_label.grid(row=2, column=1, padx=10, pady=10, sticky="n")
    selected_image_label.config(image="",
                                text="No flow image selected", bg="lightgray")

    latest_download_button = tk.Button(image_frame,
                                       text="Download Latest Image")
    latest_download_button.grid(row=3, column=0, padx=10, pady=5, sticky="n")
    latest_download_button.config(
        command=lambda: download_latest_image(selected_room))

    selected_download_button = tk.Button(image_frame,
                                         text="Download Selected Image")
    selected_download_button.grid(row=3, column=1, padx=10, pady=5, sticky="n")
    selected_download_button.config(
        command=lambda: download_selected_image(
            selected_room, selected_timestamp))

    # Update CPAP Pressure
    update_frame = ttk.LabelFrame(root, text="Update CPAP Pressure")
    update_frame.pack(fill="x", padx=10, pady=5)

    ttk.Label(update_frame, text="New CPAP Pressure:").pack(
        side="left", padx=5, pady=5)
    cpap_entry = ttk.Entry(update_frame)
    cpap_entry.pack(side="left", padx=5, pady=5)

    ttk.Button(update_frame, text="Update",
               command=lambda: update_cpap_pressure(
                   selected_room.get(), cpap_entry)).pack(
                       side="left", padx=5, pady=5)

    # Status Label
    status_label = tk.Label(root, text="", fg="blue")
    status_label.pack(pady=5)

    # Event Bindings
    room_menu.bind("<<ComboboxSelected>>", lambda e: [
        fetch_timestamps(selected_room.get(), timestamp_menu),
        fetch_latest_data(selected_room.get(), formatted_timestamp_label,
                          data_text, latest_image_label),
        selected_image_label.config(image="",
                                    text="No flow image selected",
                                    bg="lightgray"),
        timestamp_menu.config(text="Select Timestamp")
    ])
    timestamp_menu.bind("<<ComboboxSelected>>",
                        lambda e: fetch_selected_image(selected_room.get(),
                                                       timestamp_menu.get(),
                                                       selected_image_label))

    fetch_rooms(room_menu)

    # Start periodic updates
    periodic_update(selected_room, room_menu, timestamp_menu,
                    formatted_timestamp_label, data_text,
                    latest_image_label, status_label, root)

    root.mainloop()


if __name__ == "__main__":
    main_window()
