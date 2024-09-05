import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Define the paths for data storage
user_csv_path = os.path.join(os.path.dirname(__file__), "users.csv")
transaction_csv_path = os.path.join(os.path.dirname(__file__), "transactions.csv")

# Function to load users
def load_users():
    try:
        users = pd.read_csv(user_csv_path)
    except FileNotFoundError:
        users = pd.DataFrame(columns=["Username", "Password"])
    return users

# Function to save users
def save_users(users):
    users.to_csv(user_csv_path, index=False)

# Function to load transactions
def load_transactions():
    try:
        transactions = pd.read_csv(transaction_csv_path)
    except FileNotFoundError:
        transactions = pd.DataFrame(columns=["Username", "Date", "Category", "Type", "Amount", "Notes"])
    return transactions

# Function to save transactions
def save_transactions(transactions):
    transactions.to_csv(transaction_csv_path, index=False)

# Function to authenticate users
def authenticate(username, password):
    users = load_users()
    user_row = users[(users["Username"] == username) & (users["Password"] == password)]
    return not user_row.empty

# Function to register new users
def register_user(username, password):
    users = load_users()
    if username in users["Username"].values:
        return False
    new_user = pd.DataFrame([{"Username": username, "Password": password}])
    users = pd.concat([users, new_user], ignore_index=True)
    save_users(users)
    return True

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'username' not in st.session_state:
    st.session_state.username = ""

# Login and Registration section
if not st.session_state.authenticated:
    st.title("Welcome to the Money Tracker App")

    menu = st.selectbox("Select an option", ["Login", "Register"])

    if menu == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success(f"Welcome, {username}!")
            else:
                st.error("Invalid username or password")

    elif menu == "Register":
        st.subheader("Create an Account")
        new_username = st.text_input("Choose a Username")
        new_password = st.text_input("Choose a Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if new_password != confirm_password:
                st.error("Passwords do not match!")
            elif len(new_username) == 0 or len(new_password) == 0:
                st.error("Username and password cannot be empty!")
            elif register_user(new_username, new_password):
                st.success("Account created successfully! Please log in.")
            else:
                st.error("Username already exists. Please choose another.")

# Main App Content (for logged-in users)
if st.session_state.authenticated:
    # Load user-specific transactions
    transactions = load_transactions()

    st.title("Personal Money Tracker")

    # Sidebar for adding new transactions
    st.sidebar.header(f"Welcome, {st.session_state.username}")
    st.sidebar.subheader("Add New Transaction")
    transaction_type = st.sidebar.selectbox("Transaction Type", ["Income", "Expense"])
    amount = st.sidebar.number_input("Amount", min_value=0.0, step=0.01)
    category = st.sidebar.text_input("Category", "")
    date = st.sidebar.date_input("Date", datetime.today())
    notes = st.sidebar.text_area("Notes", "")

    # Add transaction button
    if st.sidebar.button("Add Transaction"):
        if amount > 0 and category:
            new_transaction = {
                "Username": st.session_state.username,
                "Date": date.strftime("%Y-%m-%d"),
                "Category": category,
                "Type": transaction_type,
                "Amount": amount if transaction_type == "Income" else -amount,
                "Notes": notes,
            }
            transactions = pd.concat([transactions, pd.DataFrame([new_transaction])], ignore_index=True)
            save_transactions(transactions)
            st.sidebar.success("Transaction added successfully!")
        else:
            st.sidebar.error("Please fill in all the required fields.")

    # Display transactions filtered by the logged-in user
    st.subheader("Transaction History")
    user_transactions = transactions[transactions["Username"] == st.session_state.username].reset_index(drop=True)
    user_transactions.index += 1  # Start index from 1

    # Display transactions with edit/delete options
    if not user_transactions.empty:
        selected_action = st.selectbox("Select Action", ["View", "Edit", "Delete"], key="action_select")

        if selected_action == "Edit":
            transaction_index = st.number_input("Transaction Index to Edit", min_value=1, max_value=len(user_transactions), step=1, key="edit_index")
            transaction_to_edit = user_transactions.iloc[transaction_index - 1]

            st.write("### Edit Transaction")
            edit_date = st.date_input("Date", datetime.strptime(transaction_to_edit["Date"], "%Y-%m-%d"), key="edit_date")
            edit_category = st.text_input("Category", transaction_to_edit["Category"], key="edit_category")
            edit_type = st.selectbox("Type", ["Income", "Expense"], index=0 if transaction_to_edit["Type"] == "Income" else 1, key="edit_type")
            edit_amount = st.number_input("Amount", value=abs(transaction_to_edit["Amount"]), step=0.01, key="edit_amount")
            edit_notes = st.text_area("Notes", transaction_to_edit["Notes"], key="edit_notes")

            if st.button("Save Changes"):
                transactions.loc[transactions.index == transaction_to_edit.name, "Date"] = edit_date.strftime("%Y-%m-%d")
                transactions.loc[transactions.index == transaction_to_edit.name, "Category"] = edit_category
                transactions.loc[transactions.index == transaction_to_edit.name, "Type"] = edit_type
                transactions.loc[transactions.index == transaction_to_edit.name, "Amount"] = edit_amount if edit_type == "Income" else -edit_amount
                transactions.loc[transactions.index == transaction_to_edit.name, "Notes"] = edit_notes
                save_transactions(transactions)
                st.success("Transaction updated successfully!")

        elif selected_action == "Delete":
            transaction_index = st.number_input("Transaction Index to Delete", min_value=1, max_value=len(user_transactions), step=1, key="delete_index")
            transaction_to_delete = user_transactions.iloc[transaction_index - 1]

            if st.button("Delete Transaction"):
                transactions = transactions.drop(transaction_to_delete.name)
                save_transactions(transactions)
                st.success("Transaction deleted successfully!")

    st.dataframe(user_transactions)

    # Summary of income and expenses for the logged-in user
    income = user_transactions[user_transactions["Type"] == "Income"]["Amount"].sum()
    expenses = user_transactions[user_transactions["Type"] == "Expense"]["Amount"].sum()
    balance = income + expenses

    st.subheader("Summary")
    st.write(f"*Total Income:* ${income:.2f}")
    st.write(f"*Total Expenses:* ${-expenses:.2f}")
    st.write(f"*Balance:* ${balance:.2f}")

    # Warning if balance is negative
    if balance < 0:
        st.warning("Warning: You have spent more than you have! Your balance is negative.")

    # Option to clear all transactions
    if st.button("Clear All Transactions"):
        transactions = transactions[transactions["Username"] != st.session_state.username]
        save_transactions(transactions)
        st.success("All transactions cleared!")

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.sidebar.info("Logged out successfully.")