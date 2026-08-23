from app.config import PRIORITIES
from app.database import db_cursor


def get_task_for_user(task_id: int, user_id: int):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, user_id, title, description, priority, completed, created_at, updated_at
            FROM tasks
            WHERE id = ? AND user_id = ?
            """,
            (task_id, user_id),
        )
        return cursor.fetchone()


def get_tasks_for_user(user_id: int, priority_filter: str = "All", sort_by: str = "Priority"):
    query = """
        SELECT id, title, description, priority, completed, created_at, updated_at
        FROM tasks
        WHERE user_id = ?
    """
    params: list = [user_id]

    if priority_filter != "All":
        query += " AND priority = ?"
        params.append(priority_filter)

    if sort_by == "Priority":
        query += """
            ORDER BY
                CASE priority
                    WHEN 'High' THEN 0
                    WHEN 'Medium' THEN 1
                    WHEN 'Low' THEN 2
                    ELSE 3
                END ASC,
                completed ASC,
                updated_at DESC
        """
    elif sort_by == "Newest":
        query += " ORDER BY completed ASC, created_at DESC"
    elif sort_by == "Oldest":
        query += " ORDER BY completed ASC, created_at ASC"
    else:
        query += " ORDER BY completed ASC, updated_at DESC"

    with db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def create_task(user_id: int, title: str, description: str, priority: str) -> None:
    if priority not in PRIORITIES:
        raise ValueError("Invalid priority value.")

    with db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tasks (user_id, title, description, priority)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, title, description, priority),
        )


def update_task(
    task_id: int,
    user_id: int,
    title: str,
    description: str,
    priority: str,
    completed: bool,
) -> bool:
    if priority not in PRIORITIES:
        raise ValueError("Invalid priority value.")

    task = get_task_for_user(task_id, user_id)
    if task is None:
        return False

    with db_cursor() as cursor:
        cursor.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, priority = ?, completed = ?,
                updated_at = datetime('now')
            WHERE id = ? AND user_id = ?
            """,
            (title, description, priority, int(completed), task_id, user_id),
        )
    return True


def toggle_task(task_id: int, user_id: int) -> bool:
    task = get_task_for_user(task_id, user_id)
    if task is None:
        return False

    new_status = 0 if task["completed"] else 1
    with db_cursor() as cursor:
        cursor.execute(
            """
            UPDATE tasks
            SET completed = ?, updated_at = datetime('now')
            WHERE id = ? AND user_id = ?
            """,
            (new_status, task_id, user_id),
        )
    return True


def delete_task(task_id: int, user_id: int) -> bool:
    task = get_task_for_user(task_id, user_id)
    if task is None:
        return False

    with db_cursor() as cursor:
        cursor.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
    return True
