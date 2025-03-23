import requests

server = "http://127.0.0.1:5000"

# 1. "/upload_patient"
out_json = {
    "mrn": 456,
    "room": 103,
    "name": "Bob Smith",
    "data": [
        {
            "cpap_pressure": 14,
            "breathing_rate": 20.0,
            "apnea_count": 1,
            "flow_image_base64": "example_base64_string2"
        }
    ]
}

r = requests.post(server + "/upload_patient", json=out_json)
print("Status Code:", r.status_code)
print("Response Text:", r.text)


# 2. "/room/<int:room_number>/cpap_pressure"
r = requests.get(server + "/room/102/cpap_pressure")
print("Status Code:", r.status_code)
print("the updated cpap pressure is", r.text)
