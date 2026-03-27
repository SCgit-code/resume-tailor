import os
import config
import prompter


def update_stories(final_resume, interview_record=None, user_id=config.DEFAULT_USER_ID):
    stories_path = config.get_stories_path(user_id)
    existing_stories = load_stories(stories_path)

    print("\nAnalyzing session for new stories and angles...")

    proposed = generate_proposed_additions(
        final_resume, existing_stories, interview_record
    )

    # Generate proposed additions
    proposed = generate_proposed_additions(final_resume, existing_stories)

    if not proposed:
        print("No new stories or angles to add.")
        return

    # Check for reconciliation flags
    reconciliation_flags = extract_reconciliation_flags(proposed)

    if reconciliation_flags:
        print("\n=== RECONCILIATION FLAGS ===")
        print("The following inconsistencies were found between your resume and stories doc:\n")
        proposed = handle_reconciliation(proposed, reconciliation_flags)

    # Show proposed additions to candidate
    print("\n=== PROPOSED STORIES ADDITIONS ===\n")
    print(proposed)
    print()

    candidate_input = input(
        "Type 'save' to add these to your experience stories, "
        "'skip' to leave the stories doc unchanged, "
        "or 'edit' to modify before saving: "
    ).strip().lower()

    if candidate_input == "save":
        write_to_stories(proposed, stories_path)
        print("\nExperience stories updated.")

    elif candidate_input == "edit":
        print("\nPaste your edited version below. Press Enter twice when done:")
        edited = get_multiline_input()
        if edited:
            write_to_stories(edited, stories_path)
            print("\nExperience stories updated with your edits.")

    else:
        print("\nStories doc unchanged.")


def generate_proposed_additions(final_resume, existing_stories, interview_record=None):
    existing_context = existing_stories if existing_stories else "No existing stories yet."
    interview_context = interview_record if interview_record else "No interview record available."

    user_message = f"""Here is the candidate's approved final resume:

{final_resume}

Here is the full interview record from this session — includes stories and context that may not have made it into the final resume:

{interview_context}

Here is the current experience stories document:

{existing_context}"""

    system_prompt = """You are updating a candidate's experience stories document after a resume tailoring session.

The experience stories document is a living repository of career stories, tested framings, and positioning angles. It compounds over time — each session adds new knowledge.

Your job:
1. Read the approved resume AND the full interview record
2. Compare both against the existing stories doc
3. Identify new stories from EITHER source — not just what made it into the resume
4. For stories from the interview that didn't make the resume, note why they might be useful for future roles
5. Check for numerical or factual inconsistencies

For inconsistencies, flag them clearly like this:
RECONCILIATION FLAG: [story name] — resume says [X], stories doc says [Y]. Which is correct?

For new additions, use exactly this format:

---
**STORY: [short descriptive name]**
**Role/company:** [role title, company name]
**Core facts:** [2-4 sentences — what happened, what the candidate did, key outcomes]
**Effective framings:**
- [role type or gap it addresses]: [how to position it in 1-2 sentences]
**Notes:** [anything worth remembering — caveats, preferences, angles that worked]
---

Rules:
- Only add what is genuinely new or different from what already exists
- Do not duplicate existing stories — add a new framing line instead
- Do not fabricate — every fact must come from the approved resume
- If there is nothing new to add, say "NONE"
- Return reconciliation flags first, then new additions"""

    response = prompter.call_claude(system_prompt, user_message)
    return response


def extract_reconciliation_flags(proposed):
    """
    Extracts reconciliation flags from the proposed additions text.
    Returns a list of flag strings.
    """
    if not proposed:
        return []

    flags = []
    for line in proposed.split("\n"):
        if line.startswith("RECONCILIATION FLAG:"):
            flags.append(line.replace("RECONCILIATION FLAG:", "").strip())

    return flags


def handle_reconciliation(proposed, flags):
    """
    Shows each reconciliation flag to the candidate one at a time.
    Candidate confirms the correct version.
    Returns updated proposed text with confirmed versions.
    """
    updated = proposed

    for flag in flags:
        print(f"\nInconsistency found: {flag}")
        confirmed = input("Type the correct value to use everywhere: ").strip()

        if confirmed:
            # Note the confirmed version — in v2 we would
            # automatically update both the stories doc and resume
            print(f"Noted. Will use: {confirmed}")
            updated += f"\nNOTE: Confirmed value for above inconsistency: {confirmed}"

    return updated


def load_stories(stories_path):
    """
    Loads the existing stories doc.
    Returns None if file doesn't exist or is empty.
    """
    if not os.path.exists(stories_path):
        return None

    with open(stories_path, "r") as f:
        content = f.read().strip()

    return content if content else None


def write_to_stories(new_content, stories_path):
    """
    Appends new content to the stories doc.
    Adds a session separator for readability.
    """
    with open(stories_path, "a") as f:
        f.write("\n\n")
        f.write("---\n")
        f.write("## Added this session\n\n")
        f.write(new_content)
        f.write("\n")


def get_multiline_input():
    """
    Collects multiline input.
    User presses Enter twice to submit.
    """
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    return "\n".join(lines[:-1]).strip()