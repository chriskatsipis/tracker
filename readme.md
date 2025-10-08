# 🥗 Python Nutrition Tracker

A secure, deployable web application built with Streamlit and Supabase to track daily nutritional intake, including calories and macronutrients. This app features a public, view-only mode for guests and a secure, admin-only mode for data entry and management.

---

## Core Features

* **Secure Multi-User Accounts:** Users can request an account and, upon admin approval, manage their own private nutrition log.
* **Admin Approval Panel:** A special master admin user can view and approve pending account requests.
* **Recipe Management:** Create, save, and manage personal recipes with detailed instructions and per-serving nutritional information. Share recipes publicly with the community.
* **Quick Recipe Logging:** Log meals directly from your saved recipes, with automatic calculation of macros based on the number of servings eaten.
* **Daily Food Logging:** Log meals with descriptions, calories, protein, carbs, and fats.
* **Customizable Daily Goals:** Set persistent default goals and override them for specific days.
* **API Rate Limiting:** Protects the app by limiting non-admin users to 50 database writes per day.
* **Rich Analytics Dashboard:** Each user can visualize their own progress with interactive charts comparing daily intake vs. goals.
---

## How to Use the App

The application has two distinct user roles.

### As a User

1.  Navigate to the application URL and log in.
2.  **Manage Recipes:**
    * Navigate to the new **"Recipes"** page from the sidebar.
    * Use the form to add new recipes, including their per-serving nutrition. You can choose to keep them private or make them public.
    * Browse "My Recipes" and "Public Recipes" in the tabs.
3.  **Track Daily Intake:**
    * On the **"Daily Log"** page, use the **"Log from Recipe"** section to quickly add a meal from your saved recipes.
    * Alternatively, use the interactive table under "Manage Your Meals" to add, edit, or delete individual meal entries.
4.  **Set Goals:**
    * Change your macro targets in the sidebar and click "Save Default Goals".
    * Use the "Set / Edit Goals" section on the Daily Log to override defaults for a specific day.

### As the Administrator

1.  Log in with the master admin account credentials.
2.  You have all the same permissions as a regular user.
3.  Additionally, an **"Admin Panel"** option will appear in the navigation sidebar, allowing you to approve new user requests.
---

## Tech Stack

This project uses a modern, efficient stack chosen for rapid development, ease of use, and a generous free tier for hosting.

* **Python:** The core programming language for the entire application.
* **Streamlit:** A Python framework used to build the entire interactive user interface with minimal code. It's responsible for rendering all pages, widgets, and charts.
* **Pandas:** Used for data manipulation, cleaning, and aggregation, forming the backbone of the analytics dashboard.
* **Plotly Express:** Powers the interactive charts on the Analytics Dashboard.
* **Supabase:** A cloud-based PostgreSQL database used as the persistent data store. It handles the database, user authentication, and row-level security.

---

## How to Use the App

The application has two distinct modes depending on your role.

### As a Guest

1.  Navigate to the application URL.
2.  In the sidebar, click **"Continue as Guest"**.
3.  You can now view all historical data on the **Daily Log** page and see all charts on the **Analytics Dashboard**.
4.  All data entry and editing controls will be hidden or disabled.

### As the Administrator

1.  Navigate to the application URL.
2.  In the sidebar, open the **"Admin Login"** expander.
3.  Enter your admin email and password and click **"Login"**.
4.  You now have full access to:
    * **Set Default Goals:** Change the default macro targets in the sidebar.
    * **Set Goals for a Specific Day:** Use the "Set / Edit Goals" section on the Daily Log.
    * **Manage Meals:** Use the interactive table to add, edit, or delete meal entries for any date.

---

## Local Setup and Installation Guide

Follow these steps to set up and run the project on your local machine.

### 1. Prerequisites

* Python 3.8+ installed on your system.
* A free [Supabase](https://supabase.com/) account.
* A free [GitHub](https://github.com/) account.

### 2. Supabase Project Setup

1.  **Create a New Project:** In your Supabase dashboard, create a new project.

2.  **Create the Database Tables via SQL:**
    * Navigate to the **SQL Editor** in your Supabase dashboard.
    * Click **"New query"**.
    * Paste the entire script below and click **"Run"**. This will create all the necessary tables.

    ```sql
    CREATE TABLE public.profiles (
      id uuid NOT NULL,
      email text NULL,
      is_approved boolean NOT NULL DEFAULT false,
      api_call_count integer NOT NULL DEFAULT 0,
      last_api_call_date date NULL,
      CONSTRAINT profiles_pkey PRIMARY KEY (id),
      CONSTRAINT profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users (id)
    ) TABLESPACE pg_default;

    CREATE TABLE public.user_preferences (
      id uuid NOT NULL,
      default_calories integer NOT NULL,
      default_protein integer NOT NULL,
      default_carbs integer NOT NULL,
      default_fats integer NOT NULL,
      CONSTRAINT user_preferences_pkey PRIMARY KEY (id),
      CONSTRAINT user_preferences_id_fkey FOREIGN KEY (id) REFERENCES auth.users (id)
    ) TABLESPACE pg_default;

    CREATE TABLE public.entries (
      id bigint GENERATED BY DEFAULT AS IDENTITY NOT NULL,
      user_id uuid NOT NULL,
      entry_date date NOT NULL,
      description text NOT NULL,
      calories integer NOT NULL,
      protein integer NOT NULL,
      carbs integer NOT NULL,
      fats integer NOT NULL,
      goal_calories integer NOT NULL,
      goal_protein integer NOT NULL,
      goal_carbs integer NOT NULL,
      goal_fats integer NOT NULL,
      CONSTRAINT entries_pkey PRIMARY KEY (id)
    ) TABLESPACE pg_default;

    CREATE TABLE public.recipes (
      id bigint GENERATED BY DEFAULT AS IDENTITY NOT NULL,
      user_id uuid NOT NULL,
      name text NOT NULL,
      description text NULL,
      instructions text NULL,
      servings_per_recipe real NOT NULL,
      calories_per_serving integer NOT NULL,
      protein_per_serving integer NOT NULL,
      carbs_per_serving integer NOT NULL,
      fats_per_serving integer NOT NULL,
      is_public boolean NOT NULL DEFAULT false,
      CONSTRAINT recipes_pkey PRIMARY KEY (id),
      CONSTRAINT recipes_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users (id)
    ) TABLESPACE pg_default;
    ```

3.  **Create the Database Trigger to automatically create a profile for each new user:**
    * Navigate to the **SQL Editor**.
    * Click **"New query"** and paste the entire script below:
    ```
    -- 1. Create a function that inserts a new row into public.profiles
    create or replace function public.handle_new_user()
    returns trigger
    language plpgsql
    security definer set search_path = public
    as $$
    begin
      insert into public.profiles (id, email)
      values (new.id, new.email);
      return new;
    end;
    $$;

    -- 2. Create the trigger that calls the function after a new user is created
    create trigger on_new_user_create_profile
      after insert on auth.users
      for each row execute procedure public.handle_new_user();
    ```
    * Click **"Run"**.

4.  **Set Your Site URL:**
    * Go to **Authentication -> URL Configuration** and set the **Site URL** to your app's deployment URL (e.g., `https://your-app-name.streamlit.app`)

5.  **Create Your Admin User:**
    * Go to **Authentication -> Users** and click **"Add User"**.
    * Enter the email and password you want to use for your admin account.
    * **Important:** After the user is created, copy their **User UUID**. You will need this for the security policies.

6.  **Enable and Configure Row Level Security (RLS):**
    * Go to **Authentication -> Policies** and enable RLS for the `entries`, `profiles`, `user_preferences`, and `recipes` tables.
    * Go to the **SQL Editor** and run the following script to create all the necessary policies.

    ```sql
    -- Policies for 'entries' table
    CREATE POLICY "Allow individual full access to entries" ON public.entries FOR ALL USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));

    -- Policies for 'user_preferences' table
    CREATE POLICY "Allow individual full access to preferences" ON public.user_preferences FOR ALL USING ((auth.uid() = id)) WITH CHECK ((auth.uid() = id));

    -- Policies for 'profiles' table
    CREATE POLICY "Allow users to read own profile" ON public.profiles FOR SELECT USING ((auth.uid() = id));
    CREATE POLICY "Allow master admin to read all profiles" ON public.profiles FOR SELECT USING ((auth.uid() = 'PASTE_YOUR_MASTER_USER_UUID_HERE'::uuid));
    CREATE POLICY "Allow master admin to update profiles" ON public.profiles FOR UPDATE USING ((auth.uid() = 'PASTE_YOUR_MASTER_USER_UUID_HERE'::uuid));

    -- Policies for 'recipes' table
    CREATE POLICY "Allow individual full access to own recipes" ON public.recipes FOR ALL USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));
    CREATE POLICY "Allow all users read access to public recipes" ON public.recipes FOR SELECT USING ((is_public = true));
    ```

7.  **Manually Approve Your Admin Account:**
    * Go to the **Table Editor** -> `profiles` table.
    * Find your master admin's row and change `is_approved` from `false` to `true`.

### 3. Local Code Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-folder>
    ```
2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Create the Secrets File:**
    * Create a folder named `.streamlit` in your project's root directory.
    * Inside that folder, create a file named `secrets.toml`.
    * Find the required credentials:
    1. URL: In your Supabase dashboard, find the URL in Project Settings -> Data API -> Project URL 
    2. KEY: Find the API Key in Project Settings -> API Keys -> Legacy API Keys (use the key labeled anon and public)
    3. MASTER_USER_ID
    * Add your Supabase credentials to this file:
        ```toml
        SUPABASE_URL = "https://<your-project-id>.supabase.co"
        SUPABASE_KEY = "your-anon-public-key"
        MASTER_USER_ID = "paste-your-admin-user-uuid-from-supabase-auth-here"
        ```
5.  **Run the Application:**
    ```bash
    streamlit run app.py
    ```

---

## Deployment

This application is ready to be deployed to Streamlit Community Cloud.

1.  Push your final code to a **public** GitHub repository. Ensure your `.gitignore` file is correctly configured to exclude your secrets.
2.  Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.
3.  Click **"New app"** and select your repository.
4.  In the **"Advanced settings"**, paste the contents of your `secrets.toml` file into the Secrets text box.
5.  Click **"Deploy"**.

---

## 🗺️ Future Roadmap

* **Multi-User Support:** Scale the application to allow multiple users to sign up and manage their own private nutrition logs. --DONE
* **Weight Tracking:** Add a new page and database table to track and visualize weight changes over time.
* **Workout Tracking:** Add a new page and database table to track and visualize workouts over time. Implement a feature to create a workout routine.
* **Meal Templates:** Implement a feature to save frequently eaten meals for quick one-click entry.
* **Barcode Scanner:** Add a new feature to scan a barcode and add the calories and macros as a meal.
* **Data Export:** Add a button to download all personal data as a CSV file for backup or external analysis.