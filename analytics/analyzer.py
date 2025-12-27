
import pandas as pd
from datetime import datetime, timedelta
from database import TransactionModel

class FinanceAnalyzer:
    def __init__(self, 
                 transaction_model: TransactionModel):
        self.transaction_model = transaction_model
    
    def get_transactions_dataframe(self):
        """Convert transactions to pandas DataFrame"""
        transactions = self.transaction_model.get_transactions()
        
        if not transactions:
            return pd.DataFrame()
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def calculate_total_by_type(self, transaction_type, start_date=None, end_date=None):
        """Calculate total amount by transaction type"""
        if start_date and end_date:
            transactions = self.transaction_model.get_transactions_by_date_range(
                start_date, end_date
            )
        else:
            transactions = self.transaction_model.get_transactions()
        
        total = sum(t['amount'] for t in transactions if t['type'] == transaction_type)
        return total
    
    def get_spending_by_category(self, start_date=None, end_date=None):
        """Get spending grouped by category"""
        if start_date and end_date:
            transactions = self.transaction_model.get_transactions_by_date_range(
                start_date, end_date
            )
        else:
            transactions = self.transaction_model.get_transactions()
        
        df = pd.DataFrame(transactions)
        
        if df.empty:
            return pd.DataFrame()
        
        # Filter only expenses
        expenses = df[df['type'] == 'Expense']
        
        if expenses.empty:
            return pd.DataFrame()
        
        category_spending = expenses.groupby('category')['amount'].agg(['sum', 'count', 'mean']).reset_index()
        category_spending.columns = ['Category', 'Total', 'Count', 'Average']
        category_spending = category_spending.sort_values('Total', ascending=False)
        
        return category_spending
    
    def get_monthly_trend(self, months=6):
        """Get monthly spending and income trend"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
        
        transactions = self.transaction_model.get_transactions_by_date_range(
            start_date, end_date
        )
        
        df = pd.DataFrame(transactions)
        
        if df.empty:
            return pd.DataFrame()
        
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
        
        monthly_data = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
        monthly_data.index = monthly_data.index.to_timestamp()
        
        return monthly_data
    
    def get_daily_average(self):
        """Calculate daily average spending"""

        # approach 1:
        transactions = self.transaction_model.get_transactions()
        expenses = [t for t in transactions if t['type'] == 'Expense']

        # # approach 2:
        # advanced_filter = {"type": 'Expense'}
        # expenses = self.transaction_model.get_transactions(advanced_filter)

        if not expenses:
            return 0
        
        df = pd.DataFrame(expenses)
        df['date'] = pd.to_datetime(df['date']) # ensure convert properly datetime format
        
        date_range = (df['date'].max() - df['date'].min()).days + 1
        total_spending = df['amount'].sum()
        
        return total_spending / date_range if date_range > 0 else 0
    
    def detect_anomalies(self, threshold=2):
        """Detect unusual spending patterns"""
        df = self.get_transactions_dataframe()
        
        if df.empty:
            return pd.DataFrame()
        
        expenses = df[df['type'] == 'Expense'].copy()
        
        if expenses.empty or len(expenses) < 5:
            return pd.DataFrame()
        
        mean_amount = expenses['amount'].mean()
        std_amount = expenses['amount'].std()
        
        expenses['z_score'] = (expenses['amount'] - mean_amount) / std_amount
        anomalies = expenses[abs(expenses['z_score']) > threshold]
        
        return anomalies[['date', 'category', 'amount', 'description', 'z_score']]
    
    def predict_next_month_spending(self):
        """Simple prediction based on moving average"""
        monthly_trend = self.get_monthly_trend(months=6)
        
        if monthly_trend.empty or 'Expense' not in monthly_trend.columns:
            return 0
        
        expenses = monthly_trend['Expense']
        
        if len(expenses) < 2:
            return expenses.iloc[-1] if len(expenses) == 1 else 0
        
        # Simple moving average prediction
        prediction = expenses.rolling(window=3, min_periods=1).mean().iloc[-1]
        
        return prediction
    
    def get_statistics_summary(self):
        """Get comprehensive statistics summary"""
        df = self.get_transactions_dataframe()
        
        if df.empty:
            return {}
        
        expenses = df[df['type'] == 'Expense']
        income = df[df['type'] == 'Income']
        
        summary = {
            'total_expenses': expenses['amount'].sum() if not expenses.empty else 0,
            'total_income': income['amount'].sum() if not income.empty else 0,
            'avg_expense': expenses['amount'].mean() if not expenses.empty else 0,
            'avg_income': income['amount'].mean() if not income.empty else 0,
            'median_expense': expenses['amount'].median() if not expenses.empty else 0,
            'transaction_count': len(df),
            'expense_count': len(expenses),
            'income_count': len(income),
        }
        
        summary['net_balance'] = summary['total_income'] - summary['total_expenses']
        
        return summary
