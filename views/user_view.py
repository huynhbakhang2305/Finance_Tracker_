from database.user_model import UserModel
import streamlit as st
import time


def render_user_profile(user_model: UserModel, user: dict[str, any]):
    """
    Render a modern, compact user profile section in the sidebar.
    Layout: [avatar] [name/email] [dropdown menu]
    """
    if 'user_settings_open' not in st.session_state:
        st.session_state['user_settings_open'] = False

    # Create a more compact profile container
    with st.sidebar:
        st.divider()
        
        col1, col2, col3 = st.columns([0.8, 3.2, 0.8], gap="small")
        
        with col1:
            avatar_url = user.get("picture")
            if avatar_url:
                st.image(avatar_url, width=40)
            else:
                st.write("👤")
        
        with col2:
            name = user.get("given_name") or user.get("name") or "User"
            email = user.get("email") or ""
            st.markdown(f"<div style='margin-top: 8px;'><span style='font-weight: 600; font-size: 14px;'>{name}</span></div>", unsafe_allow_html=True)
            if email:
                st.caption(f"📧 {email}")
        
        with col3:
            if st.button("⚙️", key="settings_toggle", help="Settings"):
                st.session_state['user_settings_open'] = not st.session_state['user_settings_open']
        
        if st.session_state['user_settings_open']: # is True
            _render_user_settings(user_model, user.get("id"))
        
        st.divider()


def _render_user_settings(user_model, user_id: str):
    """
    Render user settings options with better styling.
    """
    st.markdown("**⚙️ Settings**")
    
    col1, col2 = st.columns(2, gap="small")
    
    with col1:
        if st.button("🚪 Log out", use_container_width=True, key="logout_button"):
            st.logout()
    
    with col2:
        if st.button("❌ Deactivate", use_container_width=True, key="deactivate_button"):
            if user_id:
                user_model.deactivate_user(user_id)
                st.success("Account deactivated. Goodbye!")
                time.sleep(1)
                st.logout()
                st.rerun()
            else:
                st.error("Unable to determine user id.")
    
    st.caption("_Account settings_")