from logging import basicConfig, DEBUG
from datetime import datetime, timedelta, UTC, date
from flask import Flask, request, jsonify
from requests import get, HTTPError
from werkzeug.exceptions import HTTPException
from pandas import DataFrame, to_datetime, date_range
from prophet import Prophet


def get_json(url: str, params: dict):
    """
    Makes a GET request to specified URL with query params,
    raises an exception if response does not indicate success
    or returns JSON content of response otherwise

    :param url: URL to make request to
    :param params: query parameters for request
    :return: JSON content of response
    :raises HTTPError: if response does not indicate success
    """

    response = get(url=url, params=params)
    response.raise_for_status()
    return response.json()


def to_date(date_string) -> date:
    """
    Parses string to date

    :param date_string: string to parse
    :return: parsed date
    """
    return datetime.strptime(date_string, "%Y-%m-%d").date()


def get_exception_response(message: str, code: str | int):
    """
    Returns response in case of exception

    :param message: error message
    :param code: response status code
    :return: response JSON content in format {'error': ..., 'code': ...} and status code
    """
    return jsonify({'error': message, 'code': code}), code


# flask app instance
app = Flask(__name__)

# number of days to take from history before forecast start date
history_days = 365 * 5

# minimum accessible date to get weather data from Open-Meteo
min_history_date = '1940-01-01'

# dictionary for converting Open-Meteo data series names to our API data series names
data_columns = {
    'temperature_2m_max': 'max_temperature',
    'temperature_2m_mean': 'mean_temperature',
    'temperature_2m_min': 'min_temperature',
    'wind_speed_10m_max': 'wind_speed'
}


@app.errorhandler(HTTPError)
def handle_exception(ex: HTTPError):
    """
    Handles HTTPError

    :param ex: exception of type HTTPError
    :return: exception response
    """
    return get_exception_response(ex.response.json()['reason'], ex.response.status_code)


@app.errorhandler(HTTPException)
def handle_exception(ex: HTTPException):
    """
    Handles HTTPException

    :param ex: exception of type HTTPException
    :return: exception response
    """
    return get_exception_response(ex.description, ex.code)


@app.errorhandler(Exception)
def handle_exception(ex: Exception):
    """
    Handles any Exception

    :param ex: any exception
    :return: exception response
    """
    return get_exception_response(str(ex), 500)


@app.route('/countries/<string:country>/forecast')
def get_forecast(country: str):
    """
    Creates weather forecast for given country on specified date range [start; end].\n
    Endpoint format: /countries/<country>/forecast?start=<start>&end=<end>\n
    Query parameters:
        - start (str, optional): forecast start date in format YYYY-MM-DD. Default is tomorrow date.
        - end (str, optional): forecast end date in format YYYY-MM-DD. Default is forecast start date.

    :param country: country name to create forecast for
    :return: JSON with weather history, forecast and true data.
        Example:
        {
            "max_temperature": {
                "history": [
                    { "date": ..., "value": ... }
                ],
                "forecast": [
                    { "date": ..., "value": ... }
                ],
                "true": [
                    { "date": ..., "value": ... }
                ]
            },
            "min_temperature": {
                "history": [
                    { "date": ..., "value": ... }
                ],
                "forecast": [
                    { "date": ..., "value": ... }
                ],
                "true": [
                    { "date": ..., "value": ... }
                ]
            }
        }
    """

    # get today and tomorrow dates
    today = datetime.now(UTC).date()
    tomorrow = today + timedelta(days=1)

    # get start and end forecast dates from query params or set them to tomorrow date by default
    forecast_start = request.args.get('start', tomorrow, type=to_date)
    forecast_end = request.args.get('end', forecast_start, type=to_date)

    # handle wrong input for forecast start and end dates
    if forecast_start > forecast_end:
        return 'Forecast start date must be less than or equal to forecast end date.', 404

    # get latitude and longitude by country name
    country_data_json = get_json(
        'https://geocoding-api.open-meteo.com/v1/search',
        {'name': country, 'count': 1})

    # get country latitude and longitude from response JSON
    country_data = country_data_json['results'][0]
    latitude = country_data['latitude']
    longitude = country_data['longitude']

    # get history weather data
    history_start = max(forecast_start - timedelta(days=history_days), to_date(min_history_date))
    history_end = min(forecast_end, today)

    # get history weather data
    weather_json = get_json(
        'https://archive-api.open-meteo.com/v1/archive',
        {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': history_start,
            'end_date': history_end,
            'daily': data_columns.keys()
        })

    # convert history weather data to DataFrame
    weather_df = DataFrame(weather_json['daily']).dropna()

    # convert time column to date type
    weather_df['time'] = to_datetime(weather_df['time']).dt.date

    # split weather DataFrame into history weather data and true weather data for forecasted dates (if any)
    history_weather_df = weather_df[weather_df['time'] < forecast_start]
    true_forecast_df = weather_df[weather_df['time'] >= forecast_start]

    # dictionary for response JSON
    result = {}

    # loop, which creates forecast for every weather data column
    for column in weather_df.columns.drop('time').values:
        # get time series and current weather data series
        input_dt = history_weather_df[['time', column]]

        # convert column names to ['ds', 'y'] (for Prophet fir function)
        input_dt.columns = ['ds', 'y']

        # create Prophet instance and fit data
        prophet = Prophet()
        prophet.fit(input_dt)

        # DataFrame of dates to create forecast for
        future = DataFrame(date_range(forecast_start, forecast_end), columns=['ds'])

        # predict weather data for forecast dates and set DataFrame columns to ['date', 'value']
        forecast_df = prophet.predict(future)[['ds', 'yhat']]
        forecast_df['ds'] = forecast_df['ds'].astype(str)
        forecast_df.columns = ['date', 'value']

        # get history weather data and set DataFrame columns to ['date', 'value']
        history_df = history_weather_df[['time', column]]
        history_df['time'] = history_df['time'].astype(str)
        history_df.columns = ['date', 'value']

        # get true weather data for forecasted dates and set DataFrame columns to ['date', 'value']
        true_df = true_forecast_df[['time', column]]
        true_df['time'] = true_df['time'].astype(str)
        true_df.columns = ['date', 'value']

        # add history, forecast and true weather data to response JSON
        data_column_name = data_columns[column]
        result[data_column_name] = {
            'history': history_df.to_dict('records'),
            'forecast': forecast_df.to_dict('records'),
            'true': true_df.to_dict('records')}

    # return response JSON
    return jsonify(result)


# run application
if __name__ == '__main__':
    basicConfig(level=DEBUG)
    app.run(debug=True)
