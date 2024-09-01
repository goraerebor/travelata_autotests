from email.header import Header

import requests
import pytest
import re
from config import HEADERS, PARAMS

def base_url():
    return 'https://api-gateway.travelata.ru/frontend/tours'
def response_data():
    try:
        response = requests.get(base_url(), headers=HEADERS, params=PARAMS)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        pytest.fail(f"HTTP запрос не выполнен: {e}")


def test_connect():
    response = response_data()
    assert response.status_code == 200

def test_body():
    response = response_data()
    json_response = response.json()

    assert json_response.get('success') == True
    assert 'result' in json_response and json_response['result'] is not None


def test_result_tours():
    response = response_data()
    json_response = response.json()

    tours = json_response['result']['tours']
    for tour in tours:
        assert 'id' in tour and tour['id'] is not None
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        assert 'checkInDate' in tour and re.match(date_pattern, tour['checkInDate'])
        assert 'price' in tour and tour['price'] > 0
        assert 'nights' in tour
        assert 'tour' in tour['nights'] and tour['nights']['tour'] > 0
        assert 'hotel' in tour['nights'] and tour['nights']['hotel'] > 0
        assert 'touristGroup' in tour and tour['touristGroup'] is not None
        assert 'adults' in tour['touristGroup']
        assert 'kids' in tour['touristGroup'] and tour['touristGroup']['kids'] >= 0
        assert 'infants' in tour['touristGroup']
        assert 'kidsAges' in tour['touristGroup'] and tour['touristGroup']['kidsAges']


def test_result_distance():
    response = response_data()
    json_response = response.json()

    tours = json_response['result']['tours']
    for tour in tours:
        assert 'meal' in tour
        assert 'departureCity' in tour and tour['departureCity'] == 2
        assert 'country' in tour and tour['country'] == 92
        assert 'resort' in tour
        assert 'hotel' in tour
        assert 'hotelAvailable' in tour
        assert 'hotelCategory' in tour
        assert 'room' in tour and tour['room'] is not None
        assert 'transfer' in tour
        assert 'flightType' in tour
        assert 'medicalInsurance' in tour and tour['medicalInsurance'] == True or False