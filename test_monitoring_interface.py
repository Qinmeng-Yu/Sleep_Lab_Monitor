import pytest
from unittest.mock import Mock, patch, MagicMock
from monitoring_interface import fetch_selected_image, display_image
from monitoring_interface import fetch_latest_data, fetch_timestamps
from monitoring_interface import download_image, download_latest_image
from monitoring_interface import download_selected_image, periodic_update
from monitoring_interface import fetch_rooms, update_cpap_pressure
import base64
from PIL import Image
import io
import requests
import tkinter as tk


root = tk.Tk()
root.withdraw()


@pytest.fixture(scope="module", autouse=True)
def setup_tkinter():
    root = tk.Tk()
    root.withdraw()
    yield
    root.destroy()


@pytest.fixture
def mock_image_label():
    """
    Fixture for mocking a Tkinter Label.

    Returns:
        Mock: A mocked Tkinter Label object.
    """
    label = Mock()
    label.config = Mock()
    return label


@pytest.fixture
def mock_text_widget():
    """
    Fixture for mocking a Tkinter Text widget.

    Returns:
        Mock: A mocked Tkinter Text widget.
    """
    text_widget = Mock()
    text_widget.delete = Mock()
    text_widget.insert = Mock()
    text_widget.tag_configure = Mock()
    return text_widget


@pytest.fixture
def mock_combobox():
    """
    Fixture for mocking a Tkinter Combobox.

    Returns:
        MagicMock:
            A mocked Tkinter Combobox object with dictionary-like behavior.
    """
    combobox = MagicMock()
    combobox.values_store = []
    combobox.__getitem__.side_effect = (
        lambda key: combobox.values_store if key == "values" else None
    )
    combobox.__setitem__.side_effect = (
        lambda key, value: combobox.values_store.extend(value)
        if key == "values"
        else None
    )
    combobox.set = MagicMock()
    return combobox


@patch("monitoring_interface.requests.get")
def test_fetch_rooms_success(mock_get, mock_combobox):
    """
    Test successful fetching and display of room numbers.

    Args:
        mock_get (Mock): Mocked requests.get function.
        mock_combobox (Mock): Mocked Tkinter Combobox for room selection.

    Returns:
        None
    """
    mock_response = {"rooms": [101, 102, 103]}
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status = Mock()

    fetch_rooms(mock_combobox)

    assert mock_combobox["values"] == [101, 102, 103]


@patch("monitoring_interface.requests.get")
def test_fetch_rooms_error(mock_get, mock_combobox):
    """
    Test error handling when fetching room numbers fails.

    Args:
        mock_get (Mock): Mocked requests.get function.
        mock_combobox (Mock): Mocked Tkinter Combobox for room selection.

    Returns:
        None
    """
    mock_get.side_effect = requests.RequestException("Network Error")

    with patch("monitoring_interface.messagebox.showerror") as mock_showerror:
        fetch_rooms(mock_combobox)

        mock_showerror.assert_called_once_with(
            "Error", "Failed to fetch rooms: Network Error")


def test_display_image_success(mock_image_label):
    """
    Test the successful display of an image from a base64 string.

    Args:
        mock_image_label (Mock): Mocked Tkinter Label to display the image.

    Returns:
        None
    """
    # Mock base64 image data
    dummy_image = Image.new("RGB", (100, 100), color="red")
    with io.BytesIO() as buffer:
        dummy_image.save(buffer, format="PNG")
        base64_string = base64.b64encode(buffer.getvalue()).decode()

    with patch("monitoring_interface.ImageTk.PhotoImage") as mock_photo:
        display_image(base64_string, mock_image_label)

        assert mock_image_label.config.called
        assert mock_image_label.image == mock_photo.return_value


def test_display_image_error(mock_image_label):
    """
    Test the error handling in display_image when invalid data is provided.

    Args:
        mock_image_label (Mock): Mocked Tkinter Label for image display.

    Returns:
        None
    """
    invalid_base64 = "invalid_base64"
    display_image(invalid_base64, mock_image_label)
    assert mock_image_label.config.called
    assert mock_image_label.config.call_args[1]["text"] == (
        "Error loading image")


@patch("monitoring_interface.requests.get")
def test_fetch_latest_data_success(
        mock_get, mock_image_label, mock_text_widget):
    """
    Test successful fetch and display of the latest CPAP data.

    Args:
        mock_get (Mock): Mocked requests.get function.
        mock_image_label (Mock): Mocked Tkinter Label for image display.
        mock_text_widget (Mock): Mocked Tkinter Text widget for data display.

    Returns:
        None
    """
    mock_response = {
        "cpap_pressure": 10,
        "breathing_rate": 16,
        "apnea_count": 1,
        "timestamp": "2024-12-05T14:30:00",
        "flow_image_base64": "dummy_base64",
    }
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status = Mock()

    with patch("monitoring_interface.display_image") as mock_display_image:
        fetch_latest_data("101", Mock(), mock_text_widget, mock_image_label)

        assert mock_text_widget.delete.called
        assert mock_text_widget.insert.called
        mock_display_image.assert_called_once()


@patch("monitoring_interface.requests.get")
def test_fetch_latest_data_error(mock_get, mock_image_label, mock_text_widget):
    """
    Test error handling when fetching the latest data fails.

    Args:
        mock_get (Mock): Mocked requests.get function.
        mock_image_label (Mock): Mocked Tkinter Label for image display.
        mock_text_widget (Mock): Mocked Tkinter Text widget for data display.

    Returns:
        None
    """
    mock_get.side_effect = requests.RequestException("Network Error")

    with patch("monitoring_interface.messagebox.showerror") as mock_showerror:
        fetch_latest_data("101", Mock(), mock_text_widget, mock_image_label)

        mock_showerror.assert_called_once_with(
            "Error", "Failed to fetch latest data: Network Error")


@patch("monitoring_interface.requests.get")
def test_fetch_timestamps_success(mock_get, mock_combobox):
    """
    Test successful fetching and display of timestamps.

    Args:
        mock_get (Mock): Mocked requests.get function.
        mock_combobox (Mock): Mocked Tkinter Combobox for timestamp display.

    Returns:
        None
    """
    mock_response = {
        "timestamps": ["2024-12-05T14:30:00", "2024-12-05T15:00:00"]}
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status = Mock()

    fetch_timestamps("101", mock_combobox)

    # Verify the assigned values
    assert mock_combobox["values"] == [
        "2024-12-05 14:30:00",
        "2024-12-05 15:00:00",
    ]
    mock_combobox.set.assert_called_once_with("2024-12-05 15:00:00")


@patch("monitoring_interface.requests.get")
def test_fetch_timestamps_error(mock_get, mock_combobox):
    """
    Test error handling when fetching timestamps fails.

    Args:
        mock_get (Mock): Mocked requests.get function.
        mock_combobox (Mock): Mocked Tkinter Combobox for timestamp display.

    Returns:
        None
    """
    mock_get.side_effect = requests.RequestException("Network Error")

    with patch("monitoring_interface.messagebox.showerror") as mock_showerror:
        fetch_timestamps("101", mock_combobox)

        mock_showerror.assert_called_once_with(
            "Error", "Failed to fetch timestamps: Network Error")


@pytest.fixture
def mock_selected_image_label():
    """
    Fixture for mocking a Tkinter Label for selected images.

    Returns:
        Mock: A mocked Tkinter Label object.
    """
    label = Mock()
    label.config = Mock()
    return label


@patch("monitoring_interface.requests.get")
def test_fetch_selected_image_success(mock_get, mock_selected_image_label):
    """
    Test the successful fetching and display of a selected flow image.

    Args:
        mock_get (Mock): Mocked requests.get function.
        mock_selected_image_label (Mock):
            Mocked Tkinter Label for image display.

    Returns:
        None
    """
    mock_response = {"flow_image_base64": "dummy_base64"}
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status = Mock()

    with patch("monitoring_interface.display_image") as mock_display_image:
        fetch_selected_image(
            "101", "2024-12-05 14:30:00", mock_selected_image_label)
        mock_display_image.assert_called_once_with(
            "dummy_base64", mock_selected_image_label)


@patch("monitoring_interface.requests.get")
def test_fetch_selected_image_error(mock_get, mock_selected_image_label):
    """
    Test error handling when fetching a selected flow image fails.

    Args:
        mock_get (Mock): Mocked requests.get function.
        mock_selected_image_label (Mock):
        Mocked Tkinter Label for image display.

    Returns:
        None
    """
    mock_get.side_effect = requests.RequestException("Network Error")

    with patch("monitoring_interface.messagebox.showerror") as mock_showerror:
        fetch_selected_image(
            "101", "2024-12-05 14:30:00", mock_selected_image_label)

        mock_showerror.assert_called_once_with(
            "Error", "An unexpected error occurred: Network Error")


# @patch("builtins.open", new_callable=mock_open)
# def test_download_image_success(mock_open):
#     root = tk.Tk()  # Create the master
#     root.withdraw()  # Hide the Tkinter window (optional)
#     try:
#         dummy_data = b"dummy_image_data"
#         base64_string = base64.b64encode(dummy_data).decode()

#         # Call the function
#         download_image(base64_string, "test_image.png")

#         # Assert that open was called correctly
#         mock_open.assert_called_once_with("test_image.png", "wb")
#         # Assert the write method was called with the correct data
#         mock_open().write.assert_called_once_with(dummy_data)
#     finally:
#         root.destroy()


@patch("monitoring_interface.messagebox.showerror")
def test_download_image_error(mock_showerror):
    """
    Test error handling when downloading an image fails.

    Args:
        mock_showerror (Mock): Mocked messagebox.showerror function.

    Returns:
        None
    """
    invalid_base64 = "invalid_base64"

    download_image(invalid_base64, "test_image.png")

    # Assert that showerror is called with the general structure of the error
    mock_showerror.assert_called_once()
    args, _ = mock_showerror.call_args
    assert "Error" in args[0]
    assert "Failed to download image" in args[1]


@patch("monitoring_interface.requests.get")
@patch("monitoring_interface.download_image")
def test_download_latest_image_success(mock_download, mock_get):
    """
    Test successful fetching and downloading of the latest image.

    Args:
        mock_download (Mock): Mocked download_image function.
        mock_get (Mock): Mocked requests.get function.

    Returns:
        None
    """
    mock_response = {"flow_image_base64": "dummy_base64"}
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status = Mock()

    selected_room_var = Mock()
    selected_room_var.get.return_value = "101"
    download_latest_image(selected_room_var)

    mock_download.assert_called_once_with(
        "dummy_base64", "latest_flow_image_101.png")


@patch("monitoring_interface.requests.get")
def test_download_latest_image_error(mock_get):
    """
    Test error handling when downloading the latest image fails.

    Args:
        mock_get (Mock): Mocked requests.get function.

    Returns:
        None
    """
    mock_get.side_effect = requests.RequestException("Network Error")

    selected_room_var = Mock()
    selected_room_var.get.return_value = "101"

    with patch("monitoring_interface.messagebox.showerror") as mock_showerror:
        download_latest_image(selected_room_var)

        mock_showerror.assert_called_once_with(
            "Error", "Failed to fetch latest image: Network Error")


@patch("monitoring_interface.requests.get")
@patch("monitoring_interface.download_image")
def test_download_selected_image_success(mock_download, mock_get):
    """
    Test successful fetching and downloading of a selected image.

    Args:
        mock_download (Mock): Mocked download_image function.
        mock_get (Mock): Mocked requests.get function.

    Returns:
        None
    """
    mock_response = {"flow_image_base64": "dummy_base64"}
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status = Mock()

    selected_room_var = Mock()
    selected_room_var.get.return_value = "101"
    selected_timestamp_var = Mock()
    selected_timestamp_var.get.return_value = "2024-12-05 14:30:00"

    download_selected_image(selected_room_var, selected_timestamp_var)

    mock_download.assert_called_once_with(
        "dummy_base64", "flow_image_101_2024-12-05_14_30_00.jpg")


@patch("monitoring_interface.requests.get")
def test_download_selected_image_error(mock_get):
    """
    Test error handling when downloading a selected image fails.

    Args:
        mock_get (Mock): Mocked requests.get function.

    Returns:
        None
    """
    mock_get.side_effect = requests.RequestException("Network Error")

    selected_room_var = Mock()
    selected_room_var.get.return_value = "101"
    selected_timestamp_var = Mock()
    selected_timestamp_var.get.return_value = "2024-12-05 14:30:00"

    with patch("monitoring_interface.messagebox.showerror") as mock_showerror:
        download_selected_image(selected_room_var, selected_timestamp_var)

        mock_showerror.assert_called_once_with(
            "Error", "Failed to fetch selected image: Network Error")


@patch("monitoring_interface.requests.post")
def test_update_cpap_pressure_success(mock_post):
    """
    Test successful CPAP pressure update.

    Args:
        mock_post (Mock): Mocked requests.post function.

    Returns:
        None
    """
    mock_post.return_value.raise_for_status = Mock()

    # Mock inputs
    selected_room = "101"
    cpap_entry = Mock()
    cpap_entry.get.return_value = "10"  # Valid pressure value

    with patch("monitoring_interface.messagebox.showinfo") as mock_showinfo:
        update_cpap_pressure(selected_room, cpap_entry)

        # Assert the POST request was sent with the correct data
        mock_post.assert_called_once_with(
            f"http://127.0.0.1:5000/room/{selected_room}/update_cpap",
            json={"cpap_pressure": 10}
        )

        # Assert success message was displayed
        mock_showinfo.assert_called_once_with(
            "Success", "CPAP pressure updated successfully."
        )


def test_periodic_update_success(mock_fetch_latest_data):
    selected_room = Mock()
    selected_room.get.return_value = "101"
    room_menu = MagicMock()
    timestamp_menu = MagicMock()
    formatted_timestamp_label = Mock()
    data_text = Mock()
    latest_image_label = Mock()
    status_label = Mock()
    root = Mock()

    periodic_update(
        selected_room, room_menu, timestamp_menu,
        formatted_timestamp_label, data_text,
        latest_image_label, status_label, root
    )
    mock_fetch_latest_data.assert_called_once_with(
        "101", formatted_timestamp_label, data_text, latest_image_label
    )
