import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from cpap_analysis import flow_analysis, calculate_breath_rate_bpm, count_apnea
from cpap_analysis import plot_t_vs_flow
from PIL import Image, ImageTk
import requests
from validate import validate_cpap_data
from image_toolbox import read_file_as_b64

SERVER = "http://127.0.0.1:5000"
# SERVER = "http://vcm-43744.vm.duke.edu:5001"


def send_to_server(patient_data):
    """
    Send patient data to the server via a RESTful API.

    This function use RESTful API to send the current patient related
    data to server. The patient data includes mrn, room, name(optional),
    and data(optional).

    Args:
        patient_data (dict): The patient data to be uploaded.

    Raises:
        requests.exceptions.RequestException: If there is an issue with
        the server request.
    """
    r = requests.post(SERVER + "/upload_patient", json=patient_data)
    if r.status_code == 200:
        messagebox.showinfo("Success",
                            "Patient data uploaded successfully!")
    else:
        messagebox.showerror(
            "Upload Error", f"Server responded with: {r.text}"
                             )


def generate_json_file(mrn_value, room_value, name_value, cpap_value,
                       BR, apnea_count):
    """
    Generate a JSON object containing patient data for upload.

    This function validates and combines patient information, CPAP pressure,
    and calculated data into a JSON object suitable for uploading to a server.
    It ensures that CPAP pressure and calculated data (breathing rate and
    apnea count) are provided together or neither is included. If only one is
    provided, it raises an error.

    Args:
        mrn_value (str): The Medical Record Number (MRN) of the patient.
        room_value (str): The room number associated with the patient.
        name_value (str): The name of the patient (optional).
        cpap_value (str): The CPAP pressure value (optional).
        BR (str): The breathing rate calculated from the CPAP data.
        apnea_count (str): The apnea count calculated from the CPAP data.

    Returns:
        dict: A dictionary containing the patient data, including:
            - "mrn": Patient's MRN (int).
            - "room": Patient's room number (int).
            - "name" (optional): Patient's name (str).
            - "cpap_pressure" (optional): CPAP pressure (int).
            - "data" (optional): A list containing a dictionary with:
                - "cpap_pressure": CPAP pressure (int).
                - "breathing_rate": Breathing rate (float).
                - "apnea_count": Apnea count (int).
                - "flow_image_base64": Base64 encoded str of the flow image.

    Raises:
        ValueError: If required fields (MRN or room) are missing.
        ValueError: If MRN or room is not an integer.
        ValueError: If only one of CPAP pressure or calculated data is
                    provided.
        ValueError: If the CPAP pressure is invalid or fails validation.
    """
    # Validate MRN and Room Number
    if not mrn_value or not room_value:
        raise ValueError("MRN and Room Number are required.")

    try:
        mrn_value = int(mrn_value)
        room_value = int(room_value)
    except ValueError:
        raise ValueError("MRN and Room Number must be integers.")

    out_json = {
        "mrn": mrn_value,
        "room": room_value,
    }
    if name_value:
        out_json["name"] = name_value

    print(BR, apnea_count)

    # Ensure CPAP pressure and calculated data exist together
    check_cpap = bool(cpap_value)
    check_data = (BR != "No available data"
                  and apnea_count != "No available data")
    print("cpap check:", check_cpap)
    print("cal_check:", check_data)

    if not check_cpap and not check_data:
        return out_json

    if check_cpap and not check_data:
        raise ValueError(
            "Cannot upload CPAP pressure without CPAP calculated data.")
    if not check_cpap and check_data:
        raise ValueError(
            "Cannot upload CPAP calculated data without CPAP pressure.")
    try:
        cpap_pressure = int(cpap_value)
        cpap_check = validate_cpap_data(cpap_pressure)
        if cpap_check is not True:
            raise ValueError(cpap_check)
        out_json["data"] = [{
            "cpap_pressure": cpap_pressure,
            "breathing_rate": float(BR),
            "apnea_count": int(apnea_count),
            "flow_image_base64": read_file_as_b64("flow_plot.jpg")
            }]
    except Exception as e:
        raise ValueError(f"Invalid CPAP pressure: {str(e)}")

    return out_json


def fetch_latest_cpap(room):
    """
    Fetch and update the CPAP pressure for a specific room.

    This function sends a GET request to the server to retrieve the latest
    CPAP pressure data for the specified room. If successful, the CPAP
    pressure value is returned as a string. If the room number is invalid or
    the request fails, an error message is displayed, and an empty string is
    returned.

    Args:
        room (str): The room number entered by the user.

    Returns:
        str: The latest CPAP pressure value as a string, or an empty string
             if the data could not be fetched.
    """
    upd_cpap_pressure = ""
    try:
        room = int(room)
        r = requests.get(f"{SERVER}/room/{room}/cpap_pressure")
        r.raise_for_status()
        data = r.json()

        # Update CPAP pressure in GUI based on the server's response
        if "cpap_pressure" in data and data["cpap_pressure"] is not None:
            upd_cpap_pressure = str(data["cpap_pressure"])

    except ValueError:
        messagebox.showerror("Validation Error",
                             "Room number must be an integer.")
    except requests.exceptions.RequestException:
        messagebox.showerror("Server Error",
                             f"Failed to fetch CPAP pressure:{r.text}")
    return upd_cpap_pressure


def load_image(image_fn):
    """
    Load an image file and resize it while maintaining its aspect ratio.

    This function opens an image from the specified file path, calculates the
    scaling factor to resize the image proportionally to fit within a maximum
    size, and returns the resized image.

    Args:
        image_fn (str): The file path to the image file to be loaded.

    Returns:
        PIL.Image.Image: A resized PIL Image object.
    """
    pil_image = Image.open(image_fn)
    x, y = pil_image.size
    picture_size = 500
    alpha_x = picture_size / x
    alpha_y = picture_size / y
    alpha = min(alpha_x, alpha_y)
    new_x = round(x * alpha)
    new_y = round(y * alpha)
    pil_image = pil_image.resize((new_x, new_y))
    return pil_image


def main_window():

    def update_flow_image(img_path):
        """
        Update the flow image in the GUI with the given image path.

        This function loads an image from the specified file path, resizes it
        while maintaining its aspect ratio, and updates a `Label` widget in
        the GUI to display the image.

        Args:
            img_path (str): The file path to the image that will be displayed.

        Returns:
            None
        """
        img = load_image(img_path)
        img_tk = ImageTk.PhotoImage(img)
        cal_image_label.config(image=img_tk)
        cal_image_label.image = img_tk

    def cpap_file_select_btn_cmd():
        """
        Handle the selection of a CPAP data file, perform analysis, and update
        the GUI.

        This function prompts the user to select a CPAP data file, performs
        flow analysis on the file, calculates the breathing rate and apnea
        count, and generates a flow vs. time plot. The results of the analysis
        are displayed in the GUI.
        1. Asks the user to confirm the selection of a CPAP data file.
        2. Opens a file dialog for the user to select a file.
        3. Performs the following analyses:
            - Flow vs. time data analysis.
            - Breath rate calculation (breaths per minute).
            - Apnea count determination.
        4. Updates the GUI to display:
            - Breath rate.
            - Apnea count (with a red color if count ≥ 2).
            - The flow vs. time plot as an image.
        5. Handles any exceptions and displays an error message in case of
        failure.

        Args:
            None

        Returns:
            None

        Raises:
            Exception: If an error occurs during file selection, analysis, or
            GUI updates, an error message is shown in a dialog box.
        """
        choice = messagebox.askyesno(
            "Confirmation",
            "Are you sure you want to select cpap data file for analysis?")

        if choice:
            file_path = filedialog.askopenfilename()
            if file_path == "":
                return

        try:
            # Call CPAP analysis functions
            t_vs_flow = flow_analysis(file_path)
            img_path = plot_t_vs_flow(t_vs_flow)
            breath_rate = calculate_breath_rate_bpm(t_vs_flow)
            apnea_count = count_apnea(t_vs_flow)

            # Update the GUI with the results
            BR_value.set(f"{breath_rate:.2f}")  # Update breath rate label
            apnea_count_value.set(f"{apnea_count}")  # Update apnea count label
            apnea_count_value_label.config(
                foreground="red" if apnea_count >= 2 else "black"
            )  # Change color for apnea count if ≥ 2

            update_flow_image(img_path)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file: {str(e)}")

    def collect_patient_data():
        """
        Collect and validate patient data from the GUI inputs.

        This function first collect the current data include patient room, mrn,
        name(optional) and cpap calculated data(optional). Then validate the
        data before generate the dictionary to upload to the server.

        Returns:
            dict: A dictionary containing the patient data to be uploaded.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        mrn_value = mrn_result.get()
        room_value = room_result.get()
        name_value = name_result.get()
        cpap_value = cpap_result.get()
        BR = BR_value.get()
        apnea_count = apnea_count_value.get()

        out_json = generate_json_file(mrn_value, room_value, name_value,
                                      cpap_value, BR, apnea_count)

        return out_json

    def upload_btn_cmd():
        """
        Handle the upload of patient data to the server.

        Validates the required fields (MRN and Room Number) and optionally
        fields:
            - Patient Name, if provided.
            - CPAP pressure, breathing rate, apnea count, and flow image,
            if all are available.

        Sends a RESTful API request to the server to upload the patient data.
        """
        try:
            # Retrieve and validate inputs
            patient_data = collect_patient_data()
            # Send data to the server
            send_to_server(patient_data)
            mrn_entry.config(state="disabled")
            room_entry.config(state="disabled")
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Upload Error",
                                 f"Failed to connect to the server: {str(e)}")

    def update_latest_cpap_pressure():
        """
        Periodically fetch and update the latest CPAP pressure for the current
        room.

        This function checks the room number entered in the GUI. If a valid
        room number is provided, it fetches the latest CPAP pressure by calling
        `fetch_latest_cpap`. The function automatically reschedules itself to
        run again after a specified interval (30 seconds).

        Behavior:
            - If no room number is provided, the function reschedules itself
            without making a server request.
            - If a valid room number is provided, it attempts to fetch the
            CPAP pressure and updates the GUI.

        Raises:
            None: Errors are handled and displayed using `messagebox`.
        """
        room = room_result.get()

        if not room:
            root.after(30000, update_latest_cpap_pressure)  # Reschedule
            return

        upd_cpap = fetch_latest_cpap(room)
        cpap_result.set(upd_cpap)
        root.after(30000, update_latest_cpap_pressure)

    def reset_btn_cmd():
        """
        Reset all GUI fields, clear displayed data, and reactivate the MRN and
        Room fields.

        This function clears all user inputs and calculated data in the GUI,
        including CPAP pressure, patient information, and displayed images.
        It also reactivates the MRN and Room fields for editing.
        """
        cpap_result.set("")
        name_result.set("")
        mrn_result.set("")
        room_result.set("")
        BR_value.set("No available data")
        apnea_count_value.set("No available data")
        apnea_count_value_label.config(foreground="black")

        cal_image_label.config(image="")
        cal_image_label.image = None
        mrn_entry.config(state="normal")
        room_entry.config(state="normal")

    root = tk.Tk()
    root.title("Patient Station")

    # Configure root layout
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)

    # Left-side Entries
    entries_frame = ttk.Frame(root)
    entries_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Name entry
    name_label = ttk.Label(entries_frame, text="Name:")
    name_label.grid(column=0, row=0, sticky=tk.W, padx=10, pady=5)
    name_result = tk.StringVar()
    name_entry = ttk.Entry(entries_frame, textvariable=name_result)
    name_entry.grid(column=1, row=0, padx=5, pady=5)

    # MRN entry
    mrn_label = ttk.Label(entries_frame, text="Medical Record Number:")
    mrn_label.grid(column=0, row=1, sticky=tk.W, padx=10, pady=5)
    mrn_result = tk.StringVar()
    mrn_entry = ttk.Entry(entries_frame, textvariable=mrn_result)
    mrn_entry.grid(column=1, row=1, padx=5, pady=5)

    # Room entry
    room_label = ttk.Label(entries_frame, text="Room Number:")
    room_label.grid(column=0, row=2, sticky=tk.W, padx=10, pady=5)
    room_result = tk.StringVar()
    room_entry = ttk.Entry(entries_frame, textvariable=room_result)
    room_entry.grid(column=1, row=2, padx=5, pady=5)

    # CPAP pressure entry
    cpap_label = ttk.Label(entries_frame, text="CPAP pressure (cmH2O):")
    cpap_label.grid(column=0, row=3, sticky=tk.W, padx=10, pady=5)
    cpap_result = tk.StringVar()
    cpap_entry = ttk.Entry(entries_frame, textvariable=cpap_result)
    cpap_entry.grid(column=1, row=3, padx=5, pady=5)

    # Select CPAP data file
    select_btn = ttk.Button(entries_frame, text="Select CPAP Data File",
                            command=cpap_file_select_btn_cmd)
    select_btn.grid(column=0, row=4, columnspan=2, pady=10)

    # Upload button
    upload_btn = ttk.Button(entries_frame, text="Upload",
                            command=upload_btn_cmd)
    upload_btn.grid(column=0, row=6)

    # Rest button
    reset_btn = ttk.Button(entries_frame, text="Reset", command=reset_btn_cmd)
    reset_btn.grid(column=0, row=7)

    # Right-side Frame
    right_frame = ttk.Frame(root)
    right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    # Display CPAP calculated data
    result_frame = ttk.LabelFrame(right_frame, text="CPAP Calculated Data")
    result_frame.pack(fill="x", padx=5, pady=5)

    # Breath rate
    BR_label = ttk.Label(result_frame, text="Breath Rate (#/min):")
    BR_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
    BR_value = tk.StringVar(value="No available data")
    BR_value_label = ttk.Label(result_frame, textvariable=BR_value)
    BR_value_label.grid(row=0, column=1, padx=0, pady=5, sticky="w")

    # Apnea count
    apnea_label = ttk.Label(result_frame, text="Apnea Count:")
    apnea_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    apnea_count_value = tk.StringVar(value="No available data")
    apnea_count_value_label = ttk.Label(result_frame,
                                        textvariable=apnea_count_value)
    apnea_count_value_label.grid(row=1, column=1, padx=0, pady=5, sticky="w")

    image_label = ttk.Label(result_frame, text="CPAP Flow Image:")
    image_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

    cal_image_label = ttk.Label(result_frame)
    cal_image_label.grid(row=3, column=1, columnspan=2, padx=10, pady=10,
                         sticky="n")
    update_latest_cpap_pressure()
    root.mainloop()

    print("Displaying main window")


if __name__ == "__main__":
    main_window()
