import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import database as db
import auth


# --- App Configuration ---
st.set_page_config(page_title="Nutrition Tracker", page_icon="🥗", layout="wide")

# --- User Authentication ---
user = auth.show_auth_ui()

if not user:
    st.title("Welcome to the Nutrition Tracker!")
    st.info("Please log in or request an account in the sidebar to continue.")
    st.stop()

# --- Master User Check ---
is_master_admin = user.id == st.secrets.get("MASTER_USER_ID")

# --- Main App UI ---
st.sidebar.header("Navigation")
# Add Admin Panel to navigation if user is the master admin
nav_options = ["Daily Log", "Analytics Dashboard", "Recipes"]
if is_master_admin:
    nav_options.append("Admin Panel")
page = st.sidebar.radio("Go to", nav_options)

# --- Session State Initialization ---
if f'default_goals_{user.id}' not in st.session_state:
    # Try to fetch saved preferences
    saved_prefs = db.get_user_preferences(user.id)
    if saved_prefs:
        # If found, load the first record from the list
        user_prefs = saved_prefs[0]
        st.session_state[f'default_goals_{user.id}'] = {
            'calories': user_prefs['default_calories'],
            'protein': user_prefs['default_protein'],
            'carbs': user_prefs['default_carbs'],
            'fats': user_prefs['default_fats']
        }
    else:
        # Otherwise, use hardcoded defaults for new users
        st.session_state[f'default_goals_{user.id}'] = {'calories': 2000, 'protein': 150, 'carbs': 250, 'fats': 60}

if f'daily_goal_overrides_{user.id}' not in st.session_state:
    st.session_state[f'daily_goal_overrides_{user.id}'] = {}

# --- Default Goals UI ---
st.sidebar.header("Set Your Default Goals")
st.sidebar.caption("These are your master goals. Click save to make them permanent.")
default_goals = st.session_state[f'default_goals_{user.id}']
default_goals['calories'] = st.sidebar.number_input("Calories (kcal)", value=default_goals['calories'], min_value=0, step=50, key="default_cal")
default_goals['protein'] = st.sidebar.number_input("Protein (g)", value=default_goals['protein'], min_value=0, step=5, key="default_pro")
default_goals['carbs'] = st.sidebar.number_input("Carbs (g)", value=default_goals['carbs'], min_value=0, step=5, key="default_carb")
default_goals['fats'] = st.sidebar.number_input("Fats (g)", value=default_goals['fats'], min_value=0, step=5, key="default_fat")

if st.sidebar.button("Save Default Goals"):
    db.upsert_user_preferences(user.id, default_goals)
    st.sidebar.success("Your default goals have been saved!")

# --- Page Routing ---
if page == "Daily Log":
    st.title("🥗 Daily Log")
    # ... (Daily Log page logic from your file, with user.id passed to db calls)
    if 'flash_message' in st.session_state:
        st.success(st.session_state.flash_message)
        del st.session_state.flash_message
    selected_date = st.date_input("Select a date", date.today())
    entries = db.get_entries_by_date(selected_date, user.id)
    st.header(f"Entries for {selected_date.strftime('%B %d, %Y')}")
    if entries:
        day_goals = {
            'calories': entries[0]['goal_calories'],
            'protein': entries[0]['goal_protein'],
            'carbs': entries[0]['goal_carbs'],
            'fats': entries[0]['goal_fats']}
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
    
    daily_goal_overrides = st.session_state[f'daily_goal_overrides_{user.id}']
    user_day_goals = None
    if entries:
        user_day_goals = {
            'calories': entries[0]['goal_calories'],
            'protein': entries[0]['goal_protein'],
            'carbs': entries[0]['goal_carbs'],
            'fats': entries[0]['goal_fats']}
    elif str(selected_date) in daily_goal_overrides:
        user_day_goals = daily_goal_overrides[str(selected_date)]
    else:
        user_day_goals = default_goals

    with st.expander("🎯 Set / Edit Goals for this Day", expanded=False):
        with st.form("day_goals_form"):
            st.write("Adjust the goals for this specific day.")
            c1, c2 = st.columns(2)
            g_calories = c1.number_input("Calories", value=user_day_goals['calories'], min_value=0, step=50)
            g_protein = c2.number_input("Protein", value=user_day_goals['protein'], min_value=0, step=5)
            g_carbs = c1.number_input("Carbs", value=user_day_goals['carbs'], min_value=0, step=5)
            g_fats = c2.number_input("Fats", value=user_day_goals['fats'], min_value=0, step=5)
            if st.form_submit_button("Save Goals"):
                new_goals = {'calories': g_calories, 'protein': g_protein, 'carbs': g_carbs, 'fats': g_fats}
                if entries:
                    db.update_goals_for_date(selected_date, new_goals, user.id)
                else:
                    daily_goal_overrides[str(selected_date)] = new_goals
                st.session_state.flash_message = "Goals saved successfully!"
                st.rerun()

    # --- Log from Recipe ---
    with st.expander("🍳 Log a Meal from Your Recipes"):
        user_recipes = db.get_recipes(user.id)
        if not user_recipes:
            st.info("You don't have any recipes to log. Go to the 'Recipes' page to add one.")
        else:
            recipe_options = {recipe['name']: recipe for recipe in user_recipes}
            selected_recipe_name = st.selectbox("Choose a recipe to log", options=recipe_options.keys())
            
            selected_recipe = recipe_options[selected_recipe_name]
            
            servings_eaten = st.number_input("How many servings did you eat?", min_value=0.1, step=0.25, value=1.0)
            
            if st.button("Add Recipe to Log"):
                # Calculate the nutrition based on servings eaten
                final_calories = selected_recipe['calories_per_serving'] * servings_eaten
                final_protein = selected_recipe['protein_per_serving'] * servings_eaten
                final_carbs = selected_recipe['carbs_per_serving'] * servings_eaten
                final_fats = selected_recipe['fats_per_serving'] * servings_eaten
                
                # Use the day's goals (already calculated on this page)
                desc = f"{selected_recipe['name']} ({servings_eaten} servings)"
                
                # Add to the database
                db.add_entry(selected_date, desc, final_calories, final_protein, final_carbs, final_fats, user_day_goals, user.id)
                st.success(f"Added '{desc}' to your log for {selected_date.strftime('%B %d, %Y')}!")
                st.rerun()

    st.subheader("Manage Your Meals")
    if entries:
        df_editor = pd.DataFrame.from_records(entries).set_index('id')
    else:
        df_editor = pd.DataFrame(columns=['description', 'calories', 'protein', 'carbs', 'fats'])
    edited_df = st.data_editor(
        data=df_editor[['description', 'calories', 'protein', 'carbs', 'fats']],
        num_rows="dynamic", key="meal_editor",
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn(disabled=True, required=False),
            "description": st.column_config.TextColumn("Meal Description", required=True),
            "calories": st.column_config.NumberColumn("Calories (kcal)", default=0, min_value=0, required=True),
            "protein": st.column_config.NumberColumn("Protein (g)", default=0, min_value=0, required=True),
            "carbs": st.column_config.NumberColumn("Carbs (g)", default=0, min_value=0, required=True),
            "fats": st.column_config.NumberColumn("Fats (g)", default=0, min_value=0, required=True)})
    if st.button("Save Meal Changes"):
        original_ids, edited_ids = set(df_editor.index), set(edited_df.index)
        deleted_ids = original_ids - edited_ids
        for entry_id in deleted_ids:
            db.delete_entry(entry_id, user.id)
        for entry_id, row in edited_df.iterrows():
            if entry_id not in original_ids:
                db.add_entry(selected_date, row['description'], row['calories'], row['protein'], row['carbs'], row['fats'], user_day_goals, user.id)
            else:
                original_row = df_editor.loc[entry_id]
                if list(row.values) != list(original_row[['description', 'calories', 'protein', 'carbs', 'fats']].values):
                    db.update_entry(entry_id, row['description'], row['calories'], row['protein'], row['carbs'], row['fats'], user.id)
        st.session_state.flash_message = "Changes saved successfully!"
        st.rerun()


elif page == "Analytics Dashboard":
    st.title("📊 Your Analytics Dashboard")
    # ... (Analytics page logic from your file, with user.id passed to db call)
    all_entries = db.get_all_entries(user.id)
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

elif page == "Recipes":
    st.title("🍳 Your Recipe Book")

    # --- Add New Recipe Form ---
    with st.expander("＋ Add a New Recipe"):
        with st.form("new_recipe_form", clear_on_submit=True):
            st.subheader("Recipe Details")
            recipe_name = st.text_input("Recipe Name")
            recipe_desc = st.text_area("Description")
            recipe_servings = st.number_input("Total Servings this Recipe Makes", min_value=0.1, step=0.5, value=1.0)
            
            st.subheader("Nutrition per Serving")
            c1, c2 = st.columns(2)
            recipe_cals = c1.number_input("Calories (kcal)", min_value=0)
            recipe_prot = c2.number_input("Protein (g)", min_value=0)
            recipe_carbs = c1.number_input("Carbs (g)", min_value=0)
            recipe_fats = c2.number_input("Fats (g)", min_value=0)

            st.subheader("Preparation")
            recipe_instr = st.text_area("Instructions")
            
            recipe_public = st.toggle("Make Recipe Public?", help="If enabled, other users will be able to see and use this recipe.")

            if st.form_submit_button("Save Recipe"):
                nutrition = {'calories': recipe_cals, 'protein': recipe_prot, 'carbs': recipe_carbs, 'fats': recipe_fats}
                db.add_recipe(user.id, recipe_name, recipe_desc, recipe_instr, recipe_servings, nutrition, recipe_public)
                st.success(f"Recipe '{recipe_name}' saved successfully!")
                st.rerun()

    # --- Display Recipes ---
    my_recipes, public_recipes = st.tabs(["My Recipes", "Public Recipes"])

    with my_recipes:
        st.header("My Personal Recipes")
        user_recipes = db.get_recipes(user.id)
        if not user_recipes:
            st.info("You haven't added any recipes yet. Use the form above to get started!")
        for recipe in user_recipes:
            with st.expander(f"{recipe['name']} ({recipe['servings_per_recipe']} servings)"):
                st.markdown(f"**Description:** {recipe['description']}")
                st.markdown(f"**Nutrition per Serving:** {recipe['calories_per_serving']} kcal, {recipe['protein_per_serving']}g P, {recipe['carbs_per_serving']}g C, {recipe['fats_per_serving']}g F")
                st.markdown("**Instructions:**")
                st.markdown(recipe['instructions'])
                if st.button("Delete", key=f"del_{recipe['id']}"):
                    db.delete_recipe(recipe['id'])
                    st.rerun()

    with public_recipes:
        st.header("Public Recipes from the Community")
        all_public_recipes = db.get_public_recipes()
        if not all_public_recipes:
            st.info("No public recipes are available yet.")
        for recipe in all_public_recipes:
             with st.expander(f"{recipe['name']} ({recipe['servings_per_recipe']} servings)"):
                st.markdown(f"**Description:** {recipe['description']}")
                st.markdown(f"**Nutrition per Serving:** {recipe['calories_per_serving']} kcal, {recipe['protein_per_serving']}g P, {recipe['carbs_per_serving']}g C, {recipe['fats_per_serving']}g F")
                st.markdown("**Instructions:**")
                st.markdown(recipe['instructions'])

elif page == "Admin Panel" and is_master_admin:
    st.title("👑 Admin Panel")
    st.header("Pending User Approvals")
    
    pending_users = db.get_pending_users()
    
    if not pending_users:
        st.success("No users are currently awaiting approval.")
    else:
        st.info(f"You have {len(pending_users)} user(s) awaiting approval.")
        for user in pending_users:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Email:** {user['email']}")
            with col2:
                if st.button("Approve", key=f"approve_{user['id']}"):
                    db.approve_user(user['id'])
                    st.success(f"User {user['email']} approved!")
                    st.rerun()

