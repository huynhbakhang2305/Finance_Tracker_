from database.database_manager import DatabaseManager
import config
from datetime import datetime
from bson.objectid import ObjectId

collection_name = config.COLLECTIONS['user']

class UserModel:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.collection = self.db_manager.get_collection(collection_name=collection_name)

    def create_user(self, email: str) -> str:
        """Create new user"""

        user = {
            "email": email,
            "created_at": datetime.now(),
            "last_modified": datetime.now(),
            "is_activate": True
        }

        result = self.collection.insert_one(user)
        return str(result.inserted_id)
    
    def login(self, email: str) -> str:
        # check user exist (use find_one)
        user = self.collection.find_one({'email': email})
        
        # case 1: user not exist:
        # create: call create_user(email)
        if not user:
            return self.create_user(email)

        # case 2: user exist but deactivate
        # raise Error
        if user.get("is_activate") is not True:
            raise ValueError("This account is deactivated! Please connect to CS")

        # all checking passed
        return str(user.get("_id"))
    
    def deactivate(self, user_id: str) -> bool:
        # find and update:
        user = self.collection.find_one({
            "_id": ObjectId(user_id),
            "is_activate": True
        })

        # case: not exist user
        if not user:
            raise ValueError("User not found")
        
        # user is validate and ready to deactivate -> update them
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_activate": False}}
        )

        return result.modified_count > 0
    def delete_user_and_data(self, user_id: str) -> dict:
        """
        Permanently delete user and all related data
        (Topic 3 – Data Leak Prevention)
        """
        user_oid = ObjectId(user_id)

        # get other collections
        trans_col = self.db_manager.get_collection(
            config.COLLECTIONS["transaction"]
        )
        budget_col = self.db_manager.get_collection(
            config.COLLECTIONS.get("budget", "budgets")
        )
        cate_col = self.db_manager.get_collection(
            config.COLLECTIONS["category"]
        )

        # delete related data
        trans_result = trans_col.delete_many({"user_id": user_oid})
        budget_result = budget_col.delete_many({"user_id": user_oid})
        cate_result = cate_col.delete_many({"user_id": user_oid})

        # delete user
        user_result = self.collection.delete_one({"_id": user_oid})

        return {
            "users": user_result.deleted_count,
            "transactions": trans_result.deleted_count,
            "budgets": budget_result.deleted_count,
            "categories": cate_result.deleted_count
        }
