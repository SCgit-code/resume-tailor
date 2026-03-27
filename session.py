import json
import os
import config
from datetime import datetime


def save_step(data, step_name, user_id=config.DEFAULT_USER_ID):
    """
    Saves the output of a pipeline step to a JSON file.
    """
    sessions_dir = config.get_sessions_dir(user_id)
    os.makedirs(sessions_dir, exist_ok=True)
    filepath = os.path.join(sessions_dir, f"{step_name}.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[Saved {step_name}]")


def load_step(step_name, user_id=config.DEFAULT_USER_ID):
    """
    Loads a previously saved pipeline step.
    Returns None if not found.
    """
    filepath = os.path.join(
        config.get_sessions_dir(user_id), f"{step_name}.json"
    )
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r") as f:
        return json.load(f)


def step_exists(step_name, user_id=config.DEFAULT_USER_ID):
    """
    Returns True if a saved step exists.
    """
    filepath = os.path.join(
        config.get_sessions_dir(user_id), f"{step_name}.json"
    )
    return os.path.exists(filepath)


def save_session(state, user_id=config.DEFAULT_USER_ID):
    """
    Saves the complete pipeline state to a single session file.
    State is a dictionary containing all pipeline data and current step.
    Named with a timestamp so multiple sessions can coexist.
    """
    sessions_dir = config.get_sessions_dir(user_id)
    os.makedirs(sessions_dir, exist_ok=True)

    # Add metadata
    state["saved_at"] = datetime.now().isoformat()
    state["user_id"] = user_id

    # Use company name and timestamp for filename
    company = state.get("company_name", "unknown").lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    current_step = state.get("current_step", "unknown")
    filename = f"session_{company}_{current_step}_{timestamp}.json"

    filepath = os.path.join(sessions_dir, filename)
    with open(filepath, "w") as f:
        json.dump(state, f, indent=2)

    print(f"\n[Session saved: {filename}]")
    print(f"[To resume: set resume_from='{filepath}' in main.py]\n")
    return filepath


def load_session(filepath):
    """
    Loads a complete session from a file path.
    Returns the state dictionary or None if file not found.
    """
    if not os.path.exists(filepath):
        print(f"Session file not found: {filepath}")
        return None

    with open(filepath, "r") as f:
        state = json.load(f)

    saved_at = state.get("saved_at", "unknown time")
    company = state.get("company_name", "unknown company")
    current_step = state.get("current_step", "unknown step")

    print(f"\n[Resuming session for {company}]")
    print(f"[Saved at: {saved_at}]")
    print(f"[Resuming from: {current_step}]\n")

    return state


def list_sessions(user_id=config.DEFAULT_USER_ID):
    """
    Lists all saved sessions for a user.
    Useful for finding which session to resume.
    """
    sessions_dir = config.get_sessions_dir(user_id)

    if not os.path.exists(sessions_dir):
        print("No sessions found.")
        return []

    session_files = [
        f for f in os.listdir(sessions_dir)
        if f.startswith("session_") and f.endswith(".json")
    ]

    if not session_files:
        print("No saved sessions found.")
        return []

    print("\nSaved sessions:")
    for i, filename in enumerate(sorted(session_files, reverse=True)):
        filepath = os.path.join(sessions_dir, filename)
        try:
            with open(filepath, "r") as f:
                state = json.load(f)
            company = state.get("company_name", "unknown")
            saved_at = state.get("saved_at", "unknown")[:16]
            current_step = state.get("current_step", "unknown")
            print(f"  {i+1}. {filename}")
            print(f"     Company: {company} | Step: {current_step} | Saved: {saved_at}")
        except Exception:
            print(f"  {i+1}. {filename} (could not read)")

    return session_files