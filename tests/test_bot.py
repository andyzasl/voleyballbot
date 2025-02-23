import pytest
from bot import start, register, _show_my_data
from telegram import Update

@pytest.fixture
def mock_update(monkeypatch):
    update = Update(123, chat_id=456)
    return update

def test_start(mock_update):
    start(mock_update, None)
    # Verify response is correct
    
def test_register(mock_update):
    register(mock_update, None)
    # Verify player creation logic
    
def test_show_my_data(mock_update):
    _show_my_data(mock_update, None)
    # Verify data display
