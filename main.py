import json
import threading

import PySimpleGUI as sg
import requests

API_KEY = 'uZksJEteGGDbevCRL0xGU6Nu9aYGlrrB'
API_AUTOCOMPLETE_URL = 'http://dataservice.accuweather.com/locations/v1/cities/autocomplete?apikey={0}&q={1}'
API_WEATHER_URL = 'http://dataservice.accuweather.com/currentconditions/v1/{0}?apikey={1}'
API_FORECAST_URL = 'http://dataservice.accuweather.com/forecasts/v1/daily/5day/{0}?apikey={1}&metric=true'
API_UV_INDEX_URL = 'http://dataservice.accuweather.com/indices/v1/daily/1day/{0}/-15?apikey={1}'
API_12HR_FORECAST_URL = 'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{0}?apikey={1}&metric=true'
API_HISTORICAL_URL = 'http://dataservice.accuweather.com/currentconditions/v1/{0}/historical?apikey={1}'


def fetch_places(query):
    url = API_AUTOCOMPLETE_URL.format(API_KEY, query)
    r = requests.get(url)
    return json.loads(r.text)


def fetch_weather_data(location_key):
    url = API_WEATHER_URL.format(location_key, API_KEY)
    r = requests.get(url)
    return json.loads(r.text)


def fetch_weather_forecast(location_key):
    url = API_FORECAST_URL.format(location_key, API_KEY)
    r = requests.get(url)
    return json.loads(r.text)


def fetch_uv(location_key):
    url = API_UV_INDEX_URL.format(location_key, API_KEY)
    r = requests.get(url)
    return json.loads(r.text)


def fetch_12hr_forecast(location_key):
    url = API_12HR_FORECAST_URL.format(location_key, API_KEY)
    r = requests.get(url)
    return json.loads(r.text)


def fetch_historical_data(location_key):
    url = API_HISTORICAL_URL.format(location_key, API_KEY)
    r = requests.get(url)
    return json.loads(r.text)


place_to_key = {}
layout = [
    [sg.Text("Place:"), sg.Input(key='-PLACE-', enable_events=True, size=(35, 1))],
    [sg.Listbox(values=[], key='-PLACES-', size=(40, 5), enable_events=True, visible=False)],
    [sg.Text("", key='-WEATHER-', size=(40, 2))],
    [sg.Text("", key='-FORECAST-', size=(40, 6))],
    [sg.Text("", key='-UV-', size=(40, 1))],
    [sg.Text("", key='-12HR_FORECAST-', size=(40, 13))],
    [sg.Text("", key='-HISTORICAL-', size=(40, 8))],
    [sg.Button("Clear"), sg.Button("Close")]
]

window = sg.Window("AccuWeather", layout)
debounce_timer = None
debounce_time = 0.3

while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, "Close"):
        break

    if event == '-PLACE-':
        query = values['-PLACE-']
        if debounce_timer:
            debounce_timer.cancel()
        if len(query) > 2:
            debounce_timer = threading.Timer(debounce_time, lambda: window.write_event_value('-FETCH-', query))
            debounce_timer.start()
        else:
            window['-PLACES-'].update(visible=False)

    if event == '-FETCH-':
        query = values['-FETCH-']
        places = fetch_places(query)
        place_list = []
        for place in places:
            place_str = f"{place['LocalizedName']}, {place['Country']['LocalizedName']}, {place['AdministrativeArea']['LocalizedName']}"
            place_list.append(place_str)
            place_to_key[place_str] = place['Key']
        window['-PLACES-'].update(values=place_list)
        window['-PLACES-'].update(visible=True)

    if event == '-PLACES-':
        selected = values['-PLACES-'][0]
        location_key = place_to_key.get(selected)
        if location_key:
            window['-PLACE-'].update(value=selected)
            window['-PLACES-'].update(visible=False)
            weather_data = fetch_weather_data(location_key)
            weather_text = f"Weather: {weather_data[0]['WeatherText']}\nTemperature: {weather_data[0]['Temperature']['Metric']['Value']}°C"
            window['-WEATHER-'].update(weather_text)

            forecast_data = fetch_weather_forecast(location_key)
            forecast_text = "5-day Forecast:\n"
            for day in forecast_data['DailyForecasts']:
                date = day['Date'][:10]
                min_temp = day['Temperature']['Minimum']['Value']
                max_temp = day['Temperature']['Maximum']['Value']
                forecast_text += f"{date}: {min_temp}°C - {max_temp}°C\n"
            window['-FORECAST-'].update(forecast_text)
            uv_data = fetch_uv(location_key)
            indices_text = f"UV Index: {uv_data[0]['Category']}"
            window['-UV-'].update(indices_text)

            forecast_12hr_data = fetch_12hr_forecast(location_key)
            if forecast_12hr_data:
                forecast_12hr_text = "12-hour Forecast:\n"
                for hour in forecast_12hr_data:
                    time = hour['DateTime'][-14:-9]
                    temp = hour['Temperature']['Value']
                    forecast_12hr_text += f"{time}: {temp}°C\n"
                window['-12HR_FORECAST-'].update(forecast_12hr_text)

            historical_data = fetch_historical_data(location_key)
            historical_text = "Historical Data:\n"
            for record in historical_data:
                date_time = record['LocalObservationDateTime'][:16]
                temp = record['Temperature']['Metric']['Value']
                historical_text += f"{date_time}: {temp}°C\n"
            window['-HISTORICAL-'].update(historical_text)

    if event == "Clear":
        window['-PLACE-'].update(value='')
        window['-PLACES-'].update(values=[], visible=False)
        window['-WEATHER-'].update('')
        window['-UV-'].update('')
        window['-FORECAST-'].update('')
        window['-12HR_FORECAST-'].update('')
        window['-HISTORICAL-'].update('')

window.close()
