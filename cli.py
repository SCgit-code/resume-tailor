import sys
import os
import config
import session


def main():
    """
    Main entry point for the CLI.
    Handles both interactive mode and command line arguments.
    """
    # Check for command line arguments first
    args = parse_args()

    if args.get("url") and args.get("company"):
        # Non-interactive mode — arguments provided
        run_with_args(args)
    else:
        # Interactive mode — ask the user
        run_interactive()


def parse_args():
    """
    Parses command line arguments if provided.
    Supports: --url, --company, --notes, --resume-from
    Returns a dictionary of arguments.
    """
    args = {}
    argv = sys.argv[1:]  # Skip the script name

    i = 0
    while i < len(argv):
        if argv[i] == "--url" and i + 1 < len(argv):
            args["url"] = argv[i + 1]
            i += 2
        elif argv[i] == "--company" and i + 1 < len(argv):
            args["company"] = argv[i + 1]
            i += 2
        elif argv[i] == "--notes" and i + 1 < len(argv):
            args["notes"] = argv[i + 1]
            i += 2
        elif argv[i] == "--resume-from" and i + 1 < len(argv):
            args["resume_from"] = argv[i + 1]
            i += 2
        else:
            i += 1

    return args


def run_interactive():
    """
    Guides the user through setup interactively.
    """
    print_header()

    choice = show_main_menu()

    if choice == "1":
        start_new_session()
    elif choice == "2":
        resume_saved_session()
    elif choice == "3":
        session.list_sessions()
        print()
        run_interactive()
    else:
        print("Invalid choice. Please try again.")
        run_interactive()


def print_header():
    """
    Prints the tool header.
    """
    print("\n" + "=" * 40)
    print("         RESUME TAILOR")
    print("=" * 40 + "\n")


def show_main_menu():
    """
    Shows the main menu and returns the user's choice.
    """
    print("What would you like to do?\n")
    print("  1. Start new session")
    print("  2. Resume saved session")
    print("  3. List saved sessions")
    print()
    return input("Your choice (1/2/3): ").strip()


def start_new_session():
    """
    Collects inputs for a new session interactively.
    """
    import main as pipeline

    print("\n--- New Session ---\n")

    # Get JD URL
    jd_url = ""
    while not jd_url:
        jd_url = input("Job posting URL: ").strip()
        if not jd_url:
            print("URL is required.")

    # Get company name
    company_name = ""
    while not company_name:
        company_name = input("Company name: ").strip()
        if not company_name:
            print("Company name is required.")

    # Optional notes
    print("Any notes about this role? (press Enter to skip)")
    candidate_notes = input("> ").strip() or None

    print()
    pipeline.run(
        jd_url=jd_url,
        company_name=company_name,
        candidate_notes=candidate_notes
    )


def resume_saved_session():
    """
    Shows saved sessions and lets user pick one to resume.
    """
    import main as pipeline

    session_files = session.list_sessions()

    if not session_files:
        print("\nNo saved sessions found. Starting new session instead.\n")
        start_new_session()
        return

    print()
    choice = input("Enter session number to resume (or press Enter to go back): ").strip()

    if not choice:
        run_interactive()
        return

    try:
        index = int(choice) - 1
        if index < 0 or index >= len(session_files):
            print("Invalid selection.")
            resume_saved_session()
            return

        # Get the full path of the selected session
        sessions_dir = config.get_sessions_dir()
        selected_file = sorted(session_files, reverse=True)[index]
        filepath = os.path.join(sessions_dir, selected_file)

        pipeline.run(resume_from=filepath)

    except ValueError:
        print("Please enter a number.")
        resume_saved_session()


def run_with_args(args):
    """
    Runs the pipeline with command line arguments.
    """
    import main as pipeline

    if args.get("resume_from"):
        pipeline.run(resume_from=args["resume_from"])
    else:
        pipeline.run(
            jd_url=args["url"],
            company_name=args["company"],
            candidate_notes=args.get("notes")
        )


if __name__ == "__main__":
    main()