import os
import config
from docx import Document


def build_context_pool(user_id=config.DEFAULT_USER_ID):
    """
    Assembles the full candidate context pool.
    Detects whether this is a first run or returning user
    and loads the appropriate sources.
    Returns a dictionary with resume text and stories content.
    """
    is_first_run = check_first_run(user_id)

    if is_first_run:
        print("First run detected — loading all resumes...")
        resume_texts = load_all_resumes(user_id)
    else:
        print("Returning user detected — loading current resume and stories...")
        resume_texts = load_current_resume(user_id)

    stories_text = load_stories(user_id)

    # Report what we loaded
    print(f"Loaded {len(resume_texts)} resume(s)")
    if stories_text:
        print(f"Loaded experience stories ({len(stories_text.split())} words)")
    else:
        print("No experience stories yet")

    return {
        "resumes": resume_texts,
        "stories": stories_text,
        "is_first_run": is_first_run
    }


def check_first_run(user_id=config.DEFAULT_USER_ID):
    """
    Returns True if this is a first run.
    Detects by checking if experience_stories.md exists and has content.
    """
    stories_path = config.get_stories_path(user_id)

    if not os.path.exists(stories_path):
        return True

    with open(stories_path, "r") as f:
        content = f.read().strip()

    # Consider it a first run if the file is empty or
    # only contains the template header
    return len(content) < 100


def load_all_resumes(user_id=config.DEFAULT_USER_ID):
    """
    Loads all .docx files from the resumes folder.
    Returns a list of extracted text strings.
    """
    resumes_dir = config.get_resumes_dir(user_id)
    resume_texts = []

    if not os.path.exists(resumes_dir):
        print(f"Warning: resumes folder not found at {resumes_dir}")
        return resume_texts

    docx_files = [f for f in os.listdir(resumes_dir) if f.endswith(".docx")]

    if not docx_files:
        print("Warning: no .docx files found in resumes folder")
        return resume_texts

    for filename in docx_files:
        filepath = os.path.join(resumes_dir, filename)
        text = extract_docx_text(filepath)
        if text:
            print(f"Loaded: {filename} ({len(text.split())} words)")
            resume_texts.append({
                "filename": filename,
                "text": text
            })

    return resume_texts


def load_current_resume(user_id=config.DEFAULT_USER_ID):
    """
    Loads only the most recently modified .docx file.
    Used for returning users where stories doc carries most context.
    """
    resumes_dir = config.get_resumes_dir(user_id)

    if not os.path.exists(resumes_dir):
        print(f"Warning: resumes folder not found at {resumes_dir}")
        return []

    docx_files = [f for f in os.listdir(resumes_dir) if f.endswith(".docx")]

    if not docx_files:
        print("Warning: no .docx files found in resumes folder")
        return []

    # Pick the most recently modified file
    most_recent = max(
        docx_files,
        key=lambda f: os.path.getmtime(os.path.join(resumes_dir, f))
    )

    filepath = os.path.join(resumes_dir, most_recent)
    text = extract_docx_text(filepath)

    if text:
        print(f"Loaded current resume: {most_recent} ({len(text.split())} words)")
        return [{"filename": most_recent, "text": text}]

    return []


def extract_docx_text(filepath):
    """
    Extracts clean text from a .docx file.
    Preserves paragraph breaks for readability.
    """
    try:
        doc = Document(filepath)
        paragraphs = []

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                paragraphs.append(text)

        return "\n".join(paragraphs)

    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def load_stories(user_id=config.DEFAULT_USER_ID):
    """
    Loads the experience stories document.
    Returns None if file doesn't exist or is empty.
    """
    stories_path = config.get_stories_path(user_id)

    if not os.path.exists(stories_path):
        return None

    with open(stories_path, "r") as f:
        content = f.read().strip()

    return content if content else None


def format_context_pool(context_pool):
    """
    Formats the context pool into clean text for use in prompts.
    Called by prompter.py when building any prompt that needs
    candidate context.
    """
    sections = []

    # Add resumes
    for i, resume in enumerate(context_pool["resumes"]):
        label = "RESUME" if len(context_pool["resumes"]) == 1 else f"RESUME {i+1}: {resume['filename']}"
        sections.append(f"--- {label} ---\n{resume['text']}")

    # Add stories if present
    if context_pool["stories"]:
        sections.append(f"--- EXPERIENCE STORIES ---\n{context_pool['stories']}")

    return "\n\n".join(sections)