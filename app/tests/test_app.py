import pytest

from app.app import app, new, news_list, selected_new_index, selected_new_info

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_new(client):
    response = new(1)
    assert response.status_code == 200
    assert b'new.html' in response.data

def test_new_invalid_index(client):
    response = new(0)
    assert response.status_code == 200
    assert b'new.html' in response.data

def test_new_empty_news_list(client):
    news_list = []
    response = new(1)
    assert selected_new_index == -1
    assert selected_new_info == {}

def test_new_populated_news_list(client):
    news_list = [{'title': 'Test'}]
    response = new(1)
    assert selected_new_index == 0
    assert selected_new_info == {'title': 'Test'}