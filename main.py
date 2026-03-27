import config
import fetcher
import researcher
import prompter
import resume_reader
import session
import stories


def run(jd_url=None, company_name=None, candidate_notes=None,
        user_id=config.DEFAULT_USER_ID, start_from=None,
        resume_from=None):
    """
    Runs the full pipeline with pause/resume support.

    resume_from: path to a saved session file to resume from.
    start_from: skip to a specific step using saved step files.
    """
    config.init_user_dirs(user_id)

    # --- RESUME MODE ---
    if resume_from:
        state = session.load_session(resume_from)
        if not state:
            print("Could not load session. Starting fresh.")
            resume_from = None
        else:
            jd_url = state.get("jd_url")
            company_name = state.get("company_name")
            candidate_notes = state.get("candidate_notes")
            start_from = state.get("current_step")

    # Build the session state object we'll update as we go
    pipeline_state = {
        "jd_url": jd_url,
        "company_name": company_name,
        "candidate_notes": candidate_notes,
        "current_step": "context",
    }

    # Step 0: context pool — always load fresh
    print("\n=== LOADING CANDIDATE CONTEXT ===")
    context_pool = resume_reader.build_context_pool(user_id)
    if not context_pool["resumes"]:
        print("No resumes found. Please add .docx files to users/default/resumes/")
        return

    # Step 1: JD fetch
    if start_from in ["assessment", "interview", "draft"] and session.step_exists("jd_text", user_id):
        print("\n=== STEP 1: Loading saved JD ===")
        jd_text = session.load_step("jd_text", user_id)
    else:
        print("\n=== STEP 1: Fetching job description ===")
        jd_text = fetcher.fetch_jd(jd_url)
        if not jd_text:
            print("Failed to fetch job description.")
            return
        session.save_step(jd_text, "jd_text", user_id)

    pipeline_state["current_step"] = "research"
    session.save_session(pipeline_state, user_id)

    # Step 2: research
    if start_from in ["assessment", "interview", "draft"] and session.step_exists("research", user_id):
        print("\n=== STEP 2: Loading saved research ===")
        research_findings = session.load_step("research", user_id)
    else:
        print("\n=== STEP 2: Researching company ===")
        research_findings = researcher.research_company(company_name)
        session.save_step(research_findings, "research", user_id)

    pipeline_state["current_step"] = "role_brief"
    session.save_session(pipeline_state, user_id)

    # Step 3: role brief
    if start_from in ["assessment", "interview", "draft"] and session.step_exists("role_brief", user_id):
        print("\n=== STEP 3: Loading saved role brief ===")
        role_brief = session.load_step("role_brief", user_id)
    else:
        print("\n=== STEP 3: Generating role brief ===")
        role_brief = prompter.build_role_brief(jd_text, research_findings, candidate_notes)
        if not role_brief:
            print("Failed to generate role brief.")
            return
        session.save_step(role_brief, "role_brief", user_id)

    pipeline_state["current_step"] = "assessment"
    session.save_session(pipeline_state, user_id)

    # Step 4: assessment
    if start_from in ["interview", "draft"] and session.step_exists("assessment", user_id):
        print("\n=== STEP 4: Loading saved assessment ===")
        assessment = session.load_step("assessment", user_id)
    else:
        print("\n=== STEP 4: Hiring manager assessment ===")
        assessment = prompter.build_hiring_manager_assessment(
            role_brief, context_pool, user_id
        )
        if not assessment:
            print("Failed to generate assessment.")
            return
        session.save_step(assessment, "assessment", user_id)

    print("\n=== HIRING MANAGER ASSESSMENT ===\n")
    for section, content in assessment.items():
        print(f"--- {section.upper()} ---")
        print(content)
        print()

    pipeline_state["current_step"] = "interview"
    session.save_session(pipeline_state, user_id)

    # Step 5: interview
    if start_from == "draft" and session.step_exists("interview", user_id):
        print("\n=== STEP 5: Loading saved interview ===")
        interview_record = session.load_step("interview", user_id)
    else:
        print("\n=== STEP 5: INTERVIEW ===")
        interview_record = prompter.run_interview_loop(
            role_brief, assessment, context_pool, user_id
        )
        session.save_step(interview_record, "interview", user_id)

    pipeline_state["current_step"] = "draft"
    session.save_session(pipeline_state, user_id)

    # Step 6: draft
    print("\n=== STEP 6: Generating draft ===")
    draft = prompter.build_draft(
        role_brief, assessment, interview_record, context_pool, user_id
    )
    if not draft:
        print("Failed to generate draft.")
        return
    session.save_step(draft, "draft", user_id)

    print("\n=== DRAFT ===\n")
    print(draft)

    pipeline_state["current_step"] = "fact_check"
    session.save_session(pipeline_state, user_id)

    # Step 7: fact check
    print("\n=== STEP 7: Fact check ===")
    fact_flags = prompter.run_fact_check(draft, interview_record, context_pool)
    if fact_flags and fact_flags.strip() != "NONE":
        print("\n=== FACT CHECK FLAGS ===\n")
        print(fact_flags)
        print()
        candidate_input = input(
            "Review the flags above. Press Enter to continue to humanizer, "
            "or type 'revise' to go back to draft: "
        ).strip().lower()
        if candidate_input == "revise":
            print("Revision mode not yet built — proceeding to humanizer for now.")

    pipeline_state["current_step"] = "humanizer"
    session.save_session(pipeline_state, user_id)

    # Step 8: humanizer revision loop
    print("\n=== STEP 8: Humanizer check ===")
    approved_draft = prompter.run_humanizer_revision_loop(
        draft, interview_record, context_pool
    )
    session.save_step(approved_draft, "approved_draft", user_id)

    pipeline_state["current_step"] = "approval"
    session.save_session(pipeline_state, user_id)

    # Step 9: final approval gate
    print("\n=== STEP 9: Final approval ===\n")
    print(approved_draft)
    print()
    candidate_input = input(
        "Happy with this resume? Type 'yes' to save and update your "
        "experience stories, or 'revise' to make changes: "
    ).strip().lower()

    if candidate_input == "yes":
        # Save final resume immediately before anything else
        session.save_step(approved_draft, "final_resume", user_id)
        pipeline_state["current_step"] = "stories_update"
        session.save_session(pipeline_state, user_id)
        print("\nResume saved.")

        # Update stories — if this fails or is interrupted,
        # the final resume is already safely saved above
        stories.update_stories(approved_draft, interview_record, user_id)

        pipeline_state["current_step"] = "complete"
        session.save_session(pipeline_state, user_id)
        print("\nSession complete.")

    else:
        print("\nRevision mode not yet built — resume saved as draft for now.")
        session.save_step(approved_draft, "final_resume", user_id)


if __name__ == "__main__":
    print("Starting...")

    # To start fresh:
    # run(jd_url="...", company_name="...")

    # To skip to a step:
    run(
        jd_url="https://job-boards.greenhouse.io/kikoff/jobs/4147903009",
        company_name="Kikoff",
        start_from="draft"
    )

    # To resume a saved session:
    # session.list_sessions()
    # run(resume_from="users/default/sessions/session_kikoff_20260101_1200.json")