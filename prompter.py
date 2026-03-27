import anthropic
import config


def call_claude(system_prompt, user_message):
    """
    Core function for all Claude API calls.
    Takes a system prompt and user message, returns Claude's response as text.
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    try:
        message = client.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return message.content[0].text

    except anthropic.APIConnectionError:
        print("Error: could not connect to Claude API. Check your internet connection.")
        return None
    except anthropic.AuthenticationError:
        print("Error: invalid API key. Check your .env file.")
        return None
    except anthropic.RateLimitError:
        print("Error: rate limit hit. Wait a moment and try again.")
        return None
    except Exception as e:
        print(f"Unexpected API error: {e}")
        return None


def extract_tag(text, tag):
    """
    Extracts content between XML-style tags.
    Example: extract_tag(text, "company_snapshot") returns
    everything between <company_snapshot> and </company_snapshot>.
    Returns None if tag not found.
    """
    open_tag = f"<{tag}>"
    close_tag = f"</{tag}>"

    start = text.find(open_tag)
    end = text.find(close_tag)

    if start == -1 or end == -1:
        print(f"Warning: could not find <{tag}> in response")
        return None

    return text[start + len(open_tag):end].strip()


def build_role_brief(jd_text, research_findings, candidate_notes=None):
    """
    Takes JD text and research findings.
    Returns a structured role brief as a dictionary.
    """
    # Format research findings into readable text
    research_text = format_research(research_findings)

    # Build the user message
    user_message = f"""Here is the job description:

{jd_text}

Here is what I found about the company:

{research_text}
"""

    if candidate_notes:
        user_message += f"\nAdditional context from the candidate:\n{candidate_notes}"

    system_prompt = """You are a expert resume coach analyzing a job description and company research to produce a structured role brief.

Your output must contain exactly these four XML tags and nothing else — no preamble, no commentary, no text outside the tags:

<company_snapshot>
3-4 sentences. What this company does, who their customers are, what stage they appear to be at, and what they seem to care about. Use their own language where it is distinctive.
</company_snapshot>

<role_summary>
2-3 sentences. What this role likely owns, what success looks like in year one, and where it sits in the org if inferrable.
</role_summary>

<role_priorities>
Ranked list, max 6 items. What this role will evaluate candidates on, ranked by apparent importance. Be specific — not "communication skills" but "ability to drive alignment across engineering, legal, and policy on ambiguous problems."
</role_priorities>

<key_vocabulary>
A list of words and phrases from the JD that should appear naturally in a strong application. Do not list generic professional terms — only language that is distinctive to this role or company.
</key_vocabulary>"""

    print("\nGenerating role brief...")
    response = call_claude(system_prompt, user_message)

    if not response:
        return None

    # Parse the response into a dictionary
    role_brief = {
        "company_snapshot": extract_tag(response, "company_snapshot"),
        "role_summary": extract_tag(response, "role_summary"),
        "role_priorities": extract_tag(response, "role_priorities"),
        "key_vocabulary": extract_tag(response, "key_vocabulary"),
    }

    # Check all sections were successfully extracted
    missing = [k for k, v in role_brief.items() if v is None]
    if missing:
        print(f"Warning: missing sections: {missing}")

    return role_brief


def format_research(findings):
    """
    Formats research findings into clean readable text for the prompt.
    """
    if not findings:
        return "No research findings available."

    sections = []
    for f in findings:
        sections.append(f"Source: {f['source']}\n{f['content']}")

    return "\n\n---\n\n".join(sections)
def build_hiring_manager_assessment(role_brief, context_pool, user_id=config.DEFAULT_USER_ID):
    """
    Takes the role brief and candidate context pool.
    Returns a structured hiring manager assessment as a dictionary.
    """
    from resume_reader import format_context_pool

    # Format the role brief into readable text
    role_brief_text = format_role_brief(role_brief)

    # Format the context pool — resumes and stories
    candidate_context = format_context_pool(context_pool)

    user_message = f"""Here is the role brief:

{role_brief_text}

Here is the candidate's background:

{candidate_context}"""

    system_prompt = """You are a hiring manager who has been recruiting senior product managers for 10+ years. You are reading this candidate's background against a specific role brief. You are honest — your job is to find the best person for the role, not to make the candidate feel good.

If the candidate is making a career pivot, name it directly. Your job is not to penalize the pivot but to identify what a skeptical panel member would flag.

Produce your assessment using exactly these four XML tags and nothing else — no preamble, no commentary, no text outside the tags:

<first_impression>
2-3 sentences. Your honest gut reaction reading this candidate's background for this role. What registers immediately, positively or negatively.
</first_impression>

<strengths>
Max 4 items. What genuinely maps to what this role needs. Reference actual content from the candidate's background — not general praise. Be specific.
</strengths>

<gaps>
Max 5 items, ranked by severity. For each gap classify as one of:
[ADDRESSABLE] — can be reframed or surfaced with what already exists
[PARTIALLY ADDRESSABLE] — something exists but it is thin, worth probing
[STRUCTURAL] — real gap, name it plainly

For ADDRESSABLE and PARTIALLY ADDRESSABLE gaps: note briefly what might close them.
For STRUCTURAL gaps: name them and move on. Do not dwell.
</gaps>

<what_would_get_a_call>
2-3 specific things grounded in the role brief that would put this candidate in the top pile. Not generic advice — specific to this role and this candidate.
</what_would_get_a_call>"""

    print("\nGenerating hiring manager assessment...")
    response = call_claude(system_prompt, user_message)

    if not response:
        return None

    assessment = {
        "first_impression": extract_tag(response, "first_impression"),
        "strengths": extract_tag(response, "strengths"),
        "gaps": extract_tag(response, "gaps"),
        "what_would_get_a_call": extract_tag(response, "what_would_get_a_call"),
    }

    missing = [k for k, v in assessment.items() if v is None]
    if missing:
        print(f"Warning: missing sections: {missing}")

    return assessment


def format_role_brief(role_brief):
    """
    Formats the role brief dictionary into readable text for prompts.
    """
    sections = []
    for key, value in role_brief.items():
        if value:
            label = key.replace("_", " ").upper()
            sections.append(f"{label}:\n{value}")
    return "\n\n".join(sections)

def run_interview_loop(role_brief, assessment, context_pool, user_id=config.DEFAULT_USER_ID):
    """
    Runs the multi-round interview loop.
    Returns the full interview record for use in drafting.
    """
    from resume_reader import format_context_pool

    role_brief_text = format_role_brief(role_brief)
    candidate_context = format_context_pool(context_pool)
    assessment_text = format_assessment(assessment)

    # conversation_history holds the running exchange
    # Each entry is {"role": "assistant"|"user", "content": "..."}
    conversation_history = []
    round_number = 0
    interview_record = []

    print("\n--- Starting interview ---")
    print("Type your answers and press Enter twice when done.")
    print("Type 'skip' at any time to skip to drafting.")
    print("Aim for 8-10 sentences per answer- specific facts, numbers or outcomes.\n")

    while True:
        round_number += 1

        # After round 3, summarize early history to manage tokens
        if round_number == 4:
            print("\n[Summarizing early rounds to manage context...]\n")
            conversation_history = summarize_early_rounds(
                conversation_history,
                role_brief_text,
                candidate_context
            )

        # Build the prompt for this round
        system_prompt = build_interview_system_prompt(
            role_brief_text,
            assessment_text,
            candidate_context,
            round_number
        )

        # Call Claude with full conversation history
        response = call_claude_with_history(
            system_prompt,
            conversation_history
        )

        if not response:
            print("Error generating questions. Ending interview.")
            break

        # Check for readiness signal
        is_ready = "<ready_to_draft>" in response
        clean_response = response.replace("<ready_to_draft>", "").strip()

        # Print Claude's questions
        print(f"\n--- Round {round_number} ---")
        print(clean_response)
        print()

        # Add Claude's turn to history
        conversation_history.append({
            "role": "assistant",
            "content": clean_response
        })

        # If ready signal, ask candidate whether to proceed
        if is_ready:
            print("\n[Claude has enough context to draft. Type 'draft it' to proceed or 'keep going' to continue.]\n")

        # Get candidate response
        print("Your answer (press Enter twice when done):")
        candidate_answer = get_multiline_input()

        # Check for exit commands
        if candidate_answer.lower().strip() in ["skip", "draft", "go", "done"]:
            print("\nMoving to draft...")
            interview_record.append({
                "round": round_number,
                "questions": clean_response,
                "answer": candidate_answer
            })
            break

        # Add candidate's turn to history
        conversation_history.append({
            "role": "user",
            "content": candidate_answer
        })

        # Store round in record
        interview_record.append({
            "round": round_number,
            "questions": clean_response,
            "answer": candidate_answer
        })

    return interview_record


def build_interview_system_prompt(role_brief_text, assessment_text, candidate_context, round_number):
    """
    Builds the system prompt for each interview round.
    Adjusts instructions based on round number.
    """
    base_prompt = f"""You are a sharp resume coach conducting a targeted interview to surface experience that will strengthen a resume tailoring session.

You have already completed a hiring manager assessment. Your job is to probe the gaps and surface specifics that will let you reframe the candidate's background more effectively for this role.

ROLE BRIEF:
{role_brief_text}

HIRING MANAGER ASSESSMENT:
{assessment_text}

CANDIDATE BACKGROUND:
{candidate_context}

HOW TO INTERVIEW:
- Ask 2-3 questions per round, grouped under a single theme
- Open each round with one sentence explaining the theme and why it matters for this role
- Make questions specific — reference actual resume content or role priorities by name
- Focus on ADDRESSABLE and PARTIALLY ADDRESSABLE gaps first
- Look for bullets with outcomes but no method, or method but no outcome
- Check the candidate background carefully — if a story or angle already exists there, use it directly and skip that question
- Never re-ask something already answered in the conversation history
- For career pivots: probe for transferable experience framed in different domain language

ROUND INSTRUCTIONS:"""

    if round_number == 1:
        base_prompt += """
This is round 1. Start with the most important ADDRESSABLE gap from the assessment. One sentence on why this theme matters, then 2-3 targeted questions."""

    elif round_number == 2:
        base_prompt += """
This is round 2. Move to the next most important gap or a strength that needs more specificity. One sentence on the theme, then 2-3 questions."""

    elif round_number == 3:
        base_prompt += """
This is round 3. Cover any remaining gaps or surface specifics that are still missing. After this round, assess whether you have enough to draft a materially stronger resume."""

    else:
        base_prompt += f"""
This is round {round_number}. You have been interviewing for several rounds. Focus only on what is still genuinely missing — do not re-cover ground already addressed."""

    base_prompt += """

READINESS SIGNAL:
When you have enough to produce a materially stronger resume than the original, add <ready_to_draft> at the very end of your response — after your questions, not before. Do not add it until you genuinely have enough. Do not add it before round 3."""

    return base_prompt


def call_claude_with_history(system_prompt, conversation_history):
    """
    Calls Claude with a full conversation history.
    Used for multi-turn conversations like the interview loop.
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # If no history yet, seed with an opening instruction
    messages = conversation_history if conversation_history else [
        {"role": "user", "content": "Please begin the interview."}
    ]

    try:
        message = client.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system_prompt,
            messages=messages
        )
        return message.content[0].text

    except Exception as e:
        print(f"API error: {e}")
        return None


def summarize_early_rounds(conversation_history, role_brief_text, candidate_context):
    """
    Summarizes the first rounds of conversation into a compact paragraph.
    Replaces verbose history with a summary to manage token costs.
    Called after round 3.
    """
    history_text = "\n\n".join([
        f"{turn['role'].upper()}: {turn['content']}"
        for turn in conversation_history
    ])

    system_prompt = """Summarize the following interview conversation into a compact paragraph of 150 words or less. 
Focus on: what gaps were probed, what specific experiences or stories the candidate shared, and what reframing angles emerged.
Return only the summary paragraph — no preamble, no labels."""

    user_message = f"""ROLE BRIEF CONTEXT:
{role_brief_text}

CONVERSATION TO SUMMARIZE:
{history_text}"""

    summary = call_claude(system_prompt, user_message)

    if not summary:
        return conversation_history

    # Replace full history with summary as a single user turn
    return [{"role": "user", "content": f"[Summary of earlier rounds]: {summary}"}]


def format_assessment(assessment):
    """
    Formats the assessment dictionary into readable text for prompts.
    """
    sections = []
    for key, value in assessment.items():
        if value:
            label = key.replace("_", " ").upper()
            sections.append(f"{label}:\n{value}")
    return "\n\n".join(sections)


def get_multiline_input():
    """
    Collects multiline input from the candidate.
    User presses Enter twice to submit.
    """
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    return "\n".join(lines[:-1]).strip()
def build_draft(role_brief, assessment, interview_record, context_pool, user_id=config.DEFAULT_USER_ID):
    """
    Takes all pipeline outputs and produces a tailored resume draft.
    """
    from resume_reader import format_context_pool

    role_brief_text = format_role_brief(role_brief)
    assessment_text = format_assessment(assessment)
    interview_text = format_interview_record(interview_record)
    candidate_context = format_context_pool(context_pool)

    user_message = f"""Here is everything gathered so far:

ROLE BRIEF:
{role_brief_text}

HIRING MANAGER ASSESSMENT:
{assessment_text}

INTERVIEW RECORD:
{interview_text}

CANDIDATE BACKGROUND:
{candidate_context}"""

    system_prompt = """You are an expert resume writer producing a tailored resume draft.

Your job is to rewrite the candidate's most recent 3-4 roles to best position them for the target role. Use everything from the role brief, assessment, and interview record to inform your rewriting.

SCOPE:
- Include last 3-4 positions only
- Reproduce the summary/headline exactly as written — never touch it
- Always include an AI Fluency / Projects section if present
- Collapse earlier experience to brief descriptive lines

SOURCE RULES:
- Every claim must trace to the candidate background or interview record
- Never fabricate metrics, tools, titles, outcomes, or scope
- Omit rather than inflate when evidence is weak

WRITING RULES — always apply:
- Lead with impact, follow with method or scale
- Strong verbs: Defined, Launched, Owned, Built, Drove, Shipped, Reduced, Grew, Established, Created, Initiated, Led
- Never use: Spearheaded, Leveraged, Harnessed, Revolutionized, "Responsible for", "Worked on"
- Never use dashes (— or –) to connect clauses — use conjunctions or prepositions instead
- Never use filler qualifiers: "solo", "single-handedly", "personally", "directly"
- Each bullet makes one primary claim with one supporting detail
- Never pack multiple clauses into one long sentence

REORDERING:
- Within each role, lead with bullets most relevant to this role's priorities
- Mirror the JD's vocabulary where honest
- Translate T&S or domain-specific language into the target function's vocabulary

CONFIDENTIALITY:
- Never reference internal incident triggers, data spikes, or sensitive operational details
- Frame the solution and the skill — not the trigger

WORD COUNT:
- Target ~220 words per major role
- Flag if any role exceeds this before outputting

Return the draft inside a single XML tag:
<draft>
[full resume draft here]
</draft>"""

    print("\nGenerating resume draft...")
    response = call_claude(system_prompt, user_message)

    if not response:
        return None

    draft = extract_tag(response, "draft")
    if not draft:
        print("Warning: could not extract draft from response")
        return None

    return draft


def run_fact_check(draft, interview_record, context_pool):
    """
    Checks every claim in the draft against source material.
    Every metric, number, or percentage traces to the source material
    Returns a list of flags for the candidate to review.
    """
    from resume_reader import format_context_pool

    candidate_context = format_context_pool(context_pool)
    interview_text = format_interview_record(interview_record)

    user_message = f"""Here is the resume draft to fact check:

{draft}

Here is the source material to check against:

CANDIDATE BACKGROUND:
{candidate_context}

INTERVIEW RECORD:
{interview_text}"""

    system_prompt = """You are a meticulous fact checker reviewing a resume draft against source material.

For every specific claim in the draft, verify:
- Every metric, number, or percentage traces to the source material
- Every claim must trace to the candidate background, experience stories, or interview record
- No two separate facts have been merged into a single claim
- No outcome has been attributed to a cause that was not confirmed
- No bullet references confidential internal data or sensitive operational details
- No dashes (— or –) used to connect clauses within bullets

For each flag, return it in this format inside a <flags> tag:

<flags>
BULLET: [quote the bullet]
ISSUE: [explain specifically what is unverifiable or problematic]
SOURCE: [what the source material actually says]
---
[next flag]
</flags>

If there are no flags, return:
<flags>
NONE
</flags>

Return only the flags tag — no preamble, no commentary."""

    print("\nRunning fact check...")
    response = call_claude(system_prompt, user_message)

    if not response:
        return None

    return extract_tag(response, "flags")


def run_humanizer(draft):
    """
    Scores how human the draft reads and flags AI-sounding patterns.
    Returns a score and list of flags.
    """
    user_message = f"""Please evaluate this resume draft:

{draft}"""

    system_prompt = """You are evaluating a resume draft for human authenticity. Score it 0-100 and identify AI-sounding patterns.

Look for:
- Formulaic bullet structure repeating identically across bullets
- Unnatural precision ("increased efficiency by 23.7%")
- Verbs or phrases no human would naturally write
- Sudden tonal shifts between sections
- Generic claims with no specificity
- Suspicious metric density — every bullet has a number
- Dashes used to connect clauses — hard flag always
- Filler qualifiers: "solo", "single-handedly", "directly"
- Bullets starting with "As a..." or "As owner of..."
- Does this read as one person's career or a collection of optimized fragments?

Return your evaluation in this format:

<humanizer>
SCORE: [0-100]
VERDICT: [PASS / NEEDS FIXES / REWORK]
FLAGS: [quoted phrase + one-line explanation, or NONE]
NARRATIVE: [2-3 sentences on overall coherence and voice]
</humanizer>

Return only the humanizer tag — no preamble."""

    print("\nRunning humanizer check...")
    response = call_claude(system_prompt, user_message)

    if not response:
        return None

    return extract_tag(response, "humanizer")


def format_interview_record(interview_record):
    """
    Formats the interview record into readable text for prompts.
    """
    if not interview_record:
        return "No interview conducted."

    sections = []
    for entry in interview_record:
        sections.append(
            f"Round {entry['round']}:\n"
            f"QUESTIONS: {entry['questions']}\n"
            f"ANSWER: {entry['answer']}"
        )
    return "\n\n---\n\n".join(sections)

def run_humanizer_revision_loop(draft, interview_record, context_pool):
    """
    Shows humanizer flags to candidate one at a time.
    Candidate decides what to rewrite.
    Re-runs humanizer until score hits 80 or candidate approves.
    Returns the approved draft.
    """
    current_draft = draft

    max_attempts = 2
    attempt = 0

    while True:
        attempt += 1
        # Run humanizer check
        humanizer_result = run_humanizer(current_draft)

        if not humanizer_result:
            print("Humanizer check failed. Proceeding with current draft.")
            return current_draft

        # Parse score from result
        score = parse_humanizer_score(humanizer_result)

        print("\n=== HUMANIZER CHECK ===\n")
        print(humanizer_result)
        print()

        if score >= 80:
            print(f"\nScore {score}/100 — PASS. Resume reads as human-written.")
            return current_draft
        if attempt >= max_attempts:
            print(f"\nReached maximum rewrite attempts ({max_attempts}).")
            print("Showing final flags for your review.")
            print()
            print("Options:")
            print("  Type 'accept' to proceed with current draft")
            print("  Type 'rewrite all' for one more Claude attempt")
            print()
            candidate_input = input("Your choice: ").strip().lower()
            if candidate_input == "accept":
                return current_draft
            elif candidate_input == "rewrite all":
                attempt = 0

        # Below 80 — show flags and ask candidate what to do
        print(f"\nScore {score}/100 — below threshold of 80.")
        print("Review the flags above.")
        print()
        print("Options:")
        print("  Type 'rewrite [flag number]' to rewrite a specific flag")
        print("  Type 'accept' to accept the draft as-is despite the score")
        print("  Type 'rewrite all' to let Claude fix all flags automatically")
        print()

        candidate_input = input("Your choice: ").strip().lower()

        if candidate_input == "accept":
            print("\nAccepting draft as-is.")
            return current_draft

        elif candidate_input == "rewrite all":
            print("\nRewriting flagged sections...")
            current_draft = rewrite_flagged_sections(
                current_draft, humanizer_result
            )

        elif candidate_input.startswith("rewrite"):
            # For now treat any rewrite command as rewrite all
            # In v2 we can add per-flag selection
            print("\nRewriting flagged sections...")
            current_draft = rewrite_flagged_sections(
                current_draft, humanizer_result
            )

        else:
            print("I didn't understand that. Type 'rewrite all', 'accept', or 'rewrite [number]'.")


def rewrite_flagged_sections(draft, humanizer_result):
    """
    Sends flagged sections back to Claude for rewriting.
    Returns updated draft.
    """
    user_message = f"""Here is a resume draft that has been flagged for AI-sounding patterns:

DRAFT:
{draft}

HUMANIZER FLAGS:
{humanizer_result}

Please rewrite only the flagged sections to sound more natural and human. 

Apply these fixes:
- Vary sentence structure — not every bullet starts with "Built a..."
- Replace unnatural precision with rounded numbers where appropriate
- Remove filler phrases like "acted as", "responsible for"
- Replace dashes connecting clauses with conjunctions or prepositions
- Reduce jargon density in any bullet that feels overly corporate

Return the full updated resume inside a <draft> tag.
Do not change anything that was not flagged.
Do not add new content — only rewrite flagged sections."""

    system_prompt = """You are a professional resume editor. Your job is to make flagged sections sound more natural and human-written while preserving all factual content and impact. Never add new claims. Never remove metrics. Only change phrasing."""

    response = call_claude(system_prompt, user_message)

    if not response:
        print("Rewrite failed. Keeping current draft.")
        return draft

    new_draft = extract_tag(response, "draft")
    if not new_draft:
        print("Could not extract rewritten draft. Keeping current.")
        return draft

    print("Draft updated.")
    return new_draft

def parse_humanizer_score(humanizer_result):
    try:
        for line in humanizer_result.split("\n"):
            if line.startswith("SCORE:"):
                score_str = line.replace("SCORE:", "").strip()
                # Handle both "72" and "72/100" formats
                score_str = score_str.split("/")[0].strip()
                return int(score_str)
    except Exception:
        pass
    return 0