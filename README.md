# Final Project

**Author:** Qinmeng Yu, HyoJoo Kim

## Team Members

**Qinmeng Yu**: Responsible for the **Patient-Side GUI Client** implementation.

**HyoJoo Kim**: Focused on the **Monitoring-Station GUI Client** development and database integration.

## Project Purpose

This repository contains the code for Sleep Lab Monitoring System, where **the Sleep Lab Monitoring System** is designed to simulate a real-world environment in a sleep lab, enabling effective patient monitoring and data management. The system consists of:

1. **Patient-Side Client**: Simulates a CPAP machine for tracking patients undergoing sleep studies.
2. **Monitoring-Station Client**: Acts as a central hub for monitoring all patients in the lab.
3. **Cloud Server**: Stores patient data, provides RESTful API routes, and facilitates communication between clients.

## Demo Video

https://duke.box.com/s/dif4o6rklr8mw129hbtb44hqjg9n6t39


## Database 

The system uses **MongoDB** for data storage and management. See *database_classes.py* for more detail. The database contains collections for:

- **Patients**: Stores patient information, CPAP pressure data, and calculated data.

- **Schema:**

  ```python
  {
   "mrn": <int>,
   "room": <int>,
   "name": <optional str>,
   "cpap_pressure": <optional int>,
   "data": [
    {
     "timestamp": <ISO-8601>,
     "cpap_pressure": <int>,
     "breathing_rate": <float>,
     "apnea_count": <int>,
     "flow_image_base64": <str>
    }
   ]
  }
  ```

## Patient-Side GUI Client

1. Launch the Application:

   Open the GUI by running the script:

   ``` python patient_interface.py ```

2. Entry filling:

   Fill in room number, medical record number, name(optional), cpap pressure( (between 4 and 25).

3. CPAP Data analysis(optional):

   Click **Select Cpap Data File** button to select a .txt cpap data file to analysis. Click yes when the message box jumps out asking whether **Are you sure you want to select cpap data file for analysis?**. After selection, Calculated calculate data(breath rate, apnea count and flow image) will show up on the right frame. f the number of apnea events is two or greater, that value will be displayed in red.

4. Upload Patient Data:

   Click Upload button to upload whatever information is entered above. The mrn and room number are required for uploading. If both a CPAP pressure and CPAP calculated data have been entered, CPAP pressure, breathing rate, apnea count, and CPAP flow image along with mrn, room number and name(if enter) will be uploaded.

5. Update Information:

   After first upload, patient can update their name, cpap pressure and select a new file to analysis. MRN and room number can not be changed.

6. Reset:

   Reset all the fields back to the begginning. 

7. Periodic Updates:

   The application will automatically update patient cpap data every 30 seconds upon monitoring-side update.

## Monitoring-Side GUI Client
### How To Use

1. Launch the Application:

   Open the GUI by running the script:

   ``` python monitoring_interface.py ```

2.  Room Selection:

    Select a room number from the dropdown menu to view patient data.

3. View Patient Data:

   The latest CPAP data, including pressure, breathing rate, and apnea count, is displayed. When apnea count is **two or more**, the number is highlighted in red.

4. View Flow Images:

   The latest CPAP flow image is displayed along with a timestamp.

5. View Historical Flow Images:

   Select a specific timestamp from the dropdown to view historical flow images.

6. Download Images:

   Download the latest or selected flow image using the respective buttons, if needed.

7. Update CPAP Pressure:


   Enter a new CPAP pressure value (between 4 and 25) and click the "Update" button to save the changes.

8. Periodic Updates:

   The application will automatically update patient data every 30 seconds.

## Cloud Server - API Reference Guide

### >> Patient-Side Routes

#### 1. Add New Patient

   - **URL**: `/upload_patient`
   - **Method**: `POST`
   - **Description**: Adds a new patient or updates an existing patient's details.
   - **Response**:
     - `200 OK`: Patient added successfully.
     - `400 Bad Request`: Validation error or invalid input.

#### 2. Update CPAP Pressure
   - **URL**: `/room/<int:room_number>/update_cpap`
   - **Method**: `POST`
   - **Description**: Updates the CPAP pressure for a specific room.
   - **Request Body**:
     ```json
     {
       "cpap_pressure": 15
     }
     ```
   - **Response**:
     - `200 OK`: Pressure updated successfully.
     - `400 Bad Request`: Validation error or missing field.
     - `404 Not Found`: Room or patient not found.

### >> Monitoring-Side Routes

#### 1. Get Updated CPAP Pressure
   - **URL**: `/room/<int:room_number>/cpap_pressure`
   - **Method**: `GET`
   - **Description**: Gets the latest CPAP pressure for a specific room.
   - **Response**:
     ```json
     {
       "cpap_pressure": 12
     }
     ```
     - `200 OK`: Pressure retrieved successfully.
     - `400 Bad Request`: Room not found.

#### 2. Get All Room Numbers
   - **URL**: `/rooms`
   - **Method**: `GET`
   - **Description**: Lists all room numbers with registered patients.
   - **Response**:
     ```json
     {
       "rooms": [101, 102, 103]
     }
     ```
     - `200 OK`: Rooms retrieved successfully.
     - `500 Internal Server Error`: Failed to fetch rooms.

#### 3. Get Patient Info
   - **URL**: `/room/<int:room_number>/patient_info`
   - **Method**: `GET`
   - **Description**: Gets patient information for a specific room.
   - **Response**:
     ```json
     {
       "name": "John Doe",
       "mrn": 12345
     }
     ```
     - `200 OK`: Patient info retrieved.
     - `404 Not Found`: Patient not found in the room.
     - `500 Internal Server Error`: Failed to fetch patient info.

#### 4. Get Latest Patient Data
   - **URL**: `/room/<int:room_number>/patient_data`
   - **Method**: `GET`
   - **Description**: Gets the latest CPAP data for a specific room.
   - **Response**:
     ```json
     {
       "cpap_pressure": 12,
       "breathing_rate": 18,
       "apnea_count": 3,
       "timestamp": "2024-11-23T12:00:00",
       "flow_image_base64": "base64_encoded_string"
     }
     ```
     - `200 OK`: Data retrieved successfully.
     - `404 Not Found`: No data available or patient not found.

#### 5. Get Available Timestamps
   - **URL**: `/room/<int:room_number>/timestamps`
   - **Method**: `GET`
   - **Description**: Gets all available timestamps for CPAP data in a specific room.
   - **Response**:
     ```json
     {
       "timestamps": ["2024-11-23T12:00:00", "2024-11-24T08:00:00"]
     }
     ```
     - `200 OK`: Timestamps retrieved.
     - `404 Not Found`: No data or patient not found.

#### 6. Get CPAP Image
   - **URL**: `/room/<int:room_number>/image/<timestamp>`
   - **Method**: `GET`
   - **Description**: Gets a flow image for a specific timestamp in a room.
   - **Response**:
     ```json
     {
       "flow_image_base64": "base64_encoded_string"
     }
     ```
     - `200 OK`: Image retrieved.
     - `404 Not Found`: Image or patient not found.

### Initialization and Pre-population
---------------------------------
- **DB Connection**: MongoDB Atlas
- **Pre-populated Data**: The database is populated with sample patients using `populate_database()` for development and testing.

### Notes
-----
- Timestamps are formatted in ISO 8601 (`YYYY-MM-DDTHH:MM:SS`).
- CPAP pressure must be an integer between 4 and 25.
- Images are encoded in Base64 format.

### Virtual Machine

-----

VCM URL: "http://vcm-43744.vm.duke.edu:5001"
