# 🥗 Python Nutrition Tracker

A secure, deployable web application built with Streamlit and Supabase to track daily nutritional intake, including calories and macronutrients. This app features a public, view-only mode for guests and a secure, admin-only mode for data entry and management.

---

## Core Features

* **Secure Multi-User Accounts:** Users can request an account and, upon admin approval, manage their own private nutrition log.
* **Admin Approval Panel:** A special master admin user can view and approve pending account requests.
* **Daily Food Logging:** Log meals with descriptions, calories, protein, carbs, and fats.
* **Customizable Daily Goals:** Set persistent default goals and override them for specific days.
* **API Rate Limiting:** Protects the app by limiting non-admin users to 50 database writes per day.
* **Rich Analytics Dashboard:** Each user can visualize their own progress with interactive charts comparing daily intake vs. goals.

---

## How to Use the App

The application has two distinct user roles.

### As a User

1.  Navigate to the application URL.
2.  In the sidebar, use the **"Sign Up"** tab to request an account. You will also need to verify your email address.
3.  Once the administrator approves your account, you can log in using the **"Login"** tab.
4.  You now have full access to manage your own data:
    * **Set Default Goals:** Change your macro targets in the sidebar and click "Save Default Goals".
    * **Set Goals for a Specific Day:** Use the "Set / Edit Goals" section on the Daily Log.
    * **Manage Meals:** Use the interactive table on the "Daily Log" page to add, edit, or delete your meal entries for any date.

### As the Administrator

1.  Log in with the master admin account credentials.
2.  You have all the same permissions as a regular user to track your own nutrition.
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

2.  **Create the `entries` Table:**
    * Go to the **Table Editor** and click **"Create a new table"**.
    * Name the table `entries`.
    * **Important:** Uncheck "Enable Row Level Security (RLS)" for now. We will enable it later.
    * Add the following columns with the specified types:
        * `id` (int8) *settings: 'is unique', 'is identity'*
        * `entry_date` (date) *settings: uncheck all, no default value*
        * `description` (text) *settings: uncheck all, no default value*
        * `calories` (int4) *settings: uncheck all, no default value*
        * `protein` (int4) *settings: uncheck all, no default value*
        * `carbs` (int4) *settings: uncheck all, no default value*
        * `fats` (int4) *settings: uncheck all, no default value*
        * `goal_calories` (int4) *settings: uncheck all, no default value*
        * `goal_protein` (int4) *settings: uncheck all, no default value*
        * `goal_carbs` (int4) *settings: uncheck all, no default value*
        * `goal_fats` (int4) *settings: uncheck all, no default value*
        * `user_id` (uuid) *settings: uncheck all, no default value*

3.  **Create the `profiles` Table:**
    * Click **"Create a new table"** again.
    * Name the table `profiles`. Uncheck "Enable Row Level Security (RLS)" for now.
    * Add the following columns:
        * `id` (uuid) *settings: uncheck all, no default value*
        * `email` (text) *settings: 'is nullable', uncheck all else, no default value*
        * `is_approved` (bool) *settings: uncheck all, default: 'false'*
        * `api_call_count` (int4) *settings: uncheck all, default: '0'*
        * `last_api_call_date` (date) *settings: 'is nullable', uncheck all else, no default value*
    * **Add a Foreign Key:** Click the "link" icon next to the `id` column and add a foreign key relation to `id` -> `auth.users`.

4.  **Create the `user_preferences` Table:**
    * Go to the **Table Editor** and click **"Create a new table"**.
    * Name the table `user_preferences`. Uncheck "Enable Row Level Security (RLS)" for now.
    * Add the following columns:
        * `user_id` (uuid) **settings:** Make it the **Primary Key**.
        * `default_calories` (int4)
        * `default_protein` (int4)
        * `default_carbs` (int4)
        * `default_fats` (int4)
    * **Add a Foreign Key:** Click the "link" icon next to the `user_id` column and add a foreign key relation to `user_id` -> `auth.users`.

5.  **Create the Database Trigger to automatically create a profile for each new user:**
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

6.  **Set Your Site URL:**
    * Go to **Authentication -> URL Configuration** and set the **Site URL** to your app's deployment URL (e.g., `https://your-app-name.streamlit.app`)

7.  **Create Your Admin User:**
    * Go to **Authentication -> Users** and click **"Add User"**.
    * Enter the email and password you want to use for your admin account.
    * **Important:** After the user is created, copy their **User UUID**. You will need this for the security policies.

8.  **Enable and Configure Row Level Security (RLS):**
    * Go to **Authentication -> Policies** and enable RLS for the `entries`, `profiles`, and `user_preferences` tables.
    * You will now create 5 policies in total.

    * **Policy for `entries` Table:**
        * **Name:** `Allow individual full access on entries`
        * **Operation:** `ALL`
        * **USING expression:** `auth.uid() = user_id`
        * **WITH CHECK expression:** `auth.uid() = user_id`

    * **Policy for `user_preferences` Table:**
        * **Name:** `Allow individual full access on preferences`
        * **Operation:** `ALL`
        * **USING expression:** `auth.uid() = user_id`
        * **WITH CHECK expression:** `auth.uid() = user_id`

    * **Policies for `profiles` Table (Create 3 separate policies):**
        * **Policy 1 (Read Self):** Name: `Allow users to read their own profile`, Operation: `SELECT`, USING expression: `auth.uid() = id`
        * **Policy 2 (Admin Read All):** Name: `Allow master admin to read all profiles`, Operation: `SELECT`, USING expression: `auth.uid() = 'PASTE_YOUR_MASTER_USER_UUID_HERE'`
        * **Policy 3 (Admin Update):** Name: `Allow master admin to update profiles`, Operation: `UPDATE`, USING expression: `auth.uid() = 'PASTE_YOUR_MASTER_USER_UUID_HERE'`
        
9.  **Manually Approve Your Admin Account:**
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

* **Multi-User Support:** Scale the application to allow multiple users to sign up and manage their own private nutrition logs.
* **Weight Tracking:** Add a new page and database table to track and visualize weight changes over time.
* **Workout Tracking:** Add a new page and database table to track and visualize workouts over time. Implement a feature to create a workout routine.
* **Meal Templates:** Implement a feature to save frequently eaten meals for quick one-click entry.
* **Data Export:** Add a button to download all personal data as a CSV file for backup or external analysis.