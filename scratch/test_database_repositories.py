import os
import sys
from datetime import date, datetime, timedelta

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from src.database.supabase_client import supabase
from src.database.customer_repository import (
    create_customer,
    get_customer,
    list_customers,
    search_customer_by_name,
)
from src.database.order_repository import (
    create_order,
    get_last_orders_for_customer,
    get_order_due_between,
    get_recent_orders,
    get_recent_orders_missing_delivery_date,
)
from src.database.session_repository import (
    clear_session,
    get_session,
    mark_session_reminded,
    upsert_session,
)


def run_database_tests():
    print("=" * 60)
    print("      SUPABASE REPOSITORIES INTEGRATION TEST      ")
    print("=" * 60)

    customer_id = None
    order_id = None
    test_phone = "+19998887777"

    try:
        # 1. Test Customer Repository
        print("\n[1] Testing Customer Repository...")
        test_name = f"TestCustomer_{int(datetime.now().timestamp())}"
        test_tag = "ScratchTestTag"
        test_contact = "1234567890"

        # Create
        print(f"Creating customer '{test_name}'...")
        new_cust = create_customer(test_name, test_tag, test_contact)
        assert new_cust, "Failed to create customer"
        customer_id = new_cust[0]["id"]
        print(f"✅ Created customer ID: {customer_id}")

        # Get
        print(f"Getting customer ID: {customer_id}...")
        cust = get_customer(customer_id)
        assert cust, "Failed to retrieve customer"
        assert cust[0]["customer_name"] == test_name, "Customer name mismatch"
        assert cust[0]["customer_tag"] == test_tag, "Customer tag mismatch"
        assert cust[0]["contact_number"] == test_contact, "Customer contact mismatch"
        print("✅ Retrieved customer details match successfully")

        # List
        print("Listing customers...")
        all_custs = list_customers(limit=10)
        assert len(all_custs) > 0, "list_customers returned empty list"
        print("✅ List customers successful")

        # Search
        print(f"Searching customer by name '{test_name}'...")
        searched = search_customer_by_name(test_name)
        assert any(c["id"] == customer_id for c in searched), "Created customer not found in search"
        print("✅ Search customer successful")

        # 2. Test Order Repository
        print("\n[2] Testing Order Repository...")
        raw_text = "Test order measurements 34+30+38 length 40"
        delivery_dt = date.today() + timedelta(days=5)

        # Create
        print("Creating order...")
        new_order = create_order(
            customer_id=customer_id,
            customer_name=test_name,
            raw_measurement_text=raw_text,
            delivery_date=delivery_dt,
        )
        assert new_order, "Failed to create order"
        order_id = new_order[0]["id"]
        print(f"✅ Created order ID: {order_id}")

        # Get Recent
        print("Getting recent orders...")
        recent = get_recent_orders(limit=10)
        assert len(recent) > 0, "get_recent_orders returned empty list"
        print("✅ Recent orders query successful")

        # Get Due Between
        print("Getting orders due between...")
        due_orders = get_order_due_between(date.today(), date.today() + timedelta(days=10))
        assert len(due_orders) > 0, "get_order_due_between returned empty list"
        print("✅ Due between query successful")

        # Create Order with null delivery date to test get_recent_orders_missing_delivery_date
        print("Creating order with missing delivery date...")
        no_date_order = create_order(
            customer_id=customer_id,
            customer_name=test_name,
            raw_measurement_text="No date measurements",
            delivery_date=None,
        )
        no_date_order_id = no_date_order[0]["id"]
        
        # Get missing delivery date
        print("Getting orders missing delivery date...")
        missing_date_orders = get_recent_orders_missing_delivery_date(date.today() - timedelta(days=1))
        assert any(o["id"] == no_date_order_id for o in missing_date_orders), "Missing date order not found"
        print("✅ Missing delivery date query successful")
        
        # Clean up missing date order
        supabase.table("orders").delete().eq("id", no_date_order_id).execute()

        # Get last orders for customer
        print(f"Getting last orders for customer {customer_id}...")
        last_orders = get_last_orders_for_customer(customer_id)
        assert any(o["id"] == order_id for o in last_orders), "Created order not found in customer history"
        print("✅ Customer last orders retrieval successful")

        # 3. Test Session Repository
        print("\n[3] Testing Session Repository...")
        state = "AWAITING_CUSTOMER_CONFIRMATION"
        state_data = {"pending_order": raw_text}
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()

        # Upsert
        print(f"Upserting session for phone {test_phone}...")
        session = upsert_session(test_phone, state, state_data, expires_at)
        assert session, "Failed to upsert session"
        print("✅ Session upserted successfully")

        # Get
        print("Getting session...")
        sess = get_session(test_phone)
        assert sess, "Failed to retrieve session"
        assert sess[0]["state"] == state, "Session state mismatch"
        assert sess[0]["state_data"] == state_data, "Session state_data mismatch"
        assert sess[0]["reminded_once"] is False, "Default reminded_once should be False"
        print("✅ Session details match successfully")

        # Mark Reminded
        print("Marking session as reminded...")
        reminded = mark_session_reminded(test_phone)
        assert reminded, "Failed to mark session as reminded"
        sess_rem = get_session(test_phone)
        assert sess_rem[0]["reminded_once"] is True, "reminded_once should be True"
        print("✅ Session marked reminded successfully")

        # Clear/Delete
        print("Clearing session...")
        deleted = clear_session(test_phone)
        assert deleted, "Failed to clear session"
        sess_deleted = get_session(test_phone)
        assert not sess_deleted, "Session should no longer exist"
        print("✅ Session cleared successfully")

        print("\n" + "=" * 60)
        print("🎉 ALL DATABASE REPOSITORY TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise e

    finally:
        # Clean up database records
        print("\nCleaning up test records from database...")
        if order_id:
            try:
                supabase.table("orders").delete().eq("id", order_id).execute()
                print(f"Deleted test order: {order_id}")
            except Exception as e:
                print(f"Failed to delete test order: {e}")
        if customer_id:
            try:
                supabase.table("customer").delete().eq("id", customer_id).execute()
                print(f"Deleted test customer: {customer_id}")
            except Exception as e:
                print(f"Failed to delete test customer: {e}")
        try:
            clear_session(test_phone)
        except Exception:
            pass
        print("Cleanup completed.")


if __name__ == "__main__":
    run_database_tests()
