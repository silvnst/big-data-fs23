import requests
import numpy as np
import pandas as pd
import os
import datetime

api_key = 'd411180a4e37b77f964bb060ffdc739b' #openweathermap api key

def create_weather(city, date):
    #load coordinates from excel file
    read_coordinates = pd.read_excel('Daten/koordinaten.xlsx')
    #get coordinates for train station
    read_coordinates = read_coordinates[read_coordinates['Bahnhof'] == city]
    #get latitude and longitude
    lat = read_coordinates['latitude'].values[0]
    lon = read_coordinates['longitude'].values[0]
    #get weather data
    url = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&cnt=40'
    response = requests.get(url)
    response_json = response.json()
    target_date = round_time_to_3h(date)  # round to the next possible point in intervals of 3 hours
    target_date = target_date.strftime("%Y-%m-%d %H:%M:%S")
    # get the data for the target date
    target_data = [data for data in response_json['list'] if data['dt_txt'].startswith(target_date)]
    Temperatur = target_data[0]['main']['temp'] - 273.15
    Wind= target_data[0]['wind']['speed']
    Niederschlag = target_data[0]['rain']['3h'] if 'rain' in target_data[0] else 0
    Luftfeuchtigkeit = target_data[0]['main']['humidity']
    Schnee = target_data[0]['snow']['3h'] if 'snow' in target_data[0] else 0
    return Temperatur, Niederschlag, Luftfeuchtigkeit, Schnee, Wind


def round_time_to_3h(dt=None):
    #Round a datetime object to the next possible point in intervals of 3 hours
    if dt is None:
        dt = datetime.datetime.now()
    if dt.hour < 3:
        return datetime.datetime(dt.year, dt.month, dt.day, 3, 0, 0)
    elif dt.hour < 6:
        return datetime.datetime(dt.year, dt.month, dt.day, 6, 0, 0)
    elif dt.hour < 9:
        return datetime.datetime(dt.year, dt.month, dt.day, 9, 0, 0)
    elif dt.hour < 12:
        return datetime.datetime(dt.year, dt.month, dt.day, 12, 0, 0)
    elif dt.hour < 15:
        return datetime.datetime(dt.year, dt.month, dt.day, 15, 0, 0)
    elif dt.hour < 18:
        return datetime.datetime(dt.year, dt.month, dt.day, 18, 0, 0)
    elif dt.hour < 21:
        return datetime.datetime(dt.year, dt.month, dt.day, 21, 0, 0)
    else:
        next_day = dt + datetime.timedelta(days=1)
        return datetime.datetime(next_day.year, next_day.month, next_day.day, 0, 0, 0)

