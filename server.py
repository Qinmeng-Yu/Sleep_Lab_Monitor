from datetime import datetime
from database_classes import Patient, CPAPdata
from pymodm import connect
from flask import Flask, request, jsonify
from validate import validate_input_data, validate_cpap_data
from pymodm import errors as pymodm_errors
import logging

app = Flask(__name__)


@app.route("/upload_patient", methods=["POST"])
def post_new_patient():
    # Get the data sent with the request
    in_data = request.get_json()
    # Validate the data received
    input_check = validate_input_data(in_data)
    if input_check is not True:
        return jsonify({"error": input_check}), 400

    # Implement the route
    try:
        add_patient_to_database(in_data)
    # Return a response
        return "Successfully added", 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 400


@app.route("/room/<int:room_number>/cpap_pressure", methods=["GET"])
def get_updated_cpap_pressure(room_number):
    try:
        patient = Patient.objects.raw({"room": room_number}).first()

        if not patient.data:
            return jsonify({
                "message": f"No CPAP data available for room {room_number}.",
                "cpap_pressure": None}), 200

        cpap_data = patient.data[-1]
        return jsonify({"cpap_pressure": cpap_data.cpap_pressure}), 200

    except pymodm_errors.DoesNotExist:
        # Room not found
        return jsonify(
            {"message": f"Do not exist room with given number {room_number}."
             }), 400


@app.route("/rooms", methods=["GET"])
def get_all_rooms():
    try:
        rooms = [patient.room for patient in Patient.objects.all()]
        return jsonify({"rooms": rooms}), 200
    except Exception as e:
        logging.error(f"Error fetching rooms: {str(e)}")
        return jsonify({"error": "Failed to fetch rooms"}), 500


@app.route("/room/<int:room_number>/patient_info", methods=["GET"])
def get_patient_info(room_number):
    try:
        patient = Patient.objects.raw({"room": room_number}).first()
        return jsonify({
            "name": patient.name,
            "mrn": patient.mrn
        }), 200
    except pymodm_errors.DoesNotExist:
        return jsonify(
            {"error": f"No patient found in room {room_number}"}), 404
    except Exception as e:
        logging.error(f"Error fetching patient info: {str(e)}")
        return jsonify({"error": "Failed to fetch patient info"}), 500


@app.route("/room/<int:room_number>/patient_data", methods=["GET"])
def get_latest_patient_data(room_number):
    try:
        patient = Patient.objects.raw({"room": room_number}).first()
        if not patient.data:
            return jsonify({"error": "No CPAP data available"}), 404

        latest_data = patient.data[-1]
        response = {
            "cpap_pressure": latest_data.cpap_pressure,
            "breathing_rate": latest_data.breathing_rate,
            "apnea_count": latest_data.apnea_count,
            "timestamp": latest_data.timestamp.isoformat(),
            "flow_image_base64": latest_data.flow_image_base64 or None
        }
        return jsonify(response), 200
    except pymodm_errors.DoesNotExist:
        return jsonify(
            {"error": f"No patient found in room {room_number}"}), 404
    except Exception as e:
        logging.error(f"Error fetching patient data: {str(e)}")
        return jsonify({"error": "Failed to fetch patient data"}), 500


@app.route("/room/<int:room_number>/timestamps", methods=["GET"])
def get_timestamps(room_number):
    try:
        patient = Patient.objects.raw({"room": room_number}).first()
        if not patient.data:
            return jsonify({"error": "No CPAP data available"}), 404

        timestamps = [entry.timestamp.isoformat() for entry in patient.data]
        return jsonify({"timestamps": timestamps}), 200
    except pymodm_errors.DoesNotExist:
        return jsonify(
            {"error": f"No patient found in room {room_number}"}), 404
    except Exception as e:
        logging.error(f"Error fetching timestamps: {str(e)}")
        return jsonify({"error": "Failed to fetch timestamps"}), 500


@app.route("/room/<int:room_number>/image/<timestamp>", methods=["GET"])
def get_cpap_image(room_number, timestamp):
    try:
        patient = Patient.objects.raw({"room": room_number}).first()
        for entry in patient.data:
            if entry.timestamp.isoformat() == timestamp:
                return jsonify(
                    {"flow_image_base64": entry.flow_image_base64}), 200

        return jsonify(
            {"error": "Image not found for the given timestamp"}), 404
    except pymodm_errors.DoesNotExist:
        return jsonify(
            {"error": f"No patient found in room {room_number}"}), 404
    except Exception as e:
        logging.error(f"Error fetching CPAP image: {str(e)}")
        return jsonify({"error": "Failed to fetch image"}), 500


@app.route("/room/<int:room_number>/update_cpap", methods=["POST"])
def update_cpap_pressure(room_number):
    in_data = request.get_json()
    if "cpap_pressure" not in in_data:
        return jsonify({"error": "CPAP pressure is required"}), 400

    cpap_check = validate_cpap_data(in_data["cpap_pressure"])
    if cpap_check is not True:
        return jsonify({"error": cpap_check}), 400

    try:
        patient = Patient.objects.raw({"room": room_number}).first()
        if not patient.data:
            return jsonify({"error": "No existing CPAP data to update"}), 404

        # Get the last entry in the 'data' list
        latest_entry = patient.data[-1]

        # Create a new CPAPdata object with updated cpap_pressure
        updated_entry = CPAPdata(
            cpap_pressure=in_data["cpap_pressure"],
            breathing_rate=latest_entry.breathing_rate,
            apnea_count=latest_entry.apnea_count,
            flow_image_base64=latest_entry.flow_image_base64,
            timestamp=datetime.now()
        )

        patient.data.append(updated_entry)
        patient.save()

        return jsonify(
            {"message": "CPAP pressure updated successfully"}), 200

    except pymodm_errors.DoesNotExist:
        return jsonify(
            {"error": f"No patient found in room {room_number}"}), 404
    except Exception as e:
        logging.error(f"Error updating CPAP pressure: {str(e)}")
        return jsonify({"error": "Failed to update CPAP pressure"}), 500


def add_patient_to_database(in_data):
    """
    Add or update a patient in the database.

    This function checks whether a patient with the given MRN already exists
    in the database. If such a patient exists, their data is updated with
    the provided details. If no matching MRN is found, a new patient entry
    is created. If the room is occupied by another patient, the old patient's
    data is removed to ensure room specificity.

    Args:
        in_data (dict): Patient data containing MRN, name, room number, and
        optionally CPAP-related data entries.

    Returns:
        Patient: The patient object that was updated or created.
    """
    try:
        # Check if the MRN already exists
        patient = Patient.objects.raw({"_id": in_data["mrn"]}).first()
        if "name" in in_data:
            patient.name = in_data["name"]

        if "data" in in_data and in_data["data"]:
            for entry in in_data["data"]:
                cpap_entry = create_cpap_entry(entry)
                patient.data.append(cpap_entry)
        patient.save()

    except pymodm_errors.DoesNotExist:
        # if mrn do not exist
        try:
            # check if room numbe exist
            existing_patient = Patient.objects.raw(
                {"room": in_data["room"]}).first()
            if existing_patient.mrn != in_data["mrn"]:
                # delete old patient data if room exist
                existing_patient.delete()
        except pymodm_errors.DoesNotExist:
            pass

        new_patient = create_new_patient(in_data)
        new_patient.save()
        return new_patient


def create_cpap_entry(entry):
    """
    Create a new CPAPdata object from the provided dictionary entry.

    This function validates the CPAP data fields within the provided
    dictionary entry, ensuring the CPAP pressure matches the data format.
    After validation, it creates a CPAPdata object containing relevant
    data, including breathing rate, apnea count, CPAP pressure, and a
    flow image encoded in base64 format. The current timestamp is
    automatically concatenated to the created CPAPdata object.

    Args:
        entry (dict): A dictionary containing fields such as CPAP pressure,
        breathing rate, apnea count, and a base64-encoded flow image.

    Returns:
        CPAPdata: A new CPAPdata object ready for storage in the database.
    """
    # Validate CPAP pressure
    cpap_check = validate_cpap_data(entry["cpap_pressure"])
    if cpap_check is not True:
        raise ValueError(cpap_check)

    timestamp = datetime.now()

    return CPAPdata(
        cpap_pressure=entry["cpap_pressure"],
        breathing_rate=entry["breathing_rate"],
        apnea_count=entry["apnea_count"],
        flow_image_base64=entry["flow_image_base64"],
        timestamp=timestamp
    )


def create_new_patient(in_data):
    """
    Create a new patient record based on the provided input data.

    This function generates a new patient entry in the database using the
    provided details. The patient record includes the MRN, room number, and
    optionally the patient’s name and associated CPAP data. Each CPAP entry is
    validated and converted into a CPAPdata object before being added to the
    patient's record.

    Args:
        in_data (dict): A dictionary containing fields for MRN, room number,
        and optionally patient name and CPAP data.

    Returns:
        Patient: The newly created patient object.
    """
    new_data = []
    if "data" in in_data and in_data["data"]:
        for entry in in_data["data"]:
            cpap_entry = create_cpap_entry(entry)
            new_data.append(cpap_entry)

    if "name" in in_data:
        patient = Patient(mrn=in_data["mrn"],
                          name=in_data["name"],
                          room=in_data["room"],
                          data=new_data)
    else:
        patient = Patient(mrn=in_data["mrn"],
                          room=in_data["room"],
                          data=new_data)
    patient.save()
    return patient


def populate_database():
    """
    Pre-populates the database with sample data for development purposes.

    This function creates initial patient records with sample data
    to facilitate development and testing. Each patient record contains
    an MRN, name, room number, and CPAP data entries. These entries include
    CPAP pressure, breathing rate, apnea count, and a base64-encoded flow
    image.

    Returns:
        None
    """
    add_patient_to_database({"mrn": 19203,
                             "name": "Claire Kim",
                             "room": 101,
                             "data": [
                                 {
                                    "cpap_pressure": 12,
                                    "breathing_rate": 17,
                                    "apnea_count": 4,
                                    "flow_image_base64": "iVBORw0KGgo",
                                    "timestamp": "2024-11-23 12:00:00"
                                    }
                                    ]})
    add_patient_to_database({"mrn": 1878,
                             "name": "Qinmeng Yu",
                             "room": 102})


def initialize_server():
    """
    Initialize the Flask server and MongoDB connection.

    Configures logging for the application and establishes a connection
    to the MongoDB database. The connection string is specific to the
    MongoDB Atlas cluster being used and includes parameters for
    authentication and secure communication.

    Returns:
        None
    """
    logging.basicConfig(filename="server.log", filemode='w',
                        level=logging.DEBUG)
    logging.info("Started server")
    connect("mongodb+srv://hj00claire:R4hP7HZhbgHBzelm@sleeplab.jr91q."
            "mongodb.net/patient_server?retryWrites=true&w="
            "majority&appName=sleeplab", tlsAllowInvalidCertificates=True)


if __name__ == "__main__":
    initialize_server()
    populate_database()
    app.run(debug=True)
