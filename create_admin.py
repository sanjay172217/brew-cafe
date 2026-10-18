from getpass import getpass
from werkzeug.security import generate_password_hash
from db import get_db_connection


def create_admin():
    username = input("Enter admin username: ").strip()

    if not username or len(username) > 50:
        print("Username must contain 1–50 characters.")
        return

    password = getpass("Create admin password: ")
    confirm_password = getpass("Confirm admin password: ")

    if len(password) < 12:
        print("Use a password with at least 12 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO admins (username, password_hash)
            VALUES (%s, %s)
            """,
            (username, generate_password_hash(password))
        )

        connection.commit()

        print("SUCCESS! Admin account created.")

    except Exception as error:
        if connection and connection.is_connected():
            connection.rollback()

        print("Could not create admin account.")
        print("Details:", error)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    create_admin()