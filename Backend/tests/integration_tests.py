import unittest
from Backend.app.main import app, get_json, data_columns, to_date


class TestFlaskApp(unittest.TestCase):

    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()

    def tearDown(self):
        self.ctx.pop()

    def test_get_json_geocoding(self):
        json = get_json('https://geocoding-api.open-meteo.com/v1/search',
                            {'name': 'Ukraine', 'count': 1})

        self.assertEqual(len(json['results']), 1)

    def test_get_json_weather_data(self):
        start_date = '2020-01-01'
        end_date = '2020-02-01'
        json = get_json(
            'https://archive-api.open-meteo.com/v1/archive',
            {
                'latitude': 40.7128,
                'longitude': -74.0060,
                'start_date': start_date,
                'end_date': end_date,
                'daily': data_columns.keys()
            })

        self.assertEqual(len(json['daily']), len(data_columns.keys()) + 1)
        for data in json['daily']:
            self.assertEqual(len(json['daily'][data]), (to_date(end_date) - to_date(start_date)).days + 1)

    def test_get_forecast_success(self):
        response = self.client.get('/countries/Ukraine/forecast')
        self.assertEqual(response.status_code, 200)

    def test_get_forecast_fail(self):
        response = self.client.get('/countries/UnexistCountry/forecast')
        self.assertNotEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
