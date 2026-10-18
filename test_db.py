from db import get_db_connection

try:
    connection = get_db_connection()

    if connection.is_connected():
        print("SUCCESS! Brew Café is connected to MySQL!")

    connection.close()

except Exception as error:
    print("Database connection failed:")
    print(error)