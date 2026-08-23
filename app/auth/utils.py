import re

from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db_cursor

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="scrypt")


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def get_user_by_username(username: str):
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT id, username, email, password_hash FROM users WHERE username = ?",
            (username.strip().lower(),),
        )
        return cursor.fetchone()


def get_user_by_email(email: str):
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT id, username, email, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),),
        )
        return cursor.fetchone()


def create_user(username: str, email: str, password: str) -> int:
    password_hash = hash_password(password)
    with db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (username.strip().lower(), email.strip().lower(), password_hash),
        )
        return cursor.lastrowid


def validate_registration(username: str, email: str, password: str, confirm: str) -> list[str]:
    errors = []

    if not username or not USERNAME_PATTERN.match(username):
        errors.append("Username must be 3–30 characters (letters, numbers, underscore only).")

    if not email or not EMAIL_PATTERN.match(email):
        errors.append("Please enter a valid email address.")

    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters.")

    if password != confirm:
        errors.append("Passwords do not match.")

    if get_user_by_username(username):
        errors.append("Username is already taken.")

    if get_user_by_email(email):
        errors.append("Email is already registered.")

    return errors


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if user is None or not verify_password(user["password_hash"], password):
        return None
    return user
