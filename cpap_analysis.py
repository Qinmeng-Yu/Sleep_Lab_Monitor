import logging
import numpy as np
from math import sqrt
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import json
import os

logging.basicConfig(filename="cpap_analysis.log", level=logging.INFO)


def is_correct_data(line, patient):
    """
    Validated patient's data by checking each data points.

    This function checks if the given patient data contains exactly 7 elements.
    If the data miss element, it logs a missing value error. It also checks if
    each element is numeric and logs nonumeric values or NaNs separately.

    Parameters:
    line (int): The line number of the patient data for logging purposes.
    patient (list): A list of strings representing patient data.

    Returns:
    bool: True if all element are valid, False otherwise.
    """
    if len(patient) != 7:
        logging.error(f"Missing value in line {line}: {patient}")
        return False
    for data in patient:
        try:
            float(data)
        except ValueError:
            logging.error(f"Non-numeric string in line {line}: {patient}")
            return False
        if data == "NaN":
            logging.error(f"Nan value in line {line}: {patient}")
            return False
    return True


def load_patient(path):
    """
    Load patient data from the given text file.

    This function loads patient data with specific file path, checks each line
    for invalid value or missing elements, and logs error accordingly. After
    validation, valid data is returned in form of list.

    Parameters:
    path(str): patient data text path.

    Returns:
    valid_data(list):
    A list of lists, where the first list contains the header keys, and the
    subsequent lists contain valid patient data.

    """
    valid_data = []
    with open(path, "r") as file:
        keys = file.readline().strip("\n").split(",")
        valid_data.append(keys)
        # print(keys)
        for i, line in enumerate(file):
            patient_data = line.strip("\n").split(",")
            if is_correct_data(i+2, patient_data):
                valid_data.append(patient_data)
    return valid_data


def ADC_to_pascal(ADC_value):
    """
    Convert ADC units into pascal.

    This function first converts ADC units into a pressure reading in cm-H2O.
    Then converts cm-H2O to pascal for further calculation.

    Parameters:
    ADC_value(int): Given ADC_value pressure.

    Returns:
    pascal(float): pressure in pascal unit.
    """
    cm_H2O = ((25.4) / (14745 - 1638)) * (ADC_value - 1638)
    pascal = 98.0665 * cm_H2O
    return pascal


def flow_calculation(p1, p2):
    """
    Calculate volumetric flow based on given equation.

    The calculation is based on the following formula:
        Q = A1 * sqrt( (2 / density) * (p1 - p2) / ( (A1 / A2)^2 - 1 ) )
    where:
    - Q is the volumetric flow rate (m^3/sec)
    - A1 is the upstream cross-sectional area (m^2)
    - A2 is the cross-sectional area at the constriction (m^2)
    - density is the air density (kg/m^3) (1.99kg/m^3)
    - p1 is the upstream pressure (Pa)
    - p2 is the pressure at the constriction (Pa)

    Parameters:
    p1(float): The upstream pressure (Pa).
    p2(float): The pressure at the constriction (Pa).

    Returns:
    Q(float): Volumetric flow raterate (m^3/sec)
    """
    density = 1.199
    d1 = 15 * 10**-3
    d2 = 12 * 10**-3
    A1 = np.pi * (d1 / 2)**2
    A2 = np.pi * (d2 / 2)**2

    Q = A1 * sqrt((2 / density) * (p1 - p2) / ((A1 / A2)**2 - 1))

    return Q


def flow_analysis(path):
    """
    Perform flow calculation on patient data from a given file.

    This function loads patient data utilizing load_patient(), calculates
    the volumetric flow rate with flow_caculation and returns time and flow
    rate lists. It compares The p1_ins and p1_exp to distinguish between
    inspiratory and expiratory flow. Positive flow indicates inspiration,
    while negative flow indicates expiration.

    Parameters:
    path(str): patient data text path.

    Returns:
    list: A list containing two elements:
        - time (list of float): List of time values (in seconds).
        - flow_data (list of float): List of calculated flow rates (in m³/s).
    """
    logging.info(f"Starting analysis of file: {path}")
    time = []
    flow_data = []

    valid_data = load_patient(path)
    for i in range(1, len(valid_data)):
        time.append(float(valid_data[i][0]))
        p2 = ADC_to_pascal(int(valid_data[i][1]))
        p1_ins = ADC_to_pascal(int(valid_data[i][2]))
        p1_exp = ADC_to_pascal(int(valid_data[i][3]))
        if p1_ins >= p1_exp:
            Q = flow_calculation(p1_ins, p2)
        else:
            Q = -flow_calculation(p1_exp, p2)
        flow_data.append(Q)

    return [time, flow_data]


def calculate_duration(t_vs_flow):
    """
    Calcualte time duration.

    This function calculates time duration of the raw data in seconds
    from the time versus flow rate data.

    Parameters:
    t_vs_flow(List):A list containing two elements:
    - time (list of float): List of time values (in seconds).
    - flow_data (list of float): List of calculated flow rates (in m³/s).

    Returns:
    Float: time duration
    """
    time = t_vs_flow[0]
    return time[-1] - time[0]


def count_breaths(flow_data, h=11e-5, pro=2.5e-4, d=49):
    """
    Count the number of breaths by detecting positive peaks.

    Each positive peak represents a breath. The peak-finding method filters
    out small fluctuations by setting a minimum peak height,
    distance, and prominence. Addictional filter methods are applied
    to further filters out missed noise.

    Parameters:
    flow_data (list of float): List of calculated flow rates (in m³/s).
    h (float): Minimum height required for a peak to be considered a breath.
    d (int): Minimum number of samples between consecutive peaks.
    pro (float): Required prominence of the peaks to filter out noise.

    Returns:
    valid_peaks (np.array): peaks indices.
    int: The number of breaths detected.
    """
    # Use find_peaks to detect peaks roughly
    peaks, _ = find_peaks(flow_data, height=h, prominence=pro, distance=d)
    length = len(peaks)

    # Check if any peaks are found
    if len(peaks) == 0:
        return (np.array([]), 0)

    # Validate peaks by checking zero crossing and time period.
    valid_peaks = []
    for i in range(length-1):
        check_zero = 0 in flow_data[peaks[i]:peaks[i+1]]
        check_negative = any(n < 0 for n in flow_data[peaks[i]:peaks[i+1]])
        check_time = (flow_data[peaks[i]+1] != 0)

        if check_time and (check_zero or check_negative):
            valid_peaks.append(peaks[i])
    if 0 in flow_data[peaks[-1]:-1]:
        valid_peaks.append(peaks[-1])
    valid_peaks = np.array(valid_peaks)

    return valid_peaks, len(valid_peaks)


def calculate_breath_rate_bpm(t_vs_flow):
    """
    Calculate the average breathing rate from the data in breaths per minute.

    This function calculate the breath rate bpm by diving numbers of breaths
    by breathing duration.

    Parameters:
    t_vs_flow(List):A list containing two elements:
    - time (list of float): List of time values (in seconds).
    - flow_data (list of float): List of calculated flow rates (in m³/s).

    Returns:
    float: breath rate bpm.
    """
    duration = calculate_duration(t_vs_flow)
    breaths = count_breaths(t_vs_flow[1])[1]
    return float(breaths/duration * 60)


def calculate_breath_times(t_vs_flow):
    """
    Calculate the time in seconds from the data at which each breath occurs.

    This function returns a list of time points (in seconds) corresponding to
    the detected breath peaks from the provided time and flow data. It detects
    breaths by identifying the positive peaks in the flow data.

    Parameters:
    t_vs_flow(List):A list containing two elements:
    - time (list of float): List of time values (in seconds).
    - flow_data (list of float): List of calculated flow rates (in m³/s).

    Returns:
    List: A list of times (in seconds) when each breath occurs.
    """
    time, flow_data = t_vs_flow
    time = np.array(time)
    valid_peaks, breaths = count_breaths(flow_data)
    if breaths == 0:
        return []

    return time[valid_peaks].tolist()


def count_apnea(t_vs_flow):
    """
    Count the number of apnea from patient data.

    This function count number of apnea events in the data. An apnea event
    occurs when the time elapsed between breaths (the time between observed
    peaks) is more than 10 seconds.

    Parameters:
    t_vs_flow(List):A list containing two elements:
    - time (list of float): List of time values (in seconds).
    - flow_data (list of float): List of calculated flow rates (in m³/s).

    Returns:
    apnea_count(int): number of apnea
    """
    breath_times = calculate_breath_times(t_vs_flow)
    if breath_times == []:
        return 0
    apnea_count = 0
    for i in range(len(breath_times)-1):
        if (breath_times[i+1] - breath_times[i]) > 10:
            apnea_count += 1
    return apnea_count


def calculate_leakage(t_vs_flow):
    """
    Calculate the total mask leakage observed in the patient data.

    This function calculates the total leakage of air through the mask by
    integrating the flow rate over time and converting the result from cubic
    meters to liters. The leakage is determined by summing the flow at each
    time step multiplied by the time difference between the steps (numerical
    integration). A warning is logged if the total leakage is negative.

    Parameters:
    t_vs_flow (list): A list containing two elements:
        - time (list of float): A list of time values (in seconds).
        - flow_data (list of float): A list of calculated flow rates (in m³/s).

    Returns:
    float: The total leakage in liters (1 m³ = 1000 liters).
    """
    time, flow = t_vs_flow
    time, flow = np.array(time), np.array(flow)

    dt = np.diff(time)
    total_leakage = 0.0
    for i in range(len(flow) - 1):
        total_leakage += flow[i] * dt[i]

    # Convert from cubic meters to liters
    total_leakage_liters = total_leakage * 1000
    if total_leakage_liters < 0:
        logging.warning("Negative leakage detected.")
    return total_leakage_liters


def get_metrics(t_vs_flow, input_file):
    """
    Calculate and save patient metrics based on flow data.

    This function returns a dictionary called metrics, where the key-value
    pairs are:
    - duration: float, the time duration of the raw data in seconds
    - breaths: integer, number of breaths in the data
    - breath_rate_bpm: float, the average breathing rate from the data in
    breaths per minute
    - breath_times: list of floats, the time in seconds from the data at which
    each breath occurs (not the duration of each breath)
    - apnea_count: integer, number of apnea events in the data
    - leakage: float, the total amount of mask leakage observed in the data in
    liters
    It also outputs the metrics dictionary to a JSON file, with the same name
    as the input file but with a .json extension.

    Parameters:
    t_vs_flow (list): A list containing two elements:
        - time (list of float): List of time values (in seconds).
        - flow_data (list of float): List of calculated flow rates (in m³/s).
    input_file(str): patient data text path.

    Returns:
    dict: A dictionary containing the calculated metrics (duration, breaths,
          breath_rate_bpm, breath_times, apnea_count, and leakage).

    """
    duration = calculate_duration(t_vs_flow)
    breaths = count_breaths(t_vs_flow[1])[1]
    breath_rate_bpm = calculate_breath_rate_bpm(t_vs_flow)
    breath_times = calculate_breath_times(t_vs_flow)
    apnea_count = count_apnea(t_vs_flow)
    leakage = calculate_leakage(t_vs_flow)

    metrics = {
        "duration": float(duration),
        "breaths": int(breaths),
        "breath_rate_bpm": float(breath_rate_bpm),
        "breath_times": breath_times,
        "apnea_count": int(apnea_count),
        "leakage": float(leakage)
    }

    output_file = os.path.splitext(os.path.basename(input_file))[0] + ".json"
    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=4)

    return metrics


def plot_t_vs_flow(t_vs_flow):
    """
    Plot flow vs. time and save the plot to an image file.

    This function takes a tuple containing time and flow data, generates a
    plot of flow vs. time, and saves the resulting plot as an image file in
    JPEG format.

    Args:
        t_vs_flow (tuple): A tuple of two lists or arrays:
            - time: The time data (x-axis values).
            - flow: The flow data (y-axis values).

    Returns:
        str: The file path of the saved plot image ("flow_plot.jpg").
    """
    time, flow = t_vs_flow
    # plt.figure()
    plt.figure(figsize=(9, 4))
    plt.plot(time, flow)
    plt.xlabel("Time (s)")
    plt.ylabel("Flow ($m^3$/sec)")
    plt.title("Flow - Time")
    plt.grid(True)
    # Save the plot as an image
    img_path = "flow_plot.jpg"
    plt.savefig(img_path, dpi=300)
    plt.close()
    return img_path


if __name__ == "__main__":
    # data = load_patient('sample_data/patient_01.txt')
    # print(len(data))
    path = 'sample_data/patient_02.txt'
    t_vs_flow = flow_analysis(path)
    # t_vs_flow = ([0, 1, 2, 3], [0, 0, 0, 0])
    time, flow = t_vs_flow
    # peak, breaths = count_breaths(flow)
    # print(peak)
    # selected_times = [time[i] for i in peak]
    # selected_flows = [flow[i] for i in peak]

    # time = np.array(time)
    # flow = np.array(flow)
    # mask = (time >= 5) & (time <= 7.5)
    # part_time = time[mask]
    # part_flow = flow[mask]

    # plt.figure(figsize=(15, 7))
    # plt.plot(selected_times, selected_flows, 'r+',
    # label=f"{breaths} breaths")
    plt.plot(time, flow)
    # plt.plot(part_time, part_flow, label="part")
    # plt.xlabel("Time (s)")
    plt.ylabel("Flow ($m^3$/sec)")
    plt.title(f"Flow - Time of {path}")
    plt.grid(True)
    plt.show()

    # print(f"number of breaths: {breaths}")
    # print(f"duration: {calculate_duration(t_vs_flow)}")
    # print(f"bpm: {calculate_breath_rate_bpm(t_vs_flow)}")
    # print(f"breath times: {calculate_breath_times(t_vs_flow)}")
    # print(f"number of apnea {count_apnea(t_vs_flow)}")
    # print(f"leakage: {calculate_leakage(t_vs_flow)}")
    metrics = get_metrics(t_vs_flow, path)
    print("bpm:", metrics["breath_rate_bpm"])
    print("apnea count:", metrics["apnea_count"])

    print(metrics)
