import sqlite3

from typing import Optional

sqlite = None

def get_sqlite():
    global sqlite
    if not sqlite:
        sqlite = sqlite3.connect("network_data.db", check_same_thread=False)
    return sqlite

def query(query, params):
    sqlite = get_sqlite()
    try:
        cursor = sqlite.cursor()
        # Execute the SQL command
        cursor.execute(query, params)
        
        # Fetch the results
        results = cursor.fetchall()
        cursor.connection.commit()
        cursor.close()
        return results
    except sqlite3.Error as e:
        print(f"MySQL Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")