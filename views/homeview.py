import streamlit as st
import pandas as pd
from utils import format_currency, get_date_range_options
from analytics.analyzer import FinanceAnalyzer
from database import TransactionModel
from analytics.visualize import FinanceVisualizer

def render_dashboard(analyzer_model: FinanceAnalyzer, 
                    transaction_model: TransactionModel,
                    visualizer_model: FinanceVisualizer):
    """
    Render the main financial dashboard
    
    Args:
        analyzer_model: FinanceAnalyzer
        visualizer_model: FinanceVisualizer
        transaction_model: TransactionModel
    """
    st.title("📊 Financial Dashboard")
    
    # Date range selector
    col1, _ = st.columns([2, 1])
    with col1:
        date_range_option = st.selectbox(
            "Select Date Range",
            list(get_date_range_options().keys()),
            index=3  # Default to "Last 30 Days"
        )
    
    date_ranges = get_date_range_options() #> return dictionary
    start_date, end_date = date_ranges[date_range_option]

    # Display metrics section
    _render_metrics(analyzer_model, start_date, end_date)
    
    st.divider()
    
    # Display charts section
    _render_charts(analyzer_model, visualizer_model, start_date, end_date)
    
    # # Display recent transactions
    # _render_recent_transactions(transaction_model)


def _render_metrics(analyzer_model: FinanceAnalyzer, start_date, end_date):
    """Render the metrics cards at the top of dashboard"""
    # Get statistics
    if start_date and end_date:
        total_expenses = analyzer_model.calculate_total_by_type("Expense", start_date, end_date)
        total_income = analyzer_model.calculate_total_by_type("Income", start_date, end_date)
    else:
        total_expenses = analyzer_model.calculate_total_by_type("Expense")
        total_income = analyzer_model.calculate_total_by_type("Income")
    
    net_balance = total_income - total_expenses
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💸 Total Expenses", format_currency(total_expenses))
    
    with col2:
        st.metric("💰 Total Income", format_currency(total_income))
    
    with col3:
        delta_color = "normal" if net_balance >= 0 else "inverse"
        st.metric("📈 Net Balance", 
                  format_currency(net_balance), 
                  delta_color=delta_color)
    
    with col4:
        daily_avg = analyzer_model.get_daily_average()
        st.metric("📅 Daily Avg Expense", format_currency(daily_avg))


def _render_charts(analyzer_model:FinanceAnalyzer, 
                   visualizer_model:FinanceVisualizer, 
                   start_date, 
                   end_date):
    """Render the charts section with category and trend visualizations"""
    # Category charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Spending by Category")
        category_spending = analyzer_model.get_spending_by_category(start_date, end_date)
        if not category_spending.empty:
            fig = visualizer_model.plot_category_spending(category_spending)
            st.plotly_chart(fig, width='stretch') # embedded plotly chart into streamlit
        else:
            st.info("No expense data available for this period")
    
    with col2:
        st.subheader("Category Breakdown")
        if not category_spending.empty:
            fig = visualizer_model.plot_pie_chart(category_spending)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No expense data available for this period")
    
    # Monthly trend
    st.subheader("Monthly Trend")
    monthly_trend = analyzer_model.get_monthly_trend(months=6)
    if not monthly_trend.empty:
        fig = visualizer_model.plot_monthly_trend(monthly_trend)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No data available for monthly trend")


# # def _render_recent_transactions(transaction_model):
#     """Render the recent transactions table"""
#     st.subheader("Recent Transactions")
#     recent = transaction_model.get_transactions()
    
#     if recent:
#         df_recent = pd.DataFrame(recent)
#         df_recent['date'] = pd.to_datetime(df_recent['date'].head()).dt.date
#         df_recent['amount'] = df_recent['amount'].apply(format_currency)
#         st.dataframe(
#             df_recent[['date', 'type', 'category', 'amount', 'description']],
#             width='stretch',
#             hide_index=True
#         )
#     else:
#         st.info("No transactions yet")