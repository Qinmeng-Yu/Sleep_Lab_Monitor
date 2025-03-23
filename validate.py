def validate_input_data(in_data):
    """
    Validates the input data to ensure it meets the required structure and
    types.

    Args:
        in_data (dict): The input data dictionary to validate.
        Expected keys include:
            - "mrn" (int): The medical record number.
            - "room" (int): The room number.
            - Optional "name" (str): The patient's name.
            - Optional "data" (list): A list of dictionaries containing
               patient data entries.

    Returns:
        str or bool
            - Returns a string with an error message if the validation fails:
                - Missing required keys (e.g., "The mrn was not found.")
                - Incorrect data types (e.g., "Invalid type for key 'room'.")
                - Missing or invalid fields in the "data" list (e.g., "Missing
                  key 'cpap_pressure' in data entry.")
            - Returns True if the input data is valid.
    """
    expected_keys = ["mrn", "room"]
    expected_types = [int, int]

    for key, expected_type in zip(expected_keys, expected_types):
        if key not in in_data:
            return f"The {key} was not found."
        if not isinstance(in_data[key], expected_type):
            return f"Invalid type for key '{key}'."
        " Expected {expected_type.__name__}."

    if "name" in in_data and not isinstance(in_data["name"], str):
        return "Invalid type for key 'name'. Expected str."

    # Validate 'data' field if present
    if "data" in in_data:
        if not isinstance(in_data["data"], list):
            return "Invalid type for key 'data'. Expected list."
        if not in_data["data"]:
            return True

        for entry in in_data["data"]:
            if not isinstance(entry, dict):
                return "Each entry in 'data' must be a dictionary."

            required_data_keys = [
                "cpap_pressure",
                "breathing_rate",
                "apnea_count",
                "flow_image_base64"
            ]

            for key in required_data_keys:
                if key not in entry:
                    return f"Missing key '{key}' in data entry."

            # try:
            #     datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            # except ValueError:
            #     return f"Invalid timestamp format in data entry: {
            #         entry['timestamp']}"

    return True


def validate_cpap_data(cpap_value):
    """
    Validates the given CPAP value to ensure it meets the required criteria.

    Args:
        cpap_value (int): The CPAP pressure value to validate.

    Returns:
        str or bool
            - Returns a str with an error message if the value is invalid:
               - "The CPAP entry must be an integer."
               - "CPAP value out of range. Must be between 4 and 25 inclusive."
            - Returns True if the value is valid.
    """
    if not isinstance(cpap_value, int):
        return "The CPAP entry must be an integer."

    if not 4 <= cpap_value <= 25:
        return "CPAP value out of range. Must be between 4 and 25 inclusive."

    return True
