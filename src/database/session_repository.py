from src.database.supabase_client import supabase


def get_session(phone_number: str):
    session = (
        supabase.table("sessions").select("*").eq("phone_number", phone_number).execute()
    )
    return session.data


def upsert_session(
    phone_number: str,
    state: str,
    state_data,
    expires_at,
):
    session = (
        supabase.table("sessions")
        .upsert(
            {
                "phone_number": phone_number,
                "state": state,
                "state_data": state_data,
                "expires_at": expires_at,
            }
        )
        .execute()
    )
    return session.data


def mark_session_reminded(phone_number: str):
    query = (
        supabase.table("sessions")
        .update({"reminded_once": True})
        .eq("phone_number", phone_number)
        .execute()
    )
    return query.data


def clear_session(phone_number: str):
    deleted = (
        supabase.table("sessions").delete().eq("phone_number", phone_number).execute()
    )
    return deleted.data
