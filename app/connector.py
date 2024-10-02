import mysql.connector

class Database:
    @staticmethod
    def get_connection():
        return mysql.connector.connect(
            host="localhost",
            user="myuser",       # Use the new user
            password="mypassword",  # Use the new password
            database="llamadolu"
        )
