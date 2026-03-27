import requests
from bs4 import BeautifulSoup
import config

def fetch_jd(url):
    """
    Takes a job posting URL and returns clean text.
    """
    print(f"Fetching: {url}")
    
    # Step 1: fetch the raw HTML
    html = fetch_html(url)
    if not html:
        return None
    
    # Step 2: extract clean text from the HTML
    text = extract_text(html)
    if not text:
        return None
        
    print(f"Successfully fetched {len(text.split())} words")
    return text


def fetch_html(url):
    """
    Makes an HTTP request to the URL and returns raw HTML.
    Returns None if anything goes wrong.
    """
    # We set a User-Agent header so the server thinks
    # we're a regular browser, not a bot
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
        
        # Check if the request succeeded
        # Status code 200 means OK, anything else is a problem
        if response.status_code != 200:
            print(f"Error: received status code {response.status_code}")
            return None
            
        return response.text
        
    except requests.exceptions.Timeout:
        print("Error: the request timed out. The site may be slow or blocking us.")
        return None
    except requests.exceptions.ConnectionError:
        print("Error: could not connect. Check the URL or your internet connection.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def extract_text(html):
    """
    Takes raw HTML and returns clean readable text.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove elements that are never useful
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()
    
    # Get all remaining text
    text = soup.get_text(separator="\n")
    
    # Clean up excessive whitespace and blank lines
    lines = [line.strip() for line in text.splitlines()]
    clean_lines = [line for line in lines if line]
    clean_text = "\n".join(clean_lines)
    
    return clean_text