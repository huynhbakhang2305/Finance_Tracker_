import streamlit as st
import config
from datetime import date, datetime, timedelta
import time
from utils import handler_datetime, format_currency, format_date

from database import TransactionModel

# ======================================
# supporting functions
# ======================================

# I want to clarify the model type so I can use its methods,
# that is why I am importing TransactionModel above.
# and annotating the parameter type in the functions below.
# NOTE: This is just for type hinting and does not affect runtime.
# you can simply use 'model' without type hinting if you prefer.
# e.g., def render_transaction_card(model, item):


def _render_transaction_card(model: TransactionModel, item: dict):
    """Render a single transaction as an expandable card."""
    # Format the header
    transaction_type = item.get('type', 'Unknown')
    amount = item.get('amount', 0)
    date = item.get('date', datetime.now())
    category = item.get('category', 'Others')
    
    # Color coding
    type_color = "🔴" if transaction_type == "Expense" else "🟢"
    amount_str = f"${amount:,.2f}"
    date_str = format_date(date)
    
    # Create expander header
    header = f"{type_color} {date_str} | {category} | {amount_str}"
    
    with st.expander(header, expanded=False):
        # Display transaction details
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Type:**", transaction_type)
            st.write("**Category:**", category)
            st.write("**Amount:**", amount_str)
        
        with col2:
            st.write("**Date:**", date_str)
            if item.get('description'):
                st.write("**Description:**", item['description'])
            if item.get('last_modified'):
                modified = item['last_modified']
                modified_str = format_date(modified)
                st.write("**Last Modified:**", modified_str)
        
        # Action buttons
        st.divider()
        col_edit, col_delete, col_space = st.columns([1, 1, 3])
        
        with col_edit:
            if st.button("✏️ Edit", key=f"edit_{item['_id']}", use_container_width=True):
                st.session_state.editing_transaction = str(item['_id'])
                st.rerun()
        
        with col_delete:
            if st.button("🗑️ Delete", key=f"delete_{item['_id']}", use_container_width=True, type="primary"):
                if model.delete_transaction(str(item['_id'])):
                    st.success("Transaction deleted successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to delete transaction")

def _render_filters(model: TransactionModel):
    """Render filter controls."""
    st.subheader("🔍 Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        transaction_type = st.selectbox(
            "Transaction Type",
            options=config.TRANSACTION_TYPES,
            key="filter_type"
        )
        
        min_amount = st.number_input(
            "Min Amount",
            min_value=0.1,
            value=1.0,
            step=10.0,
            key="filter_min_amount"
        )
        
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30), # default back to 30 days from today
            key="filter_start_date"
        )
    
    with col2:
        category = st.text_input(
            "Category (regex match)",
            key="filter_category"
        )
        
        max_amount = st.number_input(
            "Max Amount",
            min_value=0.1,
            value=1.0,
            step=10.0,
            key="filter_max_amount"
        )
        
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            key="filter_end_date"
        )
    
    search_text = st.text_input(
        "Search in Description",
        key="filter_search_text"
    )
    
    # Filter action buttons
    col_apply, col_clear = st.columns(2)
    
    with col_apply:
        if st.button("✅ Apply Filters", use_container_width=True, type="primary"):
            # Build filter dictionary
            filters = {}
            
            if transaction_type:
                filters['transaction_type'] = transaction_type
            
            if category:
                filters['category'] = category
            
            if min_amount > 0:
                filters['min_amount'] = min_amount
            
            if max_amount > 0:
                filters['max_amount'] = max_amount
            
            if start_date:
                filters['start_date'] = start_date
            
            if end_date:
                filters['end_date'] = end_date
            
            if search_text:
                filters['search_text'] = search_text
            
            st.session_state.active_filters = filters if filters else None
            st.rerun()
    
    with col_clear:
        if st.button("🔄 Clear Filters", use_container_width=True):
            st.session_state.active_filters = None
            st.session_state.show_filters = False
            st.rerun()

# This function I left category_model untyped
# because I don't have the CategoryModel imported here.
# and you can see it still works fine without type hinting.
def _render_create_transaction_form(transaction_model: TransactionModel, category_model):
    """Render create transaction form."""
    st.subheader("➕ Create New Transaction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        transaction_type = st.selectbox(
            "Type *",
            options=config.TRANSACTION_TYPES,
            key="create_type"
        )
        
        amount = st.number_input(
            "Amount *",
            min_value=0.1,
            value=1.0,
            step=1.0,
            format="%.2f",
            key="create_amount"
        )
        
        date = st.date_input(
            "Date *",
            value=datetime.now(),
            key="create_date"
        )
    
    with col2:
        if transaction_type:
            categories_result = category_model.get_categories_by_type(transaction_type)
            category_options = [cate['name'] for cate in categories_result]
            category = st.selectbox(
                "Category *",
                options=category_options,
                key="create_category"
            )
        
        description = st.text_area(
            "Description",
            key="create_description",
            placeholder="Optional notes about this transaction"
        )
    
    # Action buttons
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button("💾 Save Transaction", use_container_width=True, type="primary"):
            # Validation
            if not category:
                st.error("Category is required")
                return
            
            if amount <= 0:
                st.error("Amount must be greater than 0")
                return
            
            # Create transaction
            transaction_date = datetime.combine(date, datetime.now().time())
            transaction_id = transaction_model.add_transaction(
                transaction_type=transaction_type,
                category=category,
                amount=amount,
                transaction_date=transaction_date,
                description=description
            )
            
            if transaction_id:
                st.success(f"✅ Transaction created successfully!")
                st.session_state.show_create_form = False
                st.rerun()
            else:
                st.error("❌ Failed to create transaction")
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_create_form = False
            st.rerun()

def initialize_session_state():
    """Initialize session state variables for transaction view."""
    if 'show_filters' not in st.session_state:
        st.session_state.show_filters = False
    if 'active_filters' not in st.session_state:
        st.session_state.active_filters = None
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False

# ======================================
# function render list of transactions
# ======================================
def _render_list_transaction(transaction_model: TransactionModel):
    # Fetch transactions with load more approach
    transactions = transaction_model.get_transactions(
        advanced_filters=st.session_state.active_filters
    )
        
    # Display transactions
    if not transactions:
        st.info("No transactions found. Add your first transaction to get started!")
    else:
        for item in transactions:
            _render_transaction_card(transaction_model, item)


# ======================================
# function render main view
# ======================================

def render_transactions(transaction_model, category_model):
    """Main function to render the transaction view."""

    initialize_session_state()
    # Check if transaction model has user_id set
    
    if not getattr(transaction_model, 'user_id', None): # if transaction_model attributes has no user_id
        st.warning("Please log in to view your transactions.")
        return # exist the function early
    
    # Header with CREATE button
    col_title, col_create, col_filter = st.columns([3, 1, 1])
    
    with col_title:
        st.title("📊 Transactions")
    
    with col_create:
        if st.button("➕ CREATE", use_container_width=True, type="primary"):
            st.session_state.show_create_form = not st.session_state.show_create_form # negate the boolean value
            st.rerun()
    
    with col_filter:
        if st.button("🔍 Filters", use_container_width=True):
            st.session_state.show_filters = not st.session_state.show_filters # negate the boolean value
            st.rerun()
    
    # Show create form if toggled
    if st.session_state.show_create_form:
        with st.container():
            _render_create_transaction_form(transaction_model, category_model)
        st.divider()
    
    # Show filters if toggled
    if st.session_state.show_filters:
        with st.container():
            _render_filters(transaction_model)
        st.divider()
    
    # Display active filter info
    if st.session_state.active_filters:
        filter_count = len(st.session_state.active_filters)
        st.info(f"🔍 {filter_count} filter(s) active")

    # Render list of transactions
    _render_list_transaction(transaction_model)