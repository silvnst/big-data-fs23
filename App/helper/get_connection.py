
import requests
import xml.etree.ElementTree as ET
import datetime as dt

def get_connection(departure_station, departure_station_name, arrival_station, arrival_station_name, dept_time, linien):
    # Encode the station names
    departure_station_name = departure_station_name.encode('utf-8')
    arrival_station_name = arrival_station_name.encode('utf-8')
    # Get the current time
    now_time = dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S%Z')
    # Define the XML payload
    xml_payload = '''<?xml version="1.0" encoding="utf-8"?>
    <OJP xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.siri.org.uk/siri" version="1.0" xmlns:ojp="http://www.vdv.de/ojp" xsi:schemaLocation="http://www.siri.org.uk/siri ../ojp-xsd-v1.0/OJP.xsd">
        <OJPRequest>
            <ServiceRequest>
                <RequestTimestamp>{now_time}</RequestTimestamp>
                <RequestorRef>API-Explorer</RequestorRef>
                <ojp:OJPTripRequest>
                    <RequestTimestamp>{now_time}</RequestTimestamp>
                    <ojp:Origin>
                        <ojp:PlaceRef>
                            <ojp:StopPlaceRef>{departure_station}</ojp:StopPlaceRef>
                            <ojp:LocationName>
                                <ojp:Text>{departure_station_name}</ojp:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                        <ojp:DepArrTime>{dept_time}</ojp:DepArrTime>
                    </ojp:Origin>
                    <ojp:Destination>
                        <ojp:PlaceRef>
                            <ojp:StopPlaceRef>{arrival_station}</ojp:StopPlaceRef>
                            <ojp:LocationName>
                                <ojp:Text>{arrival_station_name}</ojp:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                    </ojp:Destination>
                    <ojp:Params>
                        <ojp:IncludeTrackSections>true</ojp:IncludeTrackSections>
                        <ojp:IncludeTurnDescription></ojp:IncludeTurnDescription>
                        <ojp:IncludeIntermediateStops>false</ojp:IncludeIntermediateStops>
                    </ojp:Params>
                </ojp:OJPTripRequest>
            </ServiceRequest>
        </OJPRequest>
    </OJP>'''.format(departure_station=departure_station, now_time=now_time, dept_time=dept_time, departure_station_name=departure_station_name,
                     arrival_station=arrival_station, arrival_station_name=arrival_station_name)

    # Set the request URL
    url = 'https://api.opentransportdata.swiss/ojp2020'

    # Set the headers and content type for the request
    headers = {
        'Content-Type': 'application/xml',
        'Authorization': 'eyJvcmciOiI2NDA2NTFhNTIyZmEwNTAwMDEyOWJiZTEiLCJpZCI6IjRhM2I5MGUyZGRmYjRiZDI5NzdlNGJhNTBjNDAwNTE1IiwiaCI6Im11cm11cjEyOCJ9',
        'encoding': 'utf-8'
    }

    response = requests.post(url, headers=headers, data=xml_payload)
    
    # Parse the XML response
    root = ET.fromstring(response.content)
    result_elements = root.findall('.//{http://www.vdv.de/ojp}TripResult')
    
    # Find the TripId element
    departure_list = []
    arrival_list = []
    duration_list = []
    line_id_list = []
    line_text_list = []
    prediction_available_list = []
    for result_element in result_elements:
        # Set the default value for the prediction available
        prediction_available = 0

        # Find the ResultId element
        result_id_element = result_element.find('.//{http://www.vdv.de/ojp}ResultId')
        
        # Find the elements in the ResultId element
        trip_id_element = result_element.find('.//{http://www.vdv.de/ojp}TripId')
        line_id = result_element.find('.//{http://www.vdv.de/ojp}JourneyRef')
        line_id = line_id.text.strip()
        line_id = line_id.split(':')
        line_id = line_id[-1]
        # Find the line text
        line_text = result_element.find('.//{http://www.vdv.de/ojp}PublishedLineName')
        line_text = ET.tostring(line_text, method='text').decode()
        # Find the departure and arrival time
        departure = result_element.find('.//{http://www.vdv.de/ojp}StartTime')
        departure = departure.text
        arrival = result_element.find('.//{http://www.vdv.de/ojp}EndTime')
        arrival = arrival.text
        # Find the duration
        duration = result_element.find('.//{http://www.vdv.de/ojp}Duration')
        duration = duration.text
        # Append the values to the lists
        departure_list.append(departure)
        arrival_list.append(arrival)
        duration_list.append(duration)
        line_id_list.append(line_id)
        line_text_list.append(line_text)
        # Check if the line is in the list of lines
        if line_text in linien:
            prediction_available = 1
            prediction_available_list.append(prediction_available)
        else:
            prediction_available_list.append(prediction_available)
    
    return departure_list, arrival_list, duration_list, line_id_list, prediction_available_list, line_text_list