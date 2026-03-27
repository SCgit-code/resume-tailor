# Resume Tailor

An AI-powered resume tailoring tool that takes a job posting URL and produces 
a tailored resume draft through automated research, gap analysis, and 
iterative interview.

## Brand

**Name:** Taylor  
**Tagline:** Your story. Perfectly fitted.  
**Colors:** Navy (#1a2744) + White  

**Logo status:** Current logo in `static/logo.svg` is a placeholder generated programmatically. 
Final wordmark (with Y as necktie knot shape) and icon (necktie knot in circle) 
to be replaced with assets designed in Figma/Canva.  

**Logo specs for designer:**
- Wordmark: TAYLOR, serif font, navy, Y replaced by Windsor knot tie shape (lapels spread upward, knot center, short blade drop)
- Icon: Navy circle, white necktie knot filling the circle (Da Vinci proportions — knot fills the frame)
- Tagline: same width as wordmark, left-aligned, italic serif, navy, reduced opacity
- Export needed: SVG + PNG transparent background at 2x

## Status
Working prototype — terminal-based, single user.
Web UI and Docx export in progress.

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
- Brave Search API key (1,000 queries/5$)

## Roadmap
- [ ] Web UI
- [ ] Docx export
- [ ] Role-agnostic generalization
- [ ] Candidate tone and style samples for humanizer
- [ ] Multi-user support