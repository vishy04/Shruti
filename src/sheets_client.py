import gspread 
import gspread.exceptions
import os 



class Sheet_Client():

    def __init__(self) -> None:
        self._gc = None
        self._sheet = None
        self._customers_ws = None
        self._orders_ws = None
        self._processed_ws = None

    def _get_client(self):

        if not self._gc:
            sa_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
            self._gc = gspread.service_account_from_dict(sa_info)

        return self._gc

    def _get_sheet(self):

        if not self._sheet:
            gc = self._get_client()
            self._sheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"]) 
        return self._sheet

    @property
    def customer_ws(self):
        if not self._customers_ws:
            self._customers_ws = self._get_sheet().worksheet("Customers")
        return self._customers_ws

    
    @property
    def order_ws(self):

        if not self._order_ws:
            self._order_ws = self._get_sheet().worksheet("Orders")
        return self._order_ws

    @property
    def processed_ws():
        if not self._processed_ws:
            self._processed_ws = self._get_sheet().worksheet("ProcessedMessages")
        return self._processed_ws


_client = Sheet_Client()

def get_customers_ws():
    return _client.customer_ws

def get_orders_ws():
    return _client.order_ws

def get_processed_messages_ws():
    return _client.processed_ws
