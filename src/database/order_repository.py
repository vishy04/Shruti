from datetime import date
from src.database.supabase_client import supabase


def create_order(
    customer_id: int,
    customer_name: str,
    raw_measurement_text: str,
    delivery_date: date | None = None,
):
    data = {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "raw_measurement_text": raw_measurement_text,
    }
    if delivery_date is not None:
        data["delivery_date"] = delivery_date.isoformat()
    else:
        data["delivery_date"] = None

    order = (
        supabase.table("orders")
        .insert(data)
        .execute()
    )
    return order.data


def get_recent_orders(limit: int = 20):
    recent_orders = (
        supabase.table("orders")
        .select("*")
        .order("delivery_date", desc=True)
        .limit(limit)
        .execute()
    )
    return recent_orders.data


def get_order_due_between(start_date: date, end_date: date):
    orders = (
        supabase.table("orders")
        .select("*")
        .gte("delivery_date", start_date.isoformat())
        .lte("delivery_date", end_date.isoformat())
        .execute()
    )
    return orders.data


def get_recent_orders_missing_delivery_date(since_date: date):
    orders = (
        supabase.table("orders")
        .select("*")
        .is_("delivery_date", None)
        .gte("order_date", since_date.isoformat())
        .execute()
    )
    return orders.data


def get_last_orders_for_customer(customer_id: int, limit: int = 5):
    orders = (
        supabase.table("orders")
        .select("*")
        .eq("customer_id", customer_id)
        .order("order_date", desc=True)
        .limit(limit)
        .execute()
    )
    return orders.data
