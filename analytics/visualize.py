
"""
pip install seaborn plotly
"""

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# Set common style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

class FinanceVisualizer:
    
    @staticmethod
    def plot_category_spending(category_data):
        """Create bar chart for spending by category"""
        if category_data.empty:
            return None
        
        fig = px.bar(
            category_data,
            x='Category',
            y='Total',
            title='Spending by Category',
            labels={'Total': 'Amount ($)', 'Category': 'Category'},
            color='Total',
            color_continuous_scale='Reds'
        )
        
        # overwrite common config
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500
        )
        
        return fig
    
    @staticmethod
    def plot_pie_chart(category_data):
        """Create pie chart for category distribution"""
        if category_data.empty:
            return  # early exist
        
        fig = px.pie(
            category_data,
            values='Total',
            names='Category',
            title='Expense Distribution by Category',
            hole=0.3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        return fig
    
    @staticmethod
    def plot_monthly_trend(monthly_data):
        """Create line chart for monthly trend"""
        if monthly_data.empty:
            return None
        
        fig = go.Figure()
        
        if 'Expense' in monthly_data.columns:
            fig.add_trace(go.Scatter(
                x=monthly_data.index,
                y=monthly_data['Expense'],
                mode='lines+markers',
                name='Expenses',
                line=dict(color='red', width=2)
            ))
        
        if 'Income' in monthly_data.columns:
            fig.add_trace(go.Scatter(
                x=monthly_data.index,
                y=monthly_data['Income'],
                mode='lines+markers',
                name='Income',
                line=dict(color='green', width=2)
            ))
        
        fig.update_layout(
            title='Monthly Income vs Expenses Trend',
            xaxis_title='Month',
            yaxis_title='Amount ($)',
            hovermode='x unified',
            height=500
        )
        
        return fig
    
    @staticmethod
    def plot_budget_comparison(budget_data, actual_data):
        """Create comparison chart for budget vs actual"""
        if budget_data.empty:
            return None
        
        # Merge budget and actual data
        comparison = budget_data.merge(
            actual_data,
            left_on='Category',
            right_on='Category',
            how='left'
        ).fillna(0)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Budget',
            x=comparison['Category'],
            y=comparison['amount'],
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Actual',
            x=comparison['Category'],
            y=comparison['Total'],
            marker_color='darkblue'
        ))
        
        fig.update_layout(
            title='Budget vs Actual Spending',
            xaxis_title='Category',
            yaxis_title='Amount ($)',
            barmode='group',
            height=500
        )
        
        return fig
    
    @staticmethod
    def plot_daily_spending_heatmap(df):
        """Create heatmap for spending by day of week and hour"""
        if df.empty:
            return None
        
        expenses = df[df['type'] == 'Expense'].copy()
        
        if expenses.empty:
            return None
        
        expenses['day_of_week'] = expenses['date'].dt.day_name()
        expenses['week'] = expenses['date'].dt.isocalendar().week
        
        heatmap_data = expenses.groupby(['week', 'day_of_week'])['amount'].sum().unstack(fill_value=0)
        
        # Reorder days
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex(columns=days_order, fill_value=0)
        
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Day of Week", y="Week", color="Amount ($)"),
            title="Spending Heatmap by Week and Day",
            color_continuous_scale="Reds",
            aspect="auto"
        )
        
        return fig
    
    @staticmethod
    def plot_transaction_timeline(df):
        """Create timeline of transactions"""
        if df.empty:
            return None
        
        fig = px.scatter(
            df,
            x='date',
            y='amount',
            color='type',
            size='amount',
            hover_data=['category', 'description'],
            title='Transaction Timeline',
            color_discrete_map={'Expense': 'red', 'Income': 'green'}
        )
        
        fig.update_layout(height=500)
        
        return fig
