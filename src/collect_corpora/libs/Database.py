from pymongo import MongoClient

class Database:
    REJECTED = 'REJECTED'
    INTERESTING = 'INTERESTING'
    SCANNED_CORPUS = 'SCANNED_CORPUS'
    COMPLETED_CORPUS = 'COMPLETED_CORPUS'
    REQUEST_SENT = 'REQUEST_SENT'
    ACCESS_GRANTED = 'ACCESS_GRANTED'
    DOWNLOADED = 'DOWNLOADED'

    def __init__(self, database_name = 'MAPS'):
        client = MongoClient()
        self.db = client[database_name]

    def clear_collection(self, collection):
        return self.delete_many(collection, {})

    def duplicate_collection(self, from_collection, to_collection):
        return self.db[from_collection].aggregate([
            {'$match': {}},
            {'$out': to_collection}
        ])

    def insert_many(self, collection, objects, clear_before_insert = False):
        if clear_before_insert:
            self.clear_collection(collection)
        return self.db[collection].insert_many(objects)

    def update_one(self, collection, find_query, update_dict):
        return self.db[collection].update_one(find_query, update_dict)

    def update_many(self, collection, find_query, update_dict):
        return self.db[collection].update_many(find_query, update_dict)

    def find(self, collection, query):
        return self.db[collection].find(query)

    def delete_many(self, collection, query):
        return self.db[collection].delete_many(query)

    def get(self):
        return self.db