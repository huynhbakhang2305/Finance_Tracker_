import streamlit as st
import config

# function to render category list
def _render_category_list(category_model, category_type: str):
    st.subheader(f"{category_type} Categories")
    expense_lst = category_model.get_categories_by_type(category_type = category_type)

    if expense_lst:
        st.write(f"Total: {len(expense_lst)} categories")
        st.write("")

        cols = st.columns(3)

        for idx, item in enumerate(expense_lst):
            col_idx = idx % 3 # remaining fraction

            with cols[col_idx]:
                with st.container():
                    subcol_a, subcol_b = st.columns([4, 1])

                    with subcol_a:
                        st.write(f"📌{item.get("name")}")
                        st.caption(f"{item.get("created_at").strftime("%d-%m-%Y")}")

                    with subcol_b:
                        
                        delete_button = st.button("❌", key=f"del_{item['_id']}")
                        if delete_button:
                            # Count affected transactions
                            trans_col = category_model.db_manager.get_collection(
                                config.COLLECTIONS["transaction"]
                            )

                            affected = trans_col.count_documents({
                                "user_id": category_model.user_id,
                                "category": item.get("name")
                            })

                            st.warning(f"⚠️ {affected} transactions will be affected")

                            strategy = st.radio(
                                "Choose delete strategy",
                                ["reassign", "cascade", "block"],
                                key=f"strategy_{item['_id']}"
                            )

                            confirm = st.button(
                                "Confirm delete",
                                key=f"confirm_{item['_id']}"
                            )

                            if confirm:
                                try:
                                    category_model.delete_category_safe(
                                        category_type=item.get("type"),
                                        category_name=item.get("name"),
                                        strategy=strategy
                                    )
                                    st.success(f"✅ Deleted category '{item.get('name')}'")
                                    st.rerun()
                                except ValueError as e:
                                    st.error(str(e))


def _render_category_detail(category_model):
    st.subheader("Category detail")
    tab1, tab2 = st.tabs(config.TRANSACTION_TYPES)

    with tab1:
        _render_category_list(category_model, "Expense")

    with tab2:
        _render_category_list(category_model, "Income")

#TODO
def _render_add_category(category_model):
    st.subheader("Add category")
    with st.form("add_category_name"):
        col1, col2, col3 = st.columns([2, 2, 1]) # col1 and col2 is double size of col1

    # category type
    with col1:
        category_type = st.selectbox(
            "Category Type",
            config.TRANSACTION_TYPES # ["Expense", "Income"]
        )
    
    # category input
    with col2:
        category_name = st.text_input(
            "Category Name",
            placeholder="e.g., Groceries, Rent, Bonus"
        )
    
    with col3:
        st.write("")  # Spacing
        st.write("")
        submitted = st.form_submit_button("Submit", use_container_width=True)
    
    if submitted:
        if not category_name:
            st.error("❌ Please enter a category name")
        elif not category_type:
            st.error("❌ Please choose a category type")          
        else:
            result = category_model.upsert_category(category_type = category_type, category_name = category_name)
            if result:
                st.success(f"✅ Category '{category_name}' added successfully!")
                st.balloons()
                st.rerun()  # Refresh the page to show new category
            else:
                st.error("❌ Error adding category")


# public function
def render_categories(category_model):
    st.title("🏷️ Category Management")

    # Display existing category list
    _render_category_detail(category_model)

    st.divider()

    # Add category section
    _render_add_category(category_model)