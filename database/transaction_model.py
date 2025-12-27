from database.category_model import CategoryModel
from typing import Optional, Any
from datetime import datetime, date
from bson.objectid import ObjectId
from .database_manager import DatabaseManager
import config
from pymongo import DESCENDING, ASCENDING
from utils import handler_datetime


class TransactionModel:

    def __init__(self, user_id: Optional[str] = None):
        self.db_manager = DatabaseManager()
        self.collection = self.db_manager.get_collection(config.COLLECTIONS["transaction"])
        self.user_id = user_id

    def set_user_id(self, user_id: Optional[str]):
        """Set or clear the current user id used to scope queries."""
        self.user_id = ObjectId(user_id) if user_id is not None else None
    
    def get_transactions(
        self,
        advanced_filters: dict[str, any] = None
    ) -> list[dict]:

        # Build query filter
        query = self._build_query(advanced_filters)
              
        # Fetch transactions, sort from newest to oldest
        cursor = self.collection.find(query).sort("created_at", -1)
        return list(cursor)     
    
    def _build_query(self, advanced_filter: Optional[dict]) -> dict:
        conditions = []
        if not advanced_filter:
            return self._add_user_constraint(conditions)
        
        # Check transaction_type:
        if "transaction_type" in advanced_filter:
            conditions.append({"type": advanced_filter.get("transaction_type")})

        # Check Category:
        if "category" in advanced_filter:
            conditions.append({"category": advanced_filter.get("category")})

        # Check amount:
        min_amount = advanced_filter.get("min_amount")
        max_amount = advanced_filter.get("max_amount")
        if min_amount or max_amount:
            amount = {}
            if min_amount is not None:
                amount["$gte"] = min_amount # $gte = greater than or equal
            if max_amount is not None:
                amount["$lte"] = max_amount # $lte = less than or equal

            conditions.append({"amount": amount})

        # Check datetime
        start_date = advanced_filter.get("start_date")
        end_date = advanced_filter.get("end_date")
        if start_date or end_date:

            date_query = {}
            if start_date is not None:
                date_query["$gte"] = handler_datetime(start_date) # $gte = greater than or equal
            if end_date is not None:
                date_query["$lte"] = handler_datetime(end_date) # $lte = less than or equal
            conditions.append({"date": date_query})

        # Check description:
        if "search_text" in advanced_filter:
            conditions.append({
                "description": {
                    "$regex": advanced_filter.get("search_text"),
                    "$options": "i"  # case-insensitive
                }
            })

        return self._add_user_constraint(conditions)
    
    def _add_user_constraint(self, conditions: list) -> dict:
        conditions.append({
            "user_id": ObjectId(self.user_id) if self.user_id else None
        })
        return {
            "$and": conditions
        }
    
    def add_transaction(
        self,
        transaction_type: str,
        category: str,
        amount: float,
        transaction_date: datetime,
        description: str = ""
    ) -> Optional[str]:
        """
        Add a new transaction with automatic last_modified timestamp.
        
        Args:
            transaction_type: 'Expense' or 'Income'
            category: Category name
            amount: Transaction amount
            transaction_date: Transaction date
            description: Optional description
        
        Returns:
            Inserted document ID as string, or None if failed
        """
        cate_model = CategoryModel()
        cate_model.set_user_id(str(self.user_id))
        if not cate_model.category_exists(category_name=category, category_type=transaction_type):
            raise ValueError("Invalid category. Category does not exist.")
        if not isinstance(transaction_date, datetime):
            transaction_date = handler_datetime(transaction_date)

        transaction = {
            'type': transaction_type,
            'category': category,
            'amount': amount,
            'date': transaction_date,
            'description': description,
            'created_at': datetime.now(),
            'last_modified': datetime.now(),
            'user_id': self.user_id ## added user_id field
        }

        try:
            result = self.collection.insert_one(transaction)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error adding transaction: {e}")
            return None
    
    def update_transaction(
        self,
        transaction_id: str,
        **kwargs
    ) -> bool:
        """
        Update a transaction and set last_modified timestamp.
        
        Args:
            transaction_id: Transaction ID
            **kwargs: Fields to update
        
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if "category" in kwargs:
                cate_model = CategoryModel()
                cate_model.set_user_id(str(self.user_id))
                if not cate_model.category_exists(
                    category_name=kwargs["category"]
                ):
                    raise ValueError("Invalid category. Category does not exist.")

            # Add last_modified timestamp
            kwargs['last_modified'] = datetime.now()
            # Build filter and scope by user if available
            filter_ = {'_id': ObjectId(transaction_id),
                       'user_id': self.user_id} # added user_id constraint
            result = self.collection.update_one(filter_, {'$set': kwargs})
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating transaction: {e}")
            return False
    
    def delete_transaction(self, transaction_id: str) -> bool:
        """
        Delete a transaction.
        
        Args:
            transaction_id: Transaction ID
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            filter_ = {'_id': ObjectId(transaction_id),
                       'user_id': self.user_id} # added user_id constraint
            
            result = self.collection.delete_one(filter_)
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting transaction: {e}")
            return False
    
    def get_transaction_by_id(self, transaction_id: str) -> Optional[dict]:
        """
        Get a single transaction by ID.
        
        Args:
            transaction_id: Transaction ID
        
        Returns:
            Transaction document or None
        """
        try:
            filter_ = {'_id': ObjectId(transaction_id),
                       'user_id': self.user_id} # added user_id constraint
            return self.collection.find_one(filter_)
        except Exception as e:
            print(f"Error getting transaction: {e}")
            return None
        
    def get_transactions_by_date_range(
        self,
        start_date: datetime | date | str,
        end_date: datetime | date | str
    ) -> list[dict]:
        """
        Legacy method: Get transactions in date range.
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            list of transaction documents
        """
        return self.get_transactions(
            advanced_filters= {
                "start_date": start_date,
                "end_date": end_date,
            }
        )