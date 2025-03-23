# import pytest
from unittest.mock import Mock, patch
import pytest
from patient_interface import generate_json_file, send_to_server
from patient_interface import fetch_latest_cpap, load_image
from PIL import Image


@patch("patient_interface.requests.get")
@patch("patient_interface.messagebox.showerror")
def test_fetch_latest_cpap_success(mock_showerror, mock_get):
    """
    Test successful fetching of CPAP pressure.
    """

    # Mock the server response
    mock_response = {"cpap_pressure": 15}
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status = Mock()

    result = fetch_latest_cpap("101")
    assert result == "15"
    mock_showerror.assert_not_called()


@patch("patient_interface.requests.get")
@patch("patient_interface.messagebox.showerror")
def test_fetch_latest_cpap_no_data(mock_showerror, mock_get):
    """
    Test fetching CPAP pressure when no data is available.
    """

    # Mock the server response with no CPAP pressure
    mock_response = {"cpap_pressure": None}
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status = Mock()

    result = fetch_latest_cpap("101")
    assert result == ""
    mock_showerror.assert_not_called()


@patch("patient_interface.requests.get")
@patch("patient_interface.messagebox.showerror")
def test_fetch_latest_cpap_invalid_room_number(mock_showerror, mock_get):
    """
    Test fetching CPAP pressure with an invalid room number.
    """

    result = fetch_latest_cpap("invalid")
    assert result == ""
    mock_get.assert_not_called()
    mock_showerror.assert_called_once_with(
        "Validation Error", "Room number must be an integer."
    )


def test_generate_json_valid_data():
    with patch("patient_interface.read_file_as_b64",
               return_value="dummy_base64"):
        json_output = generate_json_file(
            mrn_value="123",
            room_value="101",
            name_value="Chloe Yu",
            cpap_value="24",
            BR="15.9",
            apnea_count="3"
        )
    assert json_output["mrn"] == 123
    assert json_output["room"] == 101
    assert json_output["name"] == "Chloe Yu"
    assert "data" in json_output
    assert json_output["data"][0]["breathing_rate"] == 15.9
    assert json_output["data"][0]["apnea_count"] == 3
    assert json_output["data"][0]["flow_image_base64"] == "dummy_base64"


def test_generate_json_no_data():
    """
    Test generating JSON when no CPAP pressure or calculated data is provided.
    """
    json_output = generate_json_file(
        mrn_value="123",
        room_value="101",
        name_value="Chloe Yu",
        cpap_value="",
        BR="No available data",
        apnea_count="No available data"
    )
    assert json_output["mrn"] == 123
    assert json_output["room"] == 101
    assert json_output["name"] == "Chloe Yu"
    assert "cpap_pressure" not in json_output
    assert "data" not in json_output


def test_generate_json_cpap_without_data():
    """
    Test error when CPAP pressure is provided without calculated data.
    """
    with pytest.raises(
         ValueError,
         match="Cannot upload CPAP pressure without CPAP calculated data."):
        generate_json_file(
            mrn_value="123",
            room_value="101",
            name_value="Chloe Yu",
            cpap_value="24",
            BR="No available data",
            apnea_count="No available data"
        )


def test_generate_json_invalid_mrn_room():
    """
    Test error when MRN or room is not an integer.
    """
    with pytest.raises(
        ValueError,
         match="MRN and Room Number must be integers."):
        generate_json_file(
            mrn_value="abc",
            room_value="101",
            name_value="Chloe Yu",
            cpap_value="24",
            BR="15.9",
            apnea_count="3"
        )


def test_generate_json_missing_mrn_room():
    """
    Test error when MRN or room is missing.
    """
    with pytest.raises(ValueError, match="MRN and Room Number are required."):
        generate_json_file(
            mrn_value="",
            room_value="101",
            name_value="Chloe Yu",
            cpap_value="24",
            BR="15.9",
            apnea_count="3"
        )


@patch("patient_interface.requests.post")
@patch("patient_interface.messagebox.showinfo")
def test_send_to_server_success(mock_showinfo, mock_post):
    """
    Test sending patient data successfully to the server.
    """
    mock_post.return_value = Mock(status_code=200)

    patient_data = {
        "mrn": 123,
        "room": 101,
        "name": "Chloe Yu",
        "data": [{
            "cpap_pressure": 10,
            "breathing_rate": 15.9,
            "apnea_count": 3,
            "flow_image_base64": "dummy_base64"
        }]
    }

    send_to_server(patient_data)

    # mock_post.assert_called_once_with(
    #     "http://127.0.0.1:5000/upload_patient", json=patient_data
    # )
    mock_showinfo.assert_called_once_with(
        "Success", "Patient data uploaded successfully!"
    )


@patch("patient_interface.requests.post")
@patch("patient_interface.messagebox.showerror")
def test_send_to_server_failure(mock_showerror, mock_post):
    """
    Test handling of server response failure when uploading patient data.
    """
    mock_post.return_value = Mock(status_code=400, text="Bad Request")

    patient_data = {
        "mrn": 123,
        "room": 101,
        "name": "Chloe Yu",
        "data": [{
            "cpap_pressure": 10,
            "breathing_rate": 15.9,
            "apnea_count": 3,
            "flow_image_base64": "dummy_base64"
        }]
    }

    send_to_server(patient_data)

    # mock_post.assert_called_once_with(
    #     "http://127.0.0.1:5000/upload_patient", json=patient_data
    # )
    mock_showerror.assert_called_once_with(
        "Upload Error", "Server responded with: Bad Request"
    )


def test_load_image():
    test_image_path = "test_image.jpg"

    original_image = Image.open(test_image_path)
    original_width, original_height = original_image.size

    resized_image = load_image(test_image_path)

    assert isinstance(resized_image, Image.Image), (
        "The returned object is not a PIL Image.")

    resized_width, resized_height = resized_image.size
    max_size = 500
    assert resized_width <= max_size and resized_height <= max_size, (
        f"Resized dimensions {resized_width}x{resized_height}"
        "exceed maximum size {max_size}."
    )

    original_aspect_ratio = original_width / original_height
    resized_aspect_ratio = resized_width / resized_height
    assert abs(original_aspect_ratio - resized_aspect_ratio) < 0.01, (
        "Aspect ratio is not maintained in the resized image."
    )
