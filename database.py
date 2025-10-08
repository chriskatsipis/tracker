import streamlit as st
from supabase import create_client, Client
from datetime import date
from functools import wraps

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

# --- Rate Limiting Decorator ---
def rate_limit_check(func):
    """
    A decorator that checks and updates API call counts for non-master users.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get the user from session state to perform the rate limit check.
        user = st.session_state.get('user')
        if not user or not hasattr(user, 'id'):
            raise Exception("User not logged in.")
        
        user_id = user.id
        master_user_id = st.secrets.get("MASTER_USER_ID")

        # Master user bypasses all checks
        if user_id == master_user_id:
            return func(*args, **kwargs)

        # --- Regular User Rate Limiting Logic ---
        profile = supabase.table('profiles').select('*').eq('id', user_id).single().execute().data
        if not profile:
            raise Exception("User profile not found.")

        today = date.today().isoformat()
        last_call_date = profile.get('last_api_call_date')
        api_calls = profile.get('api_call_count', 0)

        if last_call_date != today:
            # First call of the day, reset counter
            api_calls = 0
            supabase.table('profiles').update({
                'last_api_call_date': today,
                'api_call_count': 1
            }).eq('id', user_id).execute()
        elif api_calls >= 50:
            # Limit reached
            st.error("API call limit (50/day) reached. Please try again tomorrow.")
            return None # Stop execution
        else:
            # Increment counter
            supabase.table('profiles').update({
                'api_call_count': api_calls + 1
            }).eq('id', user_id).execute()

        return func(*args, **kwargs)
    return wrapper

# --- User Authentication Functions ---

def create_user(email, password):
    res = supabase.auth.sign_up({"email": email, "password": password})
    if res.user:
        return res.user
    raise Exception(res.error.message if res.error else "Could not create user.")

def login_user(email, password):
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if not res.user:
        raise Exception(res.error.message if res.error else "Invalid login credentials.")
    
    # Check if user is approved
    profile = supabase.table('profiles').select('is_approved').eq('id', res.user.id).single().execute().data
    if not profile or not profile.get('is_approved'):
        raise Exception("Account is pending admin approval.")
    
    return res.user

# --- Data Functions (now protected by rate limiter) ---

# READ functions are protected by caching.

@st.cache_data(ttl=60)
def get_entries_by_date(entry_date: date, user_id: str):
    response = supabase.table('entries').select("*").eq('entry_date', entry_date.isoformat()).eq('user_id', user_id).order('id').execute()
    return response.data

@st.cache_data(ttl=60)
def get_all_entries(user_id: str):
    response = supabase.table('entries').select("*").eq('user_id', user_id).order('entry_date', desc=True).execute()
    return response.data

# WRITE functions are protected by the rate limiter.

@rate_limit_check
def add_entry(entry_date: date, description: str, calories: float, protein: float, carbs: float, fats: float, goals: dict, user_id: str):
    entry = {'entry_date': str(entry_date), 'description': description, 'calories': int(calories), 'protein': int(protein), 'carbs': int(carbs), 'fats': int(fats), 'goal_calories': int(goals['calories']), 'goal_protein': int(goals['protein']), 'goal_carbs': int(goals['carbs']), 'goal_fats': int(goals['fats']), 'user_id': user_id}
    supabase.table('entries').insert(entry).execute()
    get_entries_by_date.clear()
    get_all_entries.clear()

@rate_limit_check
def delete_entry(entry_id: int, user_id: str): # user_id is passed for the decorator
    supabase.table('entries').delete().eq('id', entry_id).execute()
    get_entries_by_date.clear()
    get_all_entries.clear()

@rate_limit_check
def update_entry(entry_id: int, description: str, calories: float, protein: float, carbs: float, fats: float, user_id: str):
    update_data = {'description': description, 'calories': int(calories), 'protein': int(protein), 'carbs': int(carbs), 'fats': int(fats)}
    supabase.table('entries').update(update_data).eq('id', entry_id).execute()
    get_entries_by_date.clear()
    get_all_entries.clear()

@rate_limit_check
def update_goals_for_date(entry_date: date, new_goals: dict, user_id: str):
    update_data = {'goal_calories': int(new_goals['calories']), 'goal_protein': int(new_goals['protein']), 'goal_carbs': int(new_goals['carbs']), 'goal_fats': int(new_goals['fats'])}
    supabase.table('entries').update(update_data).eq('entry_date', str(entry_date)).eq('user_id', user_id).execute()
    get_entries_by_date.clear()
    get_all_entries.clear()

# --- Admin Panel Functions (not rate-limited) ---
def get_pending_users():
    """Fetches all users who are not yet approved."""
    if not supabase: return []
    # Assumes RLS is set up for admin to read all profiles
    response = supabase.table('profiles').select('id, email').eq('is_approved', False).execute()
    return response.data

def approve_user(user_id_to_approve: str):
    """Sets a user's is_approved status to True."""
    if not supabase: return
    supabase.table('profiles').update({'is_approved': True}).eq('id', user_id_to_approve).execute()

# --- User Preferences Functions ---

@st.cache_data(ttl=300) # Cache preferences for 5 minutes
def get_user_preferences(user_id: str):
    """Retrieves a user's default goals from the preferences table."""
    response = supabase.table('user_preferences').select('*').eq('user_id', user_id).execute()
    return response.data

def upsert_user_preferences(user_id: str, goals: dict):
    """Creates or updates a user's default goals."""
    preference_data = {
        'user_id': user_id,
        'default_calories': int(goals['calories']),
        'default_protein': int(goals['protein']),
        'default_carbs': int(goals['carbs']),
        'default_fats': int(goals['fats']),
    }
    # Upsert will insert a new row, or update it if a row with the user_id already exists.
    supabase.table('user_preferences').upsert(preference_data).execute()
    # Clear the cache to ensure the next load gets the fresh data
    get_user_preferences.clear()
