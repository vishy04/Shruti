import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import sheets
from src.extractor import Measurements, OrderData


class FakeCell:
    def __init__(self, value):
        self.value = value


class FakeWorksheet:
    def __init__(self, values, cell_value="O-1000"):
        self.values = values
        self.cell_value = cell_value
        self.updated_range = None
        self.updated_values = None
        self.updated_cell = None
        self.inserted_index = None
        self.inserted_values = None
        self.appended_rows = []

    def get_all_values(self):
        return self.values

    def col_values(self, col):
        return [row[col - 1] for row in self.values if len(row) >= col]

    def cell(self, row, col):
        return FakeCell(self.cell_value)

    def update(
        self, values=None, range_name=None, value_input_option=None, *args, **kwargs
    ):
        self.updated_range = range_name
        self.updated_values = values
        self.value_input_option = value_input_option

    def update_acell(self, cell, value):
        self.updated_cell = (cell, value)

    def insert_row(self, values, index=1, value_input_option=None):
        self.inserted_index = index
        self.inserted_values = values
        self.value_input_option = value_input_option

    def append_row(self, values, value_input_option=None):
        self.appended_rows.append((values, value_input_option))
        return {"updates": {"updatedRange": "Customers!A2:F2"}}


def test_append_order_writes_expected_columns(monkeypatch):
    customers_ws = FakeWorksheet(
        [
            [
                "Customer ID",
                "Customer Name",
                "Tag",
                "Notes",
                "Created At",
                "Updated At",
            ],
            ["C-101", "Test_customer", "", "", "01 Jan 26", "01 Jan 26"],
        ]
    )
    orders_ws = FakeWorksheet(
        [
            [
                "Order ID",
                "Customer Name",
                "Garment",
                "Chest",
                "Waist",
                "Hip",
                "Shoulder",
                "Sleeve",
                "Length",
                "Salwar Len",
                "Mori",
                "Delivery Date",
                "Status",
                "Notes",
                "Created At",
            ]
        ],
        cell_value="O-1000",
    )

    monkeypatch.setattr(sheets, "get_worksheets", lambda: (customers_ws, orders_ws))

    order = OrderData(
        thinking_process="Testing the google sheets connection",
        order_id="#T-101",
        customer_name="Test_customer",
        garment_type="suit",
        measurements=Measurements(chest=36, waist=30),
    )

    sheets.append_order(order)

    assert order.order_id == "O-1001"
    assert orders_ws.inserted_index == 2

    row = orders_ws.inserted_values
    assert len(row) == 15
    assert row[0] == "O-1001"
    assert row[1] == "Test_customer"
    assert row[2] == "suit"
    assert row[3] == 36
    assert row[4] == 30
    assert row[12] == "Pending"
    assert row[13] == ""
