import streamlit as st
from conn import MySQLDatabase
from menu import menu
import hashlib

st.set_page_config(page_title="Manage Users", page_icon="👥")

# ---- Auth guard ----
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")
    st.stop()
else:
    menu()

db = MySQLDatabase()

# Optional: enforce admin-only access if you store is_admin in session_state on login
# if not st.session_state.get("is_admin", False):
#     st.error("Admins only.")
#     st.stop()

st.title("👥 Manage Users")

# ----------------------------
# VIEW USERS
# ----------------------------
with st.expander("📋 View Users", expanded=True):
    users_df = db.fetch_all_users()
    if users_df.empty:
        st.info("No users found.")
    else:
        st.dataframe(users_df, use_container_width=True)

st.divider()

# ----------------------------
# ADD USER
# ----------------------------
st.subheader("➕ Add User")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    new_username = st.text_input("Username", key="mu_new_username")
with col2:
    new_password = st.text_input("Password", type="password", key="mu_new_password")
with col3:
    new_is_admin = st.checkbox("Admin", key="mu_new_is_admin")

if st.button("Create User", type="primary"):
    if not new_username.strip():
        st.error("Username is required.")
    elif not new_password or len(new_password) < 6:
        st.error("Password must be at least 6 characters.")
    elif db.username_exists(new_username.strip()):
        st.error("Username already exists.")
    else:
        user_id = db.create_user(new_username.strip(), new_password, int(new_is_admin))
        if user_id:
            st.success(f"User created (ID: {user_id}).")
            st.rerun()
        else:
            st.error("Failed to create user.")

st.divider()

# ----------------------------
# EDIT USER (username/admin)
# ----------------------------
st.subheader("✏️ Edit User")

users_df = db.fetch_all_users()
if users_df.empty:
    st.info("No users available to edit.")
else:
    # pick a user by id
    user_ids = users_df["id"].tolist()
    selected_id = st.selectbox("Select User ID", user_ids, key="mu_edit_user_id")

    row = users_df[users_df["id"] == selected_id].iloc[0]
    edit_username = st.text_input("Username", value=row["username"], key="mu_edit_username")
    edit_is_admin = st.checkbox("Admin", value=bool(row["is_admin"]), key="mu_edit_is_admin")

    if st.button("Save Changes"):
        if not edit_username.strip():
            st.error("Username is required.")
        elif db.username_exists(edit_username.strip(), exclude_id=int(selected_id)):
            st.error("That username is already taken.")
        else:
            ok = db.update_user(int(selected_id), edit_username.strip(), int(edit_is_admin))
            if ok:
                st.success("User updated.")
                st.rerun()
            else:
                st.error("Failed to update user.")

st.divider()

# ----------------------------
# RESET PASSWORD
# ----------------------------
st.subheader("🔁 Reset Password")

users_df = db.fetch_all_users()
if users_df.empty:
    st.info("No users available.")
else:
    user_ids = users_df["id"].tolist()
    reset_id = st.selectbox("User ID", user_ids, key="mu_reset_user_id")

    pw1 = st.text_input("New Password", type="password", key="mu_reset_pw1")
    pw2 = st.text_input("Confirm New Password", type="password", key="mu_reset_pw2")

    if st.button("Reset Password"):
        if not pw1 or len(pw1) < 6:
            st.error("Password must be at least 6 characters.")
        elif pw1 != pw2:
            st.error("Passwords do not match.")
        else:
            ok = db.reset_password(int(reset_id), pw1)
            if ok:
                st.success("Password reset successfully.")
            else:
                st.error("Failed to reset password.")

st.divider()

# ----------------------------
# DELETE USER
# ----------------------------
st.subheader("🗑️ Delete User")

users_df = db.fetch_all_users()
if users_df.empty:
    st.info("No users available.")
else:
    user_ids = users_df["id"].tolist()
    del_id = st.selectbox("User ID to delete", user_ids, key="mu_delete_user_id")

    # Optional: prevent deleting yourself if you store current user id in session_state
    # if del_id == st.session_state.get("user_id"):
    #     st.warning("You cannot delete your own account.")

    confirm = st.checkbox("I understand this will permanently delete the user.", key="mu_delete_confirm")

    if st.button("Delete User", disabled=not confirm):
        ok = db.delete_user(int(del_id))
        if ok:
            st.success("User deleted.")
            st.rerun()
        else:
            st.error("Failed to delete user.")
