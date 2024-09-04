import requests
import pytest
import datetime
from config import base_url

@pytest.fixture
def setupRequest():
    HEADERS = {
        'origin': 'https://travelata.ru',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    PARAMS = {
        'limit': 2000,
        'departureCity': 2,
        'country': 92,
        'checkInDateRange[from]': '2024-09-30',
        'checkInDateRange[to]': '2024-09-30',
        'nightRange[from]': 7,
        'nightRange[to]': 10,
        'touristGroup[adults]': 2,
        'touristGroup[kids]': 1,
        'touristGroup[infants]': 0,
        'touristGroup[kidsAges][]': 8
    }

    try:
        response = requests.get(f'{base_url}frontend/tours', headers=HEADERS, params=PARAMS)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        pytest.fail(f"HTTP запрос не выполнен: {e}")


def test_get_success_response_result(setupRequest):
    response = setupRequest
    assert response.status_code == 200
    json_response = response.json()

    assert json_response.get('success') == True
    assert 'result' in json_response and json_response['result'] is not None


def test_get_success_result_tours(setupRequest):
    response = setupRequest
    json_response = response.json()

    tours = json_response['result']['tours']
    for tour in tours:
        assert 'id' in tour and tour['id'] is not None
        assert 'checkInDate' in tour
        try:
            datetime.datetime.strptime(tour['checkInDate'], '%Y-%m-%d')
        except ValueError:
            pytest.fail(f"Неверный формат даты: {tour['checkInDate']}")
        assert 'price' in tour and tour['price'] > 0
        assert 'nights' in tour
        assert 'tour' in tour['nights'] and tour['nights']['tour'] > 0
        assert 'hotel' in tour['nights'] and tour['nights']['hotel'] > 0
        assert 'touristGroup' in tour and tour['touristGroup'] is not None
        assert 'adults' in tour['touristGroup']
        assert 'kids' in tour['touristGroup'] and tour['touristGroup']['kids'] >= 0
        assert 'infants' in tour['touristGroup']
        assert 'kidsAges' in tour['touristGroup'] and tour['touristGroup']['kidsAges']


def test_tour_fields_are_valid(setupRequest):
    response = setupRequest
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
