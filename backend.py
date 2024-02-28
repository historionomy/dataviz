from supabase import create_client, Client
import pandas as pd
import streamlit as st
import bcrypt
import jwt

def login(username, password):

    # Initialize Supabase client
    url: str = st.secrets["SUPABASE_PROJECT_URL"]
    key: str = st.secrets["SUPABASE_PROJECT_API_KEY"]
    supabase: Client = create_client(url, key)

    # Attempt to log in with provided credentials
    try:
        auth_response = supabase.auth.sign_in_with_password(
            {
                "email": username,
                "password": password
            }
        )

    except :
        print("Login error : invalid credentials")
        return None, "Invalid credentials"
    res = supabase.auth.get_session()

    jwt_token = res.access_token

    return jwt_token, None

def insert_data(token, table_name, data):

    # Initialize Supabase client
    url: str = st.secrets["SUPABASE_PROJECT_URL"]
    key: str = st.secrets["SUPABASE_PROJECT_API_KEY"]
    supabase: Client = create_client(url, key)

    # Set the Supabase client to use the provided auth token
    supabase.auth.session = supabase.auth.Session(access_token=token, token_type="bearer", user=None, expires_in=None)

    # Perform an insert operation
    response = supabase.table(table_name).insert(data).execute()

    # Reset the auth session (optional, for security)
    supabase.auth.session = None

    # Check if the insert was successful
    if response.error:
        return False, response.error.message
    else:
        return True, "Data inserted successfully"

def load_data_connected(token, table_name):

    # Initialize Supabase client
    url: str = st.secrets["SUPABASE_PROJECT_URL"]
    key: str = st.secrets["SUPABASE_PROJECT_API_KEY"]
    supabase: Client = create_client(url, key)

    # Set the Supabase client to use the provided auth token
    supabase.auth.session = supabase.auth.Session(access_token=token, token_type="bearer", user=None, expires_in=None)

    data = supabase.table(table_name).select("*").execute()

    return data

def load_data(table_name):

    # Initialize Supabase client
    url: str = st.secrets["SUPABASE_PROJECT_URL"]
    key: str = st.secrets["SUPABASE_PROJECT_API_KEY"]
    supabase: Client = create_client(url, key)

    offset = 0
    limit = 1000  # or any other chunk size that works for your application
    all_records = []

    while True:
        response = supabase.table(table_name).select("*").range(offset, offset + limit - 1).execute()
        data = response.data
        if not data:
            break  # Break the loop if no more records are returned
        all_records.extend(data)
        offset += limit

    data = pd.DataFrame(all_records)

    return data

def load_data_debug(table_name):

    df = pd.read_csv("../data-tooling/" + table_name + ".csv", header=0)
    # remove whitespaces in column names and cast to lowercase
    df.columns = df.columns.str.replace(' ', '_')
    df.columns = df.columns.str.lower()
    # Add "step_" to column names that are numerical values
    df.columns = [f'step_{col}' if col.isdigit() else col for col in df.columns]
    return df