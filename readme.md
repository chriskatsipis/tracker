# 🥗 Python Nutrition Tracker

A secure, deployable web application built with Streamlit and Supabase to track daily nutritional intake, including calories and macronutrients. This app features a public, view-only mode for guests and a secure, admin-only mode for data entry and management.

---

## Core Features

* **Daily Food Logging:** Log meals with descriptions, calories, protein, carbs, and fats.
* **Customizable Daily Goals:** Set default goals and override them for specific days (e.g., workout vs. rest days).
* **Historical Goal Tracking:** Each meal entry stores the goal that was active at the time, ensuring analytics are always accurate.
* **Interactive Meal Management:** A single, intuitive data editor allows the admin to add, update, and delete entries on both desktop and mobile.
* **Rich Analytics Dashboard:** Visualize progress with interactive time-series charts comparing daily intake vs. goals for calories, protein, carbs, and fats.
* **Secure Admin/Guest Access:**
    * **Guest Mode:** Publicly accessible, view-only dashboard. Guests cannot modify any data.
    * **Admin Mode:** Requires secure login. The admin has full control to add, edit, and delete all data.
* **API Overload Protection:** Implements server-side caching to protect against denial-of-service attacks and conserve free-tier API limits.

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
        * `id` (int8) - *Is Primary Key*
        * `entry_date` (date)
        * `description` (text)
        * `calories` (int4)
        * `protein` (int4)
        * `carbs` (int4)
        * `fats` (int4)
        * `goal_calories` (int4)
        * `goal_protein` (int4)
        * `goal_carbs` (int4)
        * `goal_fats` (int4)
3.  **Create the `user_id` Column:**
    * After the table is created, click **"Add column"**.
    * **Name:** `user_id`
    * **Type:** `uuid`
    * **Important:** Uncheck **"Allow Nullable"**.
    * Leave all other settings as default and save.
4.  **Create Your Admin User:**
    * Go to **Authentication -> Users** and click **"Add User"**.
    * Enter the email and password you want to use for your admin account.
    * **Important:** After the user is created, copy their **User UUID**. You will need this for the security policies.
5.  **Enable Row Level Security (RLS):**
    * Go to **Authentication -> Policies**.
    * Select the `entries` table and click **"Enable RLS"**.
    * **Policy 1: Allow Public Read Access**

        * Click **"New Policy" -> "Create a new policy from scratch"**.

        * **Policy Name:** `Allow public read-only access`

        * **Policy command:** `SELECT`

        * **USING expression:** Copy and paste `true` into the `USING` field.

        * Save the policy.

    * **Policy 2: Allow Admin Full Access**

        * Click **"New Policy" -> "Create a new policy from scratch"**.

        * **Policy Name:** `Allow admin full access`

        * **Policy command:** `ALL`

        * Tick the **"use the WITH CHECK expression"** box.

        * **USING expression:** `auth.uid() = 'PASTE_YOUR_ADMIN_USER_UUID_HERE'`

        * **WITH CHECK expression:** `auth.uid() = 'PASTE_YOUR_ADMIN_USER_UUID_HERE'`

        * Save the policy.

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
    * Add your Supabase credentials to this file:
        ```toml
        SUPABASE_URL = "https://<your-project-id>.supabase.co"
        SUPABASE_KEY = "your-anon-public-key"
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