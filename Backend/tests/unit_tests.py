import unittest
from parameterized import parameterized
from unittest.mock import patch
from datetime import date

from Backend.app.main import to_date, app


class TestFlaskApp(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def tearDown(self):
        pass

    @parameterized.expand([
        ('2022-01-01', date(2022, 1, 1)),
        ('1964-06-28', date(1964, 6, 28)),
        ('2000-1-1', date(2000, 1, 1)),
        ('2204-12-15', date(2204, 12, 15)),
    ])
    def test_to_date(self, test_str, actual_date):
        result = to_date(test_str)
        self.assertEqual(result, actual_date)

    @patch('Backend.app.main.get_json', side_effect=lambda url, params: {
        'https://geocoding-api.open-meteo.com/v1/search':
            {
                'results': [{'latitude': 10, 'longitude': 20}]
            },
        'https://archive-api.open-meteo.com/v1/archive':
            {
                'daily': {
                    'time': ['2020-01-01', '2020-01-02', '2020-01-03', '2020-01-04', '2020-01-05'],
                    'temperature_2m_min': [10, 20, 30, 20, 20]
                }
            },
    }[url])
    def test_get_forecast(self, get_json_mock):
        response = self.client.get('/countries/Ukraine/forecast?start=2020-01-04&end=2020-01-05')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['min_temperature']['true']), 2)
        self.assertEqual(len(response.json()['min_temperature']['forecast']), 2)
        self.assertEqual(len(response.json()['min_temperature']['history']), 3)


if __name__ == '__main__':
    unittest.main()
