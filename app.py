import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import database as db
import auth

# --- App Configuration ---
st.set_page_config(
    page_title="Nutrition Tracker",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- User Authentication ---
# The `user` object will be 'guest' for guests, a user object for admin, or None.
user = auth.show_auth_ui()

# If no choice has been made yet, stop the app.
if not user:
    st.title("Welcome to the Nutrition Tracker!")
    st.write("Please choose a role in the sidebar to continue.")
    st.stop()

is_admin = user != 'guest'

# --- Initialize Session State ---
if 'default_goals' not in st.session_state:
    st.session_state.default_goals = {
        'calories': 2000, 'protein': 150, 'carbs': 250, 'fats': 60
    }
if 'daily_goal_overrides' not in st.session_state:
    st.session_state.daily_goal_overrides = {}

# --- Main App UI ---
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Daily Log", "Analytics Dashboard"])

st.sidebar.header("Set Default Goals")
st.sidebar.caption("Used as a template for new days.")
st.session_state.default_goals['calories'] = st.sidebar.number_input(
    "Calories (kcal)", value=st.session_state.default_goals['calories'], min_value=0, step=50, key="default_cal", disabled=(not is_admin))
st.session_state.default_goals['protein'] = st.sidebar.number_input(
    "Protein (g)", value=st.session_state.default_goals['protein'], min_value=0, step=5, key="default_pro", disabled=(not is_admin))
st.session_state.default_goals['carbs'] = st.sidebar.number_input(
    "Carbs (g)", value=st.session_state.default_goals['carbs'], min_value=0, step=5, key="default_carb", disabled=(not is_admin))
st.session_state.default_goals['fats'] = st.sidebar.number_input(
    "Fats (g)", value=st.session_state.default_goals['fats'], min_value=0, step=5, key="default_fat", disabled=(not is_admin))


# --- Page Logic ---
if page == "Daily Log":
    if is_admin:
        st.title(f"🥗 Daily Log (Admin Mode)")
    else:
        st.title(f"🥗 Daily Log (Guest Mode)")

    selected_date = st.date_input("Select a date", date.today())
    entries = db.get_entries_by_date(selected_date)
    
    # --- Display Logs & Totals (Visible to Everyone) ---
    st.header(f"Entries for {selected_date.strftime('%B %d, %Y')}")
    if entries:
        day_goals = {
            'calories': entries[0]['goal_calories'], 'protein': entries[0]['goal_protein'],
            'carbs': entries[0]['goal_carbs'], 'fats': entries[0]['goal_fats']
        }
        df_display = pd.DataFrame.from_records(entries)
        totals = df_display[['calories', 'protein', 'carbs', 'fats']].sum()
        
        st.subheader("Daily Totals")
        cols = st.columns(4)
        for i, (metric, total) in enumerate(totals.items()):
            goal = day_goals.get(metric, 0)
            progress = min(total / goal, 1.0) if goal > 0 else 0
            with cols[i]:
                st.metric(label=metric.capitalize(), value=f"{int(total)}/{int(goal)}", delta=f"{int(goal-total)} remaining")
                st.progress(progress)
    else:
        st.info("No meals logged for this day.")

    # --- ADMIN-ONLY SECTION ---
    if is_admin:
        day_goals_admin = None # Recalculate for admin context
        if entries:
            day_goals_admin = {
                'calories': entries[0]['goal_calories'], 'protein': entries[0]['goal_protein'],
                'carbs': entries[0]['goal_carbs'], 'fats': entries[0]['goal_fats']
            }
        elif str(selected_date) in st.session_state.daily_goal_overrides:
            day_goals_admin = st.session_state.daily_goal_overrides[str(selected_date)]
        else:
            day_goals_admin = st.session_state.default_goals

        with st.expander("🎯 Set / Edit Goals for this Day", expanded=False):
            with st.form("day_goals_form"):
                st.write("Adjust the goals for this specific day.")
                c1, c2 = st.columns(2)
                g_calories = c1.number_input("Calories", value=day_goals_admin['calories'], min_value=0, step=50)
                g_protein = c2.number_input("Protein", value=day_goals_admin['protein'], min_value=0, step=5)
                g_carbs = c1.number_input("Carbs", value=day_goals_admin['carbs'], min_value=0, step=5)
                g_fats = c2.number_input("Fats", value=day_goals_admin['fats'], min_value=0, step=5)

                if st.form_submit_button("Save Goals"):
                    new_goals = {'calories': g_calories, 'protein': g_protein, 'carbs': g_carbs, 'fats': g_fats}
                    if entries:
                        db.update_goals_for_date(selected_date, new_goals)
                    else:
                        st.session_state.daily_goal_overrides[str(selected_date)] = new_goals
                    st.success("Goals saved!")
                    st.rerun()

        st.subheader("Manage Meals (Admin)")
        
        if entries:
            df_editor = pd.DataFrame.from_records(entries).set_index('id')
        else:
            df_editor = pd.DataFrame(columns=['description', 'calories', 'protein', 'carbs', 'fats'])

        edited_df = st.data_editor(
            data=df_editor[['description', 'calories', 'protein', 'carbs', 'fats']],
            num_rows="dynamic",
            key="meal_editor",
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("id", disabled=True, required=False),
                "description": st.column_config.TextColumn("Meal Description", required=True),
                "calories": st.column_config.NumberColumn("Calories (kcal)", default=0, min_value=0, required=True),
                "protein": st.column_config.NumberColumn("Protein (g)", default=0, min_value=0, required=True),
                "carbs": st.column_config.NumberColumn("Carbs (g)", default=0, min_value=0, required=True),
                "fats": st.column_config.NumberColumn("Fats (g)", default=0, min_value=0, required=True),
            }
        )
        if st.button("Save Meal Changes"):
            is_valid = True # Add validation logic back if needed
            if is_valid:
                original_ids = set(df_editor.index)
                edited_ids = set(edited_df.index)

                # Deletions
                deleted_ids = original_ids - edited_ids
                for entry_id in deleted_ids:
                    db.delete_entry(entry_id)

                # Additions and Updates
                for entry_id, row in edited_df.iterrows():
                    if entry_id not in original_ids:
                        db.add_entry(
                            selected_date, row['description'], row['calories'],
                            row['protein'], row['carbs'], row['fats'], day_goals_admin,
                            user.id
                        )
                    else:
                        original_row = df_editor.loc[entry_id]
                        if list(row.values) != list(original_row[['description', 'calories', 'protein', 'carbs', 'fats']].values):
                            db.update_entry(
                                entry_id, row['description'], row['calories'],
                                row['protein'], row['carbs'], row['fats']
                            )
                st.success("Changes saved!")
                st.rerun()
    else: # If guest
        st.info("You are in guest mode. Data is view-only.")


elif page == "Analytics Dashboard":
    st.title("📊 Analytics Dashboard")
    all_entries = db.get_all_entries()

    if not all_entries:
        st.warning("No data to display.")
    else:
        df_all = pd.DataFrame.from_records(all_entries)
        df_all['entry_date'] = pd.to_datetime(df_all['entry_date'])

        daily_summary = df_all.groupby(df_all['entry_date'].dt.date).agg(
            actual_calories=('calories', 'sum'), goal_calories=('goal_calories', 'first'),
            actual_protein=('protein', 'sum'), goal_protein=('goal_protein', 'first'),
            actual_carbs=('carbs', 'sum'), goal_carbs=('goal_carbs', 'first'),
            actual_fats=('fats', 'sum'), goal_fats=('goal_fats', 'first')
        ).reset_index()

        st.subheader("Calorie Intake Over Time")
        fig_calories = px.line(daily_summary, x='entry_date', y=['actual_calories', 'goal_calories'], title='Daily Calorie Intake vs. Goal')
        st.plotly_chart(fig_calories, use_container_width=True)
        
        st.subheader("Protein Intake Over Time")
        fig_protein = px.line(daily_summary, x='entry_date', y=['actual_protein', 'goal_protein'], title='Daily Protein Intake vs. Goal')
        st.plotly_chart(fig_protein, use_container_width=True)

        st.subheader("Carbohydrate Intake Over Time")
        fig_carbs = px.line(daily_summary, x='entry_date', y=['actual_carbs', 'goal_carbs'], title='Daily Carbohydrate Intake vs. Goal')
        st.plotly_chart(fig_carbs, use_container_width=True)

        st.subheader("Fat Intake Over Time")
        fig_fats = px.line(daily_summary, x='entry_date', y=['actual_fats', 'goal_fats'], title='Daily Fat Intake vs. Goal')
        st.plotly_chart(fig_fats, use_container_width=True)
