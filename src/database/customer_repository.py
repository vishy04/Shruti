from src.database.supabase_client import supabase


def search_customer_by_name(name: str):
    customers = (
        supabase.table("customer")
        .select("*")
        .like("customer_name", f"%{name}%")
        .execute()
    )
    return customers.data


def list_customers(limit: int = 50):
    customers = supabase.table("customer").select("*").limit(limit).execute()
    return customers.data


# number can be empty, type check hate = None on string. me use union type.
def create_customer(customer_name: str, customer_tag: str | None = None, contact_number: str | None = None):
    data = {
        "customer_name": customer_name,
        "customer_tag": customer_tag,
    }
    if contact_number is not None:
        data["contact_number"] = contact_number

    customer = (
        supabase.table("customer")
        .insert(data)
        .execute()
    )
    return customer.data


def get_customer(customer_id: int):
    customer = supabase.table("customer").select("*").eq("id", customer_id).execute()
    return customer.data
