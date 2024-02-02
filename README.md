# WeatherForecastService

This service provides well-documented backend API and user-friendly frontend web UI
to allow anyone get temperature forecast for needed dates in the future or past.

## Backend

This is a simple Flask API for obtaining weather forecasts based on historical weather data.
The API utilizes the Open-Meteo service for geocoding and retrieving weather data.
It also uses Prophet library for creating forecasts.

### Usage

Inside Backend/app directory run the following command to load all needed packages: 
```
pip install -r requirements.txt
```

You can run API locally using either Python or Docker:

- Just Python:

    Run the following command in Backend/app directory:
    ```
    python main.py
    ```

- Docker:

    Run the following commands in Backend/app directory:
    ```
    docker build -t weather-forecast-service-image .
    docker run -dp 5000:5000 weather-forecast-service-image
    ```

### Access
API will run on port 5000 locally.

#### Endpoint

```
/countries/{country}/forecast?start={start}&end={end}
```

Route parameters:
- country: country name, for which forecast is required.

Query parameters:
- start (optional): Forecast start date in the format YYYY-MM-DD. Default is tomorrow's date.
- end (optional): Forecast end date in the format YYYY-MM-DD. Default is the same as the forecast start date.

Example API call:
```
http://localhost:5000/countries/Ukraine/forecast?start=2024-02-01&end=2024-02-10
```

#### Response Format

The response will be a JSON object containing weather history, forecast, and true data for each weather parameter.
- **'history'** array shows history weather data, which was used for forecasting model;
- **'forecast'** array shows predicted weather data for specified dates;
- **'true'** array shows actual weather data for forecast days.
Note: this array may be empty if dates for prediction don't have history weather data
(i.e. if forecast dates are in the future or Open-Meteo service don't yet have history weather data for specified dates). 

Example response format:
```
{
    "max_temperature": {
        "history": [
            { "date": "2024-01-01", "value": 25.0 },
            { "date": "2024-01-02", "value": 26.5 }
        ],
        "forecast": [
            { "date": "2024-02-01", "value": 28.3 },
            { "date": "2024-02-02", "value": 29.1 }
        ],
        "true": [
            { "date": "2024-02-01", "value": 28.0 },
            { "date": "2024-02-02", "value": 29.5 }
        ]
    },
    "min_temperature": {
        "history": [
            { "date": "2024-01-01", "value": 15.0 },
            { "date": "2024-01-02", "value": 16.5 }
        ],
        "forecast": [
            { "date": "2024-02-01", "value": 18.3 },
            { "date": "2024-02-02", "value": 19.1 }
        ],
        "true": [
            { "date": "2024-02-01", "value": 18.0 },
            { "date": "2024-02-02", "value": 19.5 }
        ]
    }
}
```

#### Error handling

In case of an error, the API will respond with a JSON object containing an error message and status code.
```
{
    "error": "Forecast start date must be less than or equal to forecast end date.",
    "code": 404
}
```

### Notes

- API supports retrieving weather data for any location that Open-Meteo geocoder knows.
So, you can request weather data not only for any country, but also for any location you'd like.
Visit Open-Meteo API docs if you want to know more: https://open-meteo.com/en/docs/geocoding-api/.
- API automatically takes history data from 5 years interval just before start forecast date.
This interval was chosen as a compromise between data size and prediction accuracy.
- It was checked, that for non-anomaly past years computed temperature forecast will have error **less than one degree Celsius**.
- Open-Meteo has a latency 2-5 days for weather data.
So, if you requested forecast for future dates, there may be missing a couple of last dates in weather history.

## Frontend

### Usage

Inside Frontend directory run the following command to load flask package:
```
pip install Flask
```

Run the following command in Frontend directory:
```
python main.py
```

### Access

Frontend will run on port 5001 locally.

To access it, open http://localhost:5001/ in your browser, and you'll see a UI where you can input country name and choose forecast dates.
After pressing Forecast button you will be redirected to /graphic page, where plot of predicted min/mean/max temperatures for specified dates will be shown.

## Unit and Integration test

In Backend/tests directory run
```
python unit_tests.py
```
to run unit tests or
```
python integration_tests.py
```
to run integration tests.

Don't forget to install all needed packages (refer to Backend section).
