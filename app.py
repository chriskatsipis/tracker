import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import database as db

# --- App Configuration ---
st.set_page_config(
    page_title="Nutrition Tracker",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Database Initialization ---
db.init_db()

# --- Initialize Session State ---
if 'default_goals' not in st.session_state:
    st.session_state.default_goals = {
        'calories': 2000, 'protein': 150, 'carbs': 250, 'fats': 60
    }
if 'daily_goal_overrides' not in st.session_state:
    st.session_state.daily_goal_overrides = {}

# --- Sidebar ---
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Daily Log", "Analytics Dashboard"])

st.sidebar.header("Set Default Goals")
st.sidebar.caption("Used as a template for new days.")
st.session_state.default_goals['calories'] = st.sidebar.number_input(
    "Calories (kcal)", value=st.session_state.default_goals['calories'], min_value=0, step=50, key="default_cal")
st.session_state.default_goals['protein'] = st.sidebar.number_input(
    "Protein (g)", value=st.session_state.default_goals['protein'], min_value=0, step=5, key="default_pro")
st.session_state.default_goals['carbs'] = st.sidebar.number_input(
    "Carbs (g)", value=st.session_state.default_goals['carbs'], min_value=0, step=5, key="default_carb")
st.session_state.default_goals['fats'] = st.sidebar.number_input(
    "Fats (g)", value=st.session_state.default_goals['fats'], min_value=0, step=5, key="default_fat")


# --- Main App Logic ---
if page == "Daily Log":
    st.title("🥗 Daily Nutrition Log")
    
    selected_date = st.date_input("Select a date", date.today())
    selected_date_str = str(selected_date)

    entries = db.get_entries_by_date(selected_date)
    
    # --- Determine the goals for the selected day ---
    day_goals = None
    if entries:
        day_goals = {
            'calories': entries[0]['goal_calories'], 'protein': entries[0]['goal_protein'],
            'carbs': entries[0]['goal_carbs'], 'fats': entries[0]['goal_fats']
        }
    elif selected_date_str in st.session_state.daily_goal_overrides:
        day_goals = st.session_state.daily_goal_overrides[selected_date_str]
    else:
        day_goals = st.session_state.default_goals

    # --- Edit Day's Goals Expander ---
    with st.expander("🎯 Set / Edit Goals for this Day", expanded=False):
        with st.form("day_goals_form"):
            if entries:
                st.write("Adjust the goals for this specific day. Saving will update all existing meals.")
                button_label = "Save & Update Goals"
            else:
                st.info("Set the goals for this day. They will be saved with your first meal.")
                button_label = "Set Goals for this Day"

            c1, c2 = st.columns(2)
            g_calories = c1.number_input("Calories", value=day_goals['calories'], min_value=0, step=50)
            g_protein = c2.number_input("Protein", value=day_goals['protein'], min_value=0, step=5)
            g_carbs = c1.number_input("Carbs", value=day_goals['carbs'], min_value=0, step=5)
            g_fats = c2.number_input("Fats", value=day_goals['fats'], min_value=0, step=5)

            confirm_update = True
            if entries:
                st.warning("This will change the goals for all meals already logged on this day.")
                confirm_update = st.checkbox(f"Confirm update for all {len(entries)} meals.")

            if st.form_submit_button(button_label):
                if not confirm_update and entries:
                    st.error("Please check the confirmation box to apply changes.")
                else:
                    new_goals = {'calories': g_calories, 'protein': g_protein, 'carbs': g_carbs, 'fats': g_fats}
                    if entries:
                        db.update_goals_for_date(selected_date, new_goals)
                        if selected_date_str in st.session_state.daily_goal_overrides:
                            del st.session_state.daily_goal_overrides[selected_date_str]
                        st.success("Goals updated successfully!")
                    else:
                        st.session_state.daily_goal_overrides[selected_date_str] = new_goals
                        st.success("Goals set. They will be saved with your first meal.")
                    st.rerun()

    # --- Display Logs & Daily Totals ---
    st.header(f"Entries for {selected_date.strftime('%B %d, %Y')}")

    if entries:
        # FIX: Explicitly define columns when creating the DataFrame to prevent KeyErrors.
        df_display = pd.DataFrame.from_records(entries, columns=[
            'id', 'entry_date', 'description', 'calories', 'protein', 'carbs', 'fats',
            'goal_calories', 'goal_protein', 'goal_carbs', 'goal_fats'
        ])
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
        st.info("No meals logged for this day. Add one below to get started!")

    # --- Unified Meal Editor ---
    st.subheader("Manage Meals")

    # Prepare DataFrame for the editor
    if entries:
        # FIX: Apply the same robust DataFrame creation here.
        df_editor = pd.DataFrame.from_records(entries, columns=[
            'id', 'entry_date', 'description', 'calories', 'protein', 'carbs', 'fats',
            'goal_calories', 'goal_protein', 'goal_carbs', 'goal_fats'
        ])
        df_editor.set_index('id', inplace=True)
    else:
        df_editor = pd.DataFrame(columns=['description', 'calories', 'protein', 'carbs', 'fats'])

    st.caption("Add a row, edit cells, or select a row and press the Delete/Backspace key to remove.")
    
    edited_df = st.data_editor(
        data=df_editor[['description', 'calories', 'protein', 'carbs', 'fats']],
        num_rows="dynamic",
        key="meal_editor",
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("id", disabled=True, required=False),
            "description": st.column_config.TextColumn("Meal Description", required=True),
            "calories": st.column_config.NumberColumn("Calories (kcal)", default=0, min_value=0),
            "protein": st.column_config.NumberColumn("Protein (g)", default=0, min_value=0),
            "carbs": st.column_config.NumberColumn("Carbs (g)", default=0, min_value=0),
            "fats": st.column_config.NumberColumn("Fats (g)", default=0, min_value=0),
        }
    )

    if st.button("Save Meal Changes"):
        is_valid = True
        for index, row in edited_df.iterrows():
            if pd.isna(row['description']) or str(row['description']).strip() == "":
                st.error(f"Error: Row {index+1} is missing a description.")
                is_valid = False
            if any(pd.isna(row[col]) for col in ['calories', 'protein', 'carbs', 'fats']):
                 st.error(f"Error: Row '{row['description']}' has empty nutritional values. Please fill all fields.")
                 is_valid = False

        if is_valid:
            original_ids = set(df_editor.index) if entries else set()
            edited_ids = set(edited_df.index)

            deleted_ids = original_ids - edited_ids
            for entry_id in deleted_ids:
                db.delete_entry(entry_id)

            for entry_id, row in edited_df.iterrows():
                if entry_id not in original_ids:
                    db.add_entry(
                        selected_date, row['description'], row['calories'],
                        row['protein'], row['carbs'], row['fats'], day_goals
                    )
                    if selected_date_str in st.session_state.daily_goal_overrides:
                        del st.session_state.daily_goal_overrides[selected_date_str]
                else:
                    original_row = df_editor.loc[entry_id][['description', 'calories', 'protein', 'carbs', 'fats']]
                    if list(row.values) != list(original_row.values):
                        db.update_entry(
                            entry_id, row['description'], row['calories'],
                            row['protein'], row['carbs'], row['fats']
                        )
            st.success("Your changes have been saved!")
            st.rerun()


elif page == "Analytics Dashboard":
    st.title("📊 Analytics Dashboard")
    all_entries = db.get_all_entries()

    if not all_entries:
        st.warning("No data available. Add meals in the 'Daily Log' page to see analytics.")
    else:
        # FIX: Apply the same robust DataFrame creation to the analytics data.
        df_all = pd.DataFrame.from_records(all_entries, columns=[
            'id', 'entry_date', 'description', 'calories', 'protein', 'carbs', 'fats',
            'goal_calories', 'goal_protein', 'goal_carbs', 'goal_fats'
        ])
        df_all['entry_date'] = pd.to_datetime(df_all['entry_date'])

        daily_summary = df_all.groupby(df_all['entry_date'].dt.date).agg(
            actual_calories=('calories', 'sum'),
            goal_calories=('goal_calories', 'first'),
            actual_protein=('protein', 'sum'),
            goal_protein=('goal_protein', 'first'),
            actual_carbs=('carbs', 'sum'),
            goal_carbs=('goal_carbs', 'first'),
            actual_fats=('fats', 'sum'),
            goal_fats=('goal_fats', 'first')
        ).reset_index()

        st.subheader("Calorie Intake Over Time")
        fig_calories = px.line(
            daily_summary, x='entry_date', y=['actual_calories', 'goal_calories'],
            title='Daily Calorie Intake vs. Goal',
            labels={'entry_date': 'Date', 'value': 'Calories (kcal)'},
        )
        fig_calories.update_traces(selector={'name':'actual_calories'}, name='Actual Intake')
        fig_calories.update_traces(selector={'name':'goal_calories'}, name='Daily Goal')
        st.plotly_chart(fig_calories, use_container_width=True)

        st.subheader("Protein Intake Over Time")
        fig_protein = px.line(
            daily_summary, x='entry_date', y=['actual_protein', 'goal_protein'],
            title='Daily Protein Intake vs. Goal',
            labels={'entry_date': 'Date', 'value': 'Protein (g)'},
        )
        fig_protein.update_traces(selector={'name':'actual_protein'}, name='Actual Intake')
        fig_protein.update_traces(selector={'name':'goal_protein'}, name='Daily Goal')
        st.plotly_chart(fig_protein, use_container_width=True)
        
        st.subheader("Carbohydrate Intake Over Time")
        fig_carbs = px.line(
            daily_summary, x='entry_date', y=['actual_carbs', 'goal_carbs'],
            title='Daily Carbohydrate Intake vs. Goal',
            labels={'entry_date': 'Date', 'value': 'Carbs (g)'},
        )
        fig_carbs.update_traces(selector={'name':'actual_carbs'}, name='Actual Intake')
        fig_carbs.update_traces(selector={'name':'goal_carbs'}, name='Daily Goal')
        st.plotly_chart(fig_carbs, use_container_width=True)

        st.subheader("Fat Intake Over Time")
        fig_fats = px.line(
            daily_summary, x='entry_date', y=['actual_fats', 'goal_fats'],
            title='Daily Fat Intake vs. Goal',
            labels={'entry_date': 'Date', 'value': 'Fats (g)'},
        )
        fig_fats.update_traces(selector={'name':'actual_fats'}, name='Actual Intake')
        fig_fats.update_traces(selector={'name':'goal_fats'}, name='Daily Goal')
        st.plotly_chart(fig_fats, use_container_width=True)