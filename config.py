import os
from dotenv import load_dotenv

load_dotenv(override=True)

# API settings
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 4096
REQUEST_TIMEOUT = 10

# User identity — dormant for now, enables multi-user scaling later
DEFAULT_USER_ID = "default"

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# User data paths — scoped by user_id even though only "default" exists now
def get_user_dir(user_id=DEFAULT_USER_ID):
    return os.path.join(BASE_DIR, "users", user_id)

def get_stories_path(user_id=DEFAULT_USER_ID):
    return os.path.join(get_user_dir(user_id), "experience_stories.md")

def get_resumes_dir(user_id=DEFAULT_USER_ID):
    return os.path.join(get_user_dir(user_id), "resumes")

def get_sessions_dir(user_id=DEFAULT_USER_ID):
    return os.path.join(get_user_dir(user_id), "sessions")

# Ensure user directories exist
def init_user_dirs(user_id=DEFAULT_USER_ID):
    for path in [get_user_dir(user_id), get_resumes_dir(user_id), get_sessions_dir(user_id)]:
        os.makedirs(path, exist_ok=True)