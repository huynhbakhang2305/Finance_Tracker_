from pymongo import MongoClient, DESCENDING
import config
import os
class DatabaseManager:
    _instance = None
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise ValueError("❌ MONGO_URI is not set")

        self.client = MongoClient(uri)
        self.db = self.client.get_default_database()
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DATABASE_NAME]
        try:
            # test connection
            self.db.command("ping")

            # create or update index
            self._create_index()
            print("Initialize DB success")
        except Exception as e:
            print(f"Error in connect: {e}")
            raise e
        
    def _create_index(self):
        "Create indexes for better performance"
        self.db.transactions.create_index([("user_id", DESCENDING), ("date", DESCENDING)])
        self.db.categories.create_index([("user_id", DESCENDING),
                                           ("type", DESCENDING),
                                           ("name", DESCENDING)], unique = True)
        
    def get_collection(self, collection_name: str):
        """Get a collection from db"""
        return self.db[collection_name]
    
    def close_connection(self):
        """Close db connection"""
        if self.client:
            self.client.close()
            print("Shutdown database connection")


if __name__=="__main__":

    # init db
    test_db = DatabaseManager()

    # collections
    collection_name = "users"
    user_collection = test_db.get_collection(collection_name=collection_name)

    test_db.close_connection()
