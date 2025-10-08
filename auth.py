import streamlit as st
import database as db

def show_auth_ui():
    """
    Displays the user login/signup UI in the sidebar.
    Returns the user object if logged in, otherwise None.
    """
    st.sidebar.title("Welcome!")

    if 'user' in st.session_state:
        user_email = st.session_state.user.email
        st.sidebar.write(f"Logged in as: {user_email}")
        if st.sidebar.button("Logout"):
            del st.session_state.user
            # Clear user-specific caches on logout
            db.get_entries_by_date.clear()
            db.get_all_entries.clear()
            st.rerun()
        return st.session_state.user

    login_tab, signup_tab = st.sidebar.tabs(["Login", "Sign Up"])

    with login_tab:
        with st.form(key="login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button(label="Login"):
                try:
                    user = db.login_user(email, password)
                    st.session_state.user = user
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

    with signup_tab:
        with st.form(key="signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            if st.form_submit_button(label="Request Account"):
                try:
                    user = db.create_user(email, password)
                    st.success("Account request received! An admin will approve it shortly.")
                    st.info("Please also check your email to confirm your address.")
                except Exception as e:
                    st.error(f"Sign up failed: {e}")
    
    return None