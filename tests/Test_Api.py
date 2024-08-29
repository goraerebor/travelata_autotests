import requests
import pytest

@pytest.fixture
def base_url():
    return 'https://jsonplaceholder.typicode.com/posts/'

@pytest.mark.parametrize("post_id, expected_id", [
    (1, 1),
    (42, 42),
    (100, 100),
])
def test_get_api(post_id, expected_id, base_url):
    try:
        response = requests.get(f'{base_url}{post_id}')
        assert response.status_code == 200
        json_response = response.json()
        assert 'id' in json_response, "Ключ 'id' отсутствует и Json ответе"
        assert 'body' in json_response, "Ключ 'body' отсутствует и Json ответе"
        assert 'title' in json_response, "Ключ 'title' отсутствует и Json ответе"

        assert json_response['id'] == expected_id
        assert json_response['body'], "Полее должно быть пустым"
        assert json_response['title'], "Полее должно быть пустым"

    except requests.exceptions.RequestException as e:
        pytest.fail(f"HTTP запрос не выполнен: {e}")
