import pytest
from server import app
from database_classes import Patient, CPAPdata
from pymodm import errors as pymodm_errors
# from datetime import datetimes

from server import initialize_server
initialize_server()

client = app.test_client()


# @pytest.fixture(autouse=True)
# def clear_database():
#     """Clear the database before and after each test."""
#     Patient.objects.all().delete()
#     yield
#     Patient.objects.all().delete()


def test_create_new_patient():
    from server import create_new_patient
    in_data = {"mrn": 19213,
               "name": "Claire Kim",
               "room": 103,
               "data": [{
                        "cpap_pressure": 12,
                        "breathing_rate": 17,
                        "apnea_count": 4,
                        "flow_image_base64": "iVBORw0KGgo"
                        }]}
    in_data_wo_name = {"mrn": 193,
                       "room": 11,
                       "data": []}
    create_new_patient(in_data)
    create_new_patient(in_data_wo_name)
    answer = Patient.objects.raw({"_id": 19213}).first()
    answer_wo_name = Patient.objects.raw({"_id": 193}).first()
    answer.delete()
    answer_wo_name.delete()
    assert answer.name == "Claire Kim"
    assert answer.room == 103
    assert answer.data[0].apnea_count == 4
    assert answer.data[0].cpap_pressure == 12
    assert answer.data[0].breathing_rate == 17
    assert answer.data[0].flow_image_base64 == "iVBORw0KGgo"
    assert answer_wo_name.room == 11
    assert answer_wo_name.data == []


def test_create_cpap_entry_valid():
    from server import create_cpap_entry
    valid_entry = {
        "cpap_pressure": 12,
        "breathing_rate": 17,
        "apnea_count": 4,
        "flow_image_base64": "iVBORw0KGgo"}

    valid_answer = create_cpap_entry(valid_entry)
    assert isinstance(valid_answer, CPAPdata)
    assert valid_answer.cpap_pressure == valid_entry["cpap_pressure"]
    assert valid_answer.breathing_rate == valid_entry["breathing_rate"]
    assert valid_answer.apnea_count == valid_entry["apnea_count"]
    assert valid_answer.flow_image_base64 == valid_entry["flow_image_base64"]


def test_create_cpap_entry_invalid():
    from server import create_cpap_entry
    invalid_entry = {
        "cpap_pressure": 30,
        "breathing_rate": 17,
        "apnea_count": 4,
        "flow_image_base64": "iVBORw0KGgo"}
    with pytest.raises(
        ValueError,
         match="CPAP value out of range. Must be between 4 and 25 inclusive."):
        create_cpap_entry(invalid_entry)


def test_add_patient_to_database():
    from server import add_patient_to_database
    # create new patient
    in_data = {"mrn": 123,
               "name": "David",
               "room": 7,
               "data": [{
                        "cpap_pressure": 12,
                        "breathing_rate": 17,
                        "apnea_count": 4,
                        "flow_image_base64": "iVBORw0KGgo"
                        }]}
    add_patient_to_database(in_data)
    answer = Patient.objects.raw({"_id": 123}).first()
    assert answer.name == "David"
    assert answer.room == 7
    assert answer.data[0].apnea_count == 4

    # patient with same mrn(update name and append data)
    in_data_same_mrn = {"mrn": 123,
                        "room": 7,
                        "name": "Sofia",
                        "data": [{
                            "cpap_pressure": 13,
                            "breathing_rate": 18,
                            "apnea_count": 1,
                            "flow_image_base64": "iVBORw0KGgo"
                        }]}
    add_patient_to_database(in_data_same_mrn)
    answer_upd = Patient.objects.raw({"_id": 123}).first()
    assert answer_upd.name == "Sofia"
    assert len(answer_upd.data) == 2
    assert answer_upd.data[0].apnea_count == 4
    assert answer_upd.data[1].apnea_count == 1

    # patient with same room but different mrn
    in_data_same_room = {"mrn": 13,
                         "room": 7,
                         "name": "Chloe",
                         "data": []}
    add_patient_to_database(in_data_same_room)

    with pytest.raises(pymodm_errors.DoesNotExist):
        Patient.objects.raw({"_id": 123}).first()

    answer_upd_patient = Patient.objects.raw({"_id": 13}).first()
    answer_upd_patient.delete()
    assert answer_upd_patient.name == "Chloe"
    assert answer_upd_patient.room == 7
    assert answer_upd_patient.data == []
