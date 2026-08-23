import streamlit as st

from app.config import PRIORITIES, PRIORITY_INDICATORS
from app.database import init_db
from app.auth.utils import authenticate_user, create_user, validate_registration
from app.tasks.service import (
    create_task,
    delete_task,
    get_tasks_for_user,
    toggle_task,
    update_task,
)

st.set_page_config(page_title="TaskFlow", page_icon="✓", layout="wide")

PRIORITY_FILTER_OPTIONS = ["All"] + list(PRIORITIES)
SORT_OPTIONS = ["Priority", "Newest", "Oldest", "Recently Updated"]


def init_session_state() -> None:
    defaults = {
        "user_id": None,
        "username": None,
        "priority_filter": "All",
        "sort_by": "Priority",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_logged_in() -> bool:
    return st.session_state.get("user_id") is not None


def login_user(user_id: int, username: str) -> None:
    st.session_state.user_id = user_id
    st.session_state.username = username


def logout_user() -> None:
    st.session_state.user_id = None
    st.session_state.username = None


def render_priority_badge(priority: str) -> None:
    indicator = PRIORITY_INDICATORS.get(priority, "⚪")
    st.markdown(f"{indicator} **{priority}**")


def render_auth_screen() -> None:
    st.title("✓ TaskFlow")
    st.caption("Organize your tasks with priority levels")

    login_tab, register_tab = st.tabs(["Log In", "Sign Up"])

    with login_tab:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)

            if submitted:
                if not username.strip() or not password:
                    st.error("Username and password are required.")
                else:
                    user = authenticate_user(username, password)
                    if user is None:
                        st.error("Invalid username or password.")
                    else:
                        login_user(user["id"], user["username"])
                        st.success(f"Welcome back, {user['username']}!")
                        st.rerun()

    with register_tab:
        with st.form("register_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="At least 6 characters")
            confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat your password")
            submitted = st.form_submit_button("Sign Up", type="primary", use_container_width=True)

            if submitted:
                errors = validate_registration(username, email, password, confirm)
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        create_user(username, email, password)
                        st.success("Account created! Please log in.")
                    except Exception:
                        st.error("Registration failed. Please try again.")


def render_create_task_form() -> None:
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("create_task_form", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                title = st.text_input("Title", placeholder="What needs to be done?", max_chars=200)
            with col2:
                priority = st.selectbox("Priority", PRIORITIES, index=1)

            description = st.text_input("Description (optional)", placeholder="Add details...")

            if st.form_submit_button("Add Task", type="primary", use_container_width=True):
                title = title.strip()
                description = description.strip()

                if not title:
                    st.error("Task title is required.")
                elif len(title) > 200:
                    st.error("Task title must be 200 characters or fewer.")
                else:
                    try:
                        create_task(st.session_state.user_id, title, description, priority)
                        st.success("Task created successfully.")
                        st.rerun()
                    except Exception:
                        st.error("Failed to create task. Please try again.")


def render_task_item(task) -> None:
    task_id = task["id"]
    status_icon = "✅" if task["completed"] else "⬜"
    title_style = "~~" if task["completed"] else ""

    with st.container(border=True):
        header_col, badge_col, actions_col = st.columns([5, 2, 2])

        with header_col:
            st.markdown(f"### {status_icon} {title_style}{task['title']}{title_style}")
            if task["description"]:
                st.caption(task["description"])

        with badge_col:
            render_priority_badge(task["priority"])

        with actions_col:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                toggle_label = "Undo" if task["completed"] else "Done"
                if st.button(toggle_label, key=f"toggle_{task_id}", use_container_width=True):
                    if toggle_task(task_id, st.session_state.user_id):
                        st.rerun()
                    else:
                        st.error("Failed to update task status.")
            with btn_col2:
                if st.button("Delete", key=f"delete_{task_id}", type="secondary", use_container_width=True):
                    if delete_task(task_id, st.session_state.user_id):
                        st.rerun()
                    else:
                        st.error("Failed to delete task.")

        with st.expander("Edit task"):
            with st.form(key=f"edit_form_{task_id}"):
                edit_title = st.text_input("Title", value=task["title"], max_chars=200)
                edit_description = st.text_input("Description", value=task["description"] or "")
                edit_priority = st.selectbox(
                    "Priority",
                    PRIORITIES,
                    index=PRIORITIES.index(task["priority"]) if task["priority"] in PRIORITIES else 1,
                )
                edit_completed = st.checkbox("Mark as completed", value=bool(task["completed"]))

                if st.form_submit_button("Save Changes", type="primary"):
                    edit_title = edit_title.strip()
                    if not edit_title:
                        st.error("Task title is required.")
                    elif len(edit_title) > 200:
                        st.error("Task title must be 200 characters or fewer.")
                    else:
                        try:
                            updated = update_task(
                                task_id,
                                st.session_state.user_id,
                                edit_title,
                                edit_description.strip(),
                                edit_priority,
                                edit_completed,
                            )
                            if updated:
                                st.success("Task updated successfully.")
                                st.rerun()
                            else:
                                st.error("Task not found.")
                        except Exception:
                            st.error("Failed to update task. Please try again.")


def render_dashboard() -> None:
    st.title("Your Tasks")
    st.caption(f"Logged in as **@{st.session_state.username}**")

    with st.sidebar:
        st.header("Controls")
        st.session_state.priority_filter = st.selectbox(
            "Filter by priority",
            PRIORITY_FILTER_OPTIONS,
            index=PRIORITY_FILTER_OPTIONS.index(st.session_state.priority_filter),
        )
        st.session_state.sort_by = st.selectbox(
            "Sort by",
            SORT_OPTIONS,
            index=SORT_OPTIONS.index(st.session_state.sort_by),
        )

        st.divider()
        st.markdown("**Priority legend**")
        for level in PRIORITIES:
            st.markdown(f"{PRIORITY_INDICATORS[level]} {level}")

        st.divider()
        if st.button("Log out", type="secondary", use_container_width=True):
            logout_user()
            st.rerun()

    render_create_task_form()

    tasks = get_tasks_for_user(
        st.session_state.user_id,
        priority_filter=st.session_state.priority_filter,
        sort_by=st.session_state.sort_by,
    )

    st.subheader(f"Task List ({len(tasks)})")

    if not tasks:
        st.info("No tasks found. Add your first task above!")
    else:
        for task in tasks:
            render_task_item(task)


def main() -> None:
    init_db()
    init_session_state()

    if is_logged_in():
        render_dashboard()
    else:
        render_auth_screen()


if __name__ == "__main__":
    main()
