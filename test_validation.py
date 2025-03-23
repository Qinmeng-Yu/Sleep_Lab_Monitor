import pytest


@pytest.mark.parametrize("input, expected", [
    (4, True),
    ("4", "The CPAP entry must be an integer."),
    (27, "CPAP value out of range. Must be between 4 and 25 inclusive.")])
def test_validate_cpap_data(input, expected):
    from validate import validate_cpap_data
    answer = validate_cpap_data(input)
    assert answer == expected


@pytest.mark.parametrize("in_data, expected", [
    ({"room": 123,
      "mrn": 7823}, True),
    ({"room": 123}, "The mrn was not found."),
    ({"room": 123,
      "mrn": "7823"}, "Invalid type for key 'mrn'.")
])
def test_validate_input_data_mrn_room(in_data, expected):
    from validate import validate_input_data
    answer = validate_input_data(in_data)
    assert answer == expected


@pytest.mark.parametrize("in_data, expected", [
    ({"room": 123,
      "mrn": 7823,
      "name": "Qinmeng Yu"}, True),
    ({"room": 123,
      "mrn": 7823,
      "name": 1234}, "Invalid type for key 'name'. Expected str."),
])
def test_validate_input_data_name(in_data, expected):
    from validate import validate_input_data
    answer = validate_input_data(in_data)
    assert answer == expected


@pytest.mark.parametrize("in_data, expected", [
    ({"room": 123,
      "mrn": 7823,
      "name": "Qinmeng Yu",
      "data": []}, True),
    ({"room": 123,
      "mrn": 7823,
      "name": "Qinmeng Yu",
      "data": {
            "cpap_pressure": 12,
            "breathing_rate": 17,
            "apnea_count": 4,
            "flow_image_base64": "iVBORw0KGgo",
            "timestamp": "2024-11-23T12:00:00Z"}},
        "Invalid type for key 'data'. Expected list."),
    ({"room": 123,
      "mrn": 7823,
      "name": "Qinmeng Yu",
      "data": [{
            "cpap_pressure": 12,
            "breathing_rate": 17,
            "apnea_count": 4,
            "flow_image_base64": "iVBORw0KGgo",
            "timestamp": "2024-11-23T12:00:00Z"}]}, True),
    ({"room": 123,
      "mrn": 7823,
      "name": "Qinmeng Yu",
      "data": [[12, 17]]}, "Each entry in 'data' must be a dictionary."),
    ({"room": 123,
      "mrn": 7823,
      "name": "Qinmeng Yu",
      "data": [{
            "cpap_pressure": 12,
            "breathing_rate": 17,
            "apnea_count": 4,
            "timestamp": "2024-11-23T12:00:00Z"}]},
        "Missing key 'flow_image_base64' in data entry.")
])
def test_validate_input_data_data(in_data, expected):
    from validate import validate_input_data
    answer = validate_input_data(in_data)
    assert answer == expected
