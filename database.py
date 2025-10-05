import streamlit as st
from supabase import create_client, Client
from datetime import date

# --- Supabase Connection ---
def init_db():
    """Initializes the connection to the Supabase database."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)
        return supabase
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

supabase: Client = init_db()

# --- Data Fetching Functions ---

def get_entries_by_date(entry_date: date):
    """Retrieves all food entries for a specific date from Supabase."""
    if not supabase: return []
    try:
        response = supabase.table('entries').select("*").eq('entry_date', entry_date.isoformat()).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching entries: {e}")
        return []

def get_all_entries():
    """Retrieves all entries from the database for historical analysis."""
    if not supabase: return []
    try:
        response = supabase.table('entries').select("*").order('entry_date', desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching all entries: {e}")
        return []

# --- Data Modification Functions ---

def add_entry(entry_date: date, description: str, calories: int, protein: int, carbs: int, fats: int, goals: dict):
    """Adds a new food entry to the Supabase database."""
    if not supabase: return
    try:
        supabase.table('entries').insert({
            'entry_date': entry_date.isoformat(),
            'description': description,
            'calories': calories,
            'protein': protein,
            'carbs': carbs,
            'fats': fats,
            'goal_calories': goals['calories'],
            'goal_protein': goals['protein'],
            'goal_carbs': goals['carbs'],
            'goal_fats': goals['fats']
        }).execute()
    except Exception as e:
        st.error(f"Error adding entry: {e}")

def delete_entry(entry_id: int):
    """Deletes an entry by its ID from Supabase."""
    if not supabase: return
    try:
        supabase.table('entries').delete().eq('id', entry_id).execute()
    except Exception as e:
        st.error(f"Error deleting entry: {e}")

def update_entry(entry_id: int, description: str, calories: int, protein: int, carbs: int, fats: int):
    """Updates an existing food entry in Supabase."""
    if not supabase: return
    try:
        supabase.table('entries').update({
            'description': description,
            'calories': calories,
            'protein': protein,
            'carbs': carbs,
            'fats': fats
        }).eq('id', entry_id).execute()
    except Exception as e:
        st.error(f"Error updating entry: {e}")

def update_goals_for_date(entry_date: date, new_goals: dict):
    """Updates the goal columns for all entries on a specific date in Supabase."""
    if not supabase: return
    try:
        supabase.table('entries').update({
            'goal_calories': new_goals['calories'],
            'goal_protein': new_goals['protein'],
            'goal_carbs': new_goals['carbs'],
            'goal_fats': new_goals['fats']
        }).eq('entry_date', entry_date.isoformat()).execute()
    except Exception as e:
        st.error(f"Error updating goals: {e}")