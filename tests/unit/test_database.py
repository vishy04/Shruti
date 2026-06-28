import pytest
from unittest.mock import MagicMock
from datetime import date
from src.database.supabase_client import supabase
import src.database.customer_repository as cust_repo
import src.database.order_repository as order_repo
import src.database.session_repository as session_repo


def test_get_customer(monkeypatch):
    mock_execute = MagicMock()
    mock_execute.return_value.data = [{"id": 123, "customer_name": "Alice", "customer_tag": "Friend"}]
    
    mock_eq = MagicMock()
    mock_eq.return_value.execute = mock_execute
    
    mock_select = MagicMock()
    mock_select.return_value.eq = mock_eq
    
    mock_table = MagicMock()
    mock_table.return_value.select = mock_select
    
    monkeypatch.setattr(supabase, "table", mock_table)
    
    res = cust_repo.get_customer(123)
    assert res == [{"id": 123, "customer_name": "Alice", "customer_tag": "Friend"}]
    mock_table.assert_called_once_with("customer")
    mock_select.assert_called_once_with("*")
    mock_eq.assert_called_once_with("id", 123)


def test_create_customer(monkeypatch):
    mock_execute = MagicMock()
    mock_execute.return_value.data = [{"id": 123, "customer_name": "Bob", "customer_tag": "Kolar"}]
    
    mock_insert = MagicMock()
    mock_insert.return_value.execute = mock_execute
    
    mock_table = MagicMock()
    mock_table.return_value.insert = mock_insert
    
    monkeypatch.setattr(supabase, "table", mock_table)
    
    res = cust_repo.create_customer("Bob", "Kolar", "9876543210")
    assert res == [{"id": 123, "customer_name": "Bob", "customer_tag": "Kolar"}]
    mock_table.assert_called_once_with("customer")
    mock_insert.assert_called_once_with({
        "customer_name": "Bob",
        "customer_tag": "Kolar",
        "contact_number": "9876543210"
    })


def test_create_order(monkeypatch):
    mock_execute = MagicMock()
    mock_execute.return_value.data = [{"id": 99, "customer_name": "Bob", "delivery_date": "2026-07-05"}]
    
    mock_insert = MagicMock()
    mock_insert.return_value.execute = mock_execute
    
    mock_table = MagicMock()
    mock_table.return_value.insert = mock_insert
    
    monkeypatch.setattr(supabase, "table", mock_table)
    
    delivery_date = date(2026, 7, 5)
    res = order_repo.create_order(123, "Bob", "Measurements test text", delivery_date)
    assert res == [{"id": 99, "customer_name": "Bob", "delivery_date": "2026-07-05"}]
    mock_table.assert_called_once_with("orders")
    mock_insert.assert_called_once_with({
        "customer_id": 123,
        "customer_name": "Bob",
        "raw_measurement_text": "Measurements test text",
        "delivery_date": "2026-07-05"
    })


def test_create_order_no_date(monkeypatch):
    mock_execute = MagicMock()
    mock_execute.return_value.data = [{"id": 99, "customer_name": "Bob", "delivery_date": None}]
    
    mock_insert = MagicMock()
    mock_insert.return_value.execute = mock_execute
    
    mock_table = MagicMock()
    mock_table.return_value.insert = mock_insert
    
    monkeypatch.setattr(supabase, "table", mock_table)
    
    res = order_repo.create_order(123, "Bob", "Measurements test text", None)
    assert res == [{"id": 99, "customer_name": "Bob", "delivery_date": None}]
    mock_table.assert_called_once_with("orders")
    mock_insert.assert_called_once_with({
        "customer_id": 123,
        "customer_name": "Bob",
        "raw_measurement_text": "Measurements test text",
        "delivery_date": None
    })


def test_get_session(monkeypatch):
    mock_execute = MagicMock()
    mock_execute.return_value.data = [{"phone_number": "+12345", "state": "CONFIRMING"}]
    
    mock_eq = MagicMock()
    mock_eq.return_value.execute = mock_execute
    
    mock_select = MagicMock()
    mock_select.return_value.eq = mock_eq
    
    mock_table = MagicMock()
    mock_table.return_value.select = mock_select
    
    monkeypatch.setattr(supabase, "table", mock_table)
    
    res = session_repo.get_session("+12345")
    assert res == [{"phone_number": "+12345", "state": "CONFIRMING"}]
    mock_table.assert_called_once_with("sessions")
    mock_select.assert_called_once_with("*")
    mock_eq.assert_called_once_with("phone_number", "+12345")


def test_upsert_session(monkeypatch):
    mock_execute = MagicMock()
    mock_execute.return_value.data = [{"phone_number": "+12345"}]
    
    mock_upsert = MagicMock()
    mock_upsert.return_value.execute = mock_execute
    
    mock_table = MagicMock()
    mock_table.return_value.upsert = mock_insert = mock_upsert
    
    monkeypatch.setattr(supabase, "table", mock_table)
    
    res = session_repo.upsert_session("+12345", "CONFIRMING", {"foo": "bar"}, "2026-06-30T12:00:00")
    assert res == [{"phone_number": "+12345"}]
    mock_table.assert_called_once_with("sessions")
    mock_insert.assert_called_once_with({
        "phone_number": "+12345",
        "state": "CONFIRMING",
        "state_data": {"foo": "bar"},
        "expires_at": "2026-06-30T12:00:00"
    })
