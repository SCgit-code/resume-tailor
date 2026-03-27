# Resume Tailor

An AI-powered resume tailoring tool that takes a job posting URL and produces 
a tailored resume draft through automated research, gap analysis, and 
iterative interview.

## Status
Working prototype — terminal-based, single user.
Web UI and Google Docs export in progress.

## What it does
1. Fetches and analyzes any job posting URL
2. Researches the company automatically
3. Produces a hiring manager assessment of your resume vs the role
4. Runs a targeted interview to surface relevant experience
5. Drafts a tailored resume with fact checking and humanizer validation
6. Builds a compounding experience stories library across sessions

## Setup
1. Clone the repo
2. Create a virtual environment: `python3 -m venv venv`
3. Activate it: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your API keys:
```
ANTHROPIC_API_KEY=your_key_here
BRAVE_API_KEY=your_key_here
```
6. Add your resume(s) as `.docx` files to `users/default/resumes/`
7. Run: `python3 main.py`

## Requirements
- Python 3.10+
- Anthropic API key
- Brave Search API key (free tier: 2,000 queries/month)

## Roadmap
- [ ] Web UI
- [ ] Google Docs export
- [ ] Role-agnostic generalization
- [ ] Candidate tone and style samples for humanizer
- [ ] Multi-user support