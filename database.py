import streamlit as st
from supabase import create_client, Client
from datetime import date

# --- Supabase Initialization ---
def init_connection():
    """Initializes the connection to the Supabase database."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

supabase: Client = init_connection()

# --- User Authentication Functions ---
# The admin user should be created directly in the Supabase dashboard.

def login_user(email, password):
    """Logs in an existing user."""
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if res.user:
        return res.user
    else:
        raise Exception(res.error.message if res.error else "Invalid login credentials.")

# --- Data Functions ---

@st.cache_data(ttl=60)
def get_entries_by_date(entry_date: date):
    """Retrieves all food entries for a specific date (publicly readable)."""
    response = supabase.table('entries').select("*").eq('entry_date', entry_date.isoformat()).order('id').execute()
    return response.data

@st.cache_data(ttl=60)
def get_all_entries():
    """Retrieves all entries (publicly readable)."""
    response = supabase.table('entries').select("*").order('entry_date', desc=True).execute()
    return response.data

def add_entry(entry_date: date, description: str, calories: float, protein: float, carbs: float, fats: float, goals: dict, user_id: str):
    """Adds a new food entry for a specific user (the admin)."""
    entry = {
        'entry_date': str(entry_date),
        'description': description,
        'calories': int(calories),
        'protein': int(protein),
        'carbs': int(carbs),
        'fats': int(fats),
        'goal_calories': int(goals['calories']),
        'goal_protein': int(goals['protein']),
        'goal_carbs': int(goals['carbs']),
        'goal_fats': int(goals['fats']),
        'user_id': user_id
    }
    response = supabase.table('entries').insert(entry).execute()
    get_entries_by_date.clear()
    get_all_entries.clear()
    return response.data

def delete_entry(entry_id: int):
    """Deletes an entry by its ID (admin only)."""
    supabase.table('entries').delete().eq('id', entry_id).execute()
    get_entries_by_date.clear()
    get_all_entries.clear()

def update_entry(entry_id: int, description: str, calories: float, protein: float, carbs: float, fats: float):
    """Updates an existing food entry (admin only)."""
    update_data = {
        'description': description,
        'calories': int(calories),
        'protein': int(protein),
        'carbs': int(carbs),
        'fats': int(fats),
    }
    supabase.table('entries').update(update_data).eq('id', entry_id).execute()
    get_entries_by_date.clear()
    get_all_entries.clear()

def update_goals_for_date(entry_date: date, new_goals: dict):
    """Updates goals for all entries on a specific date (admin only)."""
    update_data = {
        'goal_calories': int(new_goals['calories']),
        'goal_protein': int(new_goals['protein']),
        'goal_carbs': int(new_goals['carbs']),
        'goal_fats': int(new_goals['fats']),
    }
    supabase.table('entries').update(update_data).eq('entry_date', str(entry_date)).execute()
    get_entries_by_date.clear()
    get_all_entries.clear()