from datetime import datetime, timedelta, UTC
from flask import Flask, request, jsonify
from requests import get, HTTPError
from pandas import DataFrame
from werkzeug.exceptions import HTTPException


app = Flask(__name__)


def get_json(url: str, params: dict):
    # make GET request
    response = get(url=url, params=params)

    # raise HTTPError if response does not indicate success
    response.raise_for_status()

    return response.json()


def get_exception_response(message, code):
    return jsonify({'error': message, 'code': code}), code


@app.errorhandler(HTTPError)
def handle_exception(ex):
    return get_exception_response(ex.response.json()['reason'], ex.response.status_code)


@app.errorhandler(HTTPException)
def handle_exception(ex):
    return get_exception_response(ex.description, ex.code)


@app.errorhandler(Exception)
def handle_exception(ex):
    return get_exception_response(str(ex), 500)


@app.route('/countries/<string:country>/forecast')
def get_forecast(country: str):
    tomorrow = datetime.now(UTC) + timedelta(days=1)

    # get start and end forecast dates from query params
    args = request.args
    forecast_start = args.get('start', tomorrow)
    forecast_end = args.get('end', tomorrow)

    # get latitude and longitude by country name
    country_data_json = get_json(
        'https://geocoding-api.open-meteo.com/v1/search',
        {'name': country, 'count': 1})

    country_data = country_data_json['results'][0]
    latitude = country_data['latitude']
    longitude = country_data['longitude']

    history_start = forecast_start - timedelta(days=365)
    history_end = forecast_start - timedelta(days=1)

    # get weather data
    weather_data_json = get_json(
        'https://archive-api.open-meteo.com/v1/archive',
        {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': history_start.strftime('%Y-%m-%d'),
            'end_date': history_end.strftime('%Y-%m-%d'),
            'daily': ['temperature_2m_max', 'temperature_2m_min', 'temperature_2m_mean']
        })

    weather_data = weather_data_json['daily']

    return weather_data


if __name__ == '__main__':
    app.run(debug=True)
