import requests
import config
from fetcher import fetch_html, extract_text


def research_company(company_name):
    """
    Takes a company name.
    Returns a list of research findings from 3 targeted searches.
    """
    print(f"\nResearching {company_name}...")

    queries = [
        f"{company_name} official website about mission product",
        f"{company_name} funding stage size crunchbase",
        f"{company_name} news 2025",
    ]

    all_findings = []
    for i, query in enumerate(queries):
        print(f"Searching: {query}")
        results = brave_search(query)
        if results:
            top_result = get_top_result(
                results,
                prefer_official=(i == 0),
                company_name=company_name
            )
            if top_result:
                # Try full page fetch first
                content = fetch_page_content(top_result["url"])
                # Fall back to snippet if fetch fails
                if not content:
                    content = top_result.get("snippet")
                    if content:
                        print(f"Using snippet fallback for: {top_result['url']}")
                if content:
                    all_findings.append({
                        "query": query,
                        "source": top_result["url"],
                        "title": top_result["title"],
                        "content": content[:2000]
                    })

    if not all_findings:
        print("Warning: no research findings retrieved")
        return None

    print(f"Successfully gathered {len(all_findings)} sources")
    return all_findings


def brave_search(query):
    """
    Sends a query to Brave Search API.
    Returns a list of results with title, url, and snippet.
    """
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": config.BRAVE_API_KEY
    }

    params = {
        "q": query,
        "count": 3
    }

    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=config.REQUEST_TIMEOUT
        )

        if response.status_code != 200:
            print(f"Brave API error: status code {response.status_code}")
            return None

        data = response.json()

        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", "")
            })

        return results

    except Exception as e:
        print(f"Search error: {e}")
        return None


def get_top_result(results, prefer_official=False, company_name=None):
    """
    Returns the best result from a list.
    If prefer_official, tries to find the company's own domain first.
    """
    if not results:
        return None

    if prefer_official and company_name:
        company_slug = company_name.lower().replace(" ", "")
        for result in results:
            if company_slug in result["url"].lower():
                return result

    return results[0]


def fetch_page_content(url):
    """
    Fetches and cleans content from a URL.
    Reuses the functions we already built in fetcher.py.
    """
    try:
        html = fetch_html(url)
        if not html:
            return None
        text = extract_text(html)
        return text
    except Exception as e:
        print(f"Could not fetch {url}: {e}")
        return None