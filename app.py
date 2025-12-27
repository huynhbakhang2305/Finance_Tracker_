import streamlit as st
import config
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json

# import model
from database import (
    CategoryModel,
    TransactionModel,
    UserModel,
)

# import analytics
from analytics.analyzer import FinanceAnalyzer
from analytics.visualize import FinanceVisualizer

# import view module
from views import (
    render_categories,
    render_transactions,
    render_user_profile,
    render_dashboard
)

# initialize models
@st.cache_resource
def init_models():
    """Initialize and cached models"""
    return {
        "category": CategoryModel(),
        "transaction": TransactionModel(),
        "user": UserModel(),
        "visualizer": FinanceVisualizer()
    }

# initialize session per user
if "models" not in st.session_state:
    # initialize models
    st.session_state['models'] = init_models()


models = st.session_state['models']

# Page configuration
st.set_page_config(
    page_title = "Finance Tracker",
    page_icon = "🤑",
    layout = "wide"
)

# =============================================
# Google OAuth Setup
# =============================================

GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]

def login_with_google():
    """Khởi tạo Google OAuth flow"""
    flow = Flow.from_client_config(
        {
            "installed": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        },
        scopes=['https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile']
    )
    
    flow.redirect_uri = REDIRECT_URI
    authorization_url, state = flow.authorization_url()
    
    return authorization_url, state, flow

def login_screen():
    """Hiển thị màn hình login"""
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.header("🔐 Finance Tracker")
            st.subheader("Please login to continue")
            
            if st.button("🔵 Login with Google", use_container_width=True):
                auth_url, state, flow = login_with_google()
                st.session_state['auth_state'] = state
                st.session_state['auth_flow'] = flow
                st.markdown(f'<a href="{auth_url}" target="_blank">Click here if not redirected</a>', 
                           unsafe_allow_html=True)
                st.stop()

# =============================================
# 1. Authen User
# =============================================

# Kiểm tra xem user đã login hay chưa
if "google_user" not in st.session_state:
    st.session_state.google_user = None

# Nếu chưa login
if st.session_state.google_user is None:
    login_screen()
    st.stop()

# User đã login - Lấy thông tin từ session
google_user = st.session_state.google_user

# =============================================
# Login với MongoDB
# =============================================

user_model: UserModel = models['user']
try:
    mongo_user_id = user_model.login(google_user['email'])
except Exception as e:
    st.error(f"❌ Error during user login: {e}")
    st.stop()

# Set user_id cho models
models['category'].set_user_id(mongo_user_id)
models['transaction'].set_user_id(mongo_user_id)

# Tạo user dict
user = {
    "email": google_user['email'],
    "name": google_user.get('name', 'User'),
    "picture": google_user.get('picture', ''),
    "id": mongo_user_id
}

# =============================================
# Sidebar - User Profile & Logout
# =============================================

with st.sidebar:
    st.divider()
    col1, col2 = st.columns([1, 3])
    with col1:
        if user['picture']:
            st.image(user['picture'], width=50)
    with col2:
        st.write(f"**{user['name']}**")
        st.caption(user['email'])
    
    if st.button("🚪 Logout"):
        st.session_state.google_user = None
        st.rerun()
    
    st.divider()

    # Display user profile after update user with mongo_user_id
    render_user_profile(user_model, user)

    # init analyzer
    # because transaction_model has set user_id already in line 74
    analyzer_model = FinanceAnalyzer(models['transaction'])

    # =============================================
    # 2. Navigation
    # =============================================

    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Category", "Transaction"]
    )

    # =============================================
    # 3. Router
    # =============================================
    if page == "Home":
        st.title("Home")
        render_dashboard(analyzer_model=analyzer_model, 
                        transaction_model=models['transaction'],
                        visualizer_model=models["visualizer"])

    elif page == "Category":
        # get category_model from models
        category_model = models['category']

        # display category views
        render_categories(category_model=category_model)

    elif page == "Transaction":
        # get category_model and transaction from models
        category_model = models['category']
        transaction_model = models['transaction']

        # display transaction views
        render_transactions(transaction_model=transaction_model, category_model=category_model)

    
