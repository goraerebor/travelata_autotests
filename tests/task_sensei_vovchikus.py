import requests
import pytest
import re
#Предположил, что все проверки в один тест запихнуть это не верно.
#
def base_url():
    return 'https://api-gateway.travelata.ru/frontend/tours?limit=2000&departureCity=2&country=92&checkInDateRange%5Bfrom%5D=2024-09-30&checkInDateRange%5Bto%5D=2024-09-30&nightRange%5Bfrom%5D=7&nightRange%5Bto%5D=10&touristGroup%5Badults%5D=2&touristGroup%5Bkids%5D=1&touristGroup%5Binfants%5D=0&touristGroup%5BkidsAges%5D%5B%5D=8&priceRange%5Bfrom%5D=6000&priceRange%5Bto%5D=50000000&commandUuid=6e154e7f-5880-4d6f-b734-ce3cb2701739&clientUuid=dfc590fd-d65d-49e2-8ece-0d7f323bd8bc&customerUuid=&trSm=1&sections%5B%5D=hotels&sections%5B%5D=countries&sections%5B%5D=firstPaymentDefinitions&sections%5B%5D=operators&sections%5B%5D=sortRate&sections%5B%5D=hotelPhotos&abTests%5B0%5D%5Buuid%5D=54a8a079-c67b-4bb5-b6d0-046e0a0290dc&abTests%5B0%5D%5Bslug%5D=IN-3866&abTests%5B0%5D%5Bversion%5D=b&abTests%5B1%5D%5Buuid%5D=70047ba6-7fd5-4e5a-926e-a674655d2093&abTests%5B1%5D%5Bslug%5D=IN-3998&abTests%5B1%5D%5Bversion%5D=b&abTests%5B2%5D%5Buuid%5D=f84a853e-2c50-47b3-9943-88893af179a8&abTests%5B2%5D%5Bslug%5D=IN2-1155&abTests%5B2%5D%5Bversion%5D=b&abTests%5B3%5D%5Buuid%5D=293911ed-f195-448c-8b05-a949909760d2&abTests%5B3%5D%5Bslug%5D=IN2-864&abTests%5B3%5D%5Bversion%5D=a&abTests%5B4%5D%5Buuid%5D=cf8951c4-1fcf-4a77-a7bf-12bf1edf1d28&abTests%5B4%5D%5Bslug%5D=IN2-953&abTests%5B4%5D%5Bversion%5D=b'

def test_response_data():
    try:
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://travelata.ru',
            'referer': 'https://travelata.ru/',
            'sec-ch-ua': '"Not A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(base_url(), headers=headers)
        assert response.status_code == 200
        json_response = response.json()

        assert json_response['success'] == True
        assert 'result' in json_response and json_response['result'] is not None

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
            assert 'kids' in tour['touristGroup'] and tour['touristGroup']['kids']  >= 0
            assert 'infants' in tour['touristGroup']
            assert 'kidsAges' in tour['touristGroup'] and tour['touristGroup']['kidsAges']

    except requests.exceptions.RequestException as e:
        pytest.fail(f"HTTP запрос не выполнен: {e}")

