import streamlit as st
import database as db

def show_auth_ui():
    """
    Displays the admin login/guest UI in the sidebar.
    Returns the user object if logged in as admin, 'guest' if in guest mode, 
    otherwise None if no choice is made.
    """
    # If a choice has already been made, maintain that state.
    if 'user' in st.session_state and st.session_state.user:
        if st.session_state.user == 'guest':
            st.sidebar.write("Viewing as a Guest.")
            if st.sidebar.button("Switch to Admin Login"):
                del st.session_state.user
                st.rerun()
        else:
            user_email = st.session_state.user.email
            st.sidebar.write(f"Logged in as: {user_email}")
            if st.sidebar.button("Logout"):
                del st.session_state.user
                st.rerun()
        return st.session_state.user

    # Initial choice screen
    st.sidebar.title("Choose Your Role")
    
    if st.sidebar.button("Continue as Guest"):
        st.session_state.user = 'guest'
        st.rerun()

    with st.sidebar.expander("Admin Login"):
        with st.form(key="admin_login_form"):
            email = st.text_input("Admin Email")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button(label="Login")

            if submit_button:
                if not email or not password:
                    st.error("Please enter both email and password.")
                    return None
                
                try:
                    user = db.login_user(email, password)
                    st.session_state.user = user
                    st.success("Admin login successful!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login Failed: {e}")
                    return None
    
    return None