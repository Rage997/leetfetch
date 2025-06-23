import os
import requests
import browser_cookie3
from typing import List, Dict

GRAPHQL_URL = "https://leetcode.com/graphql"
USERNAME = "rage"  # Replace with your actual LeetCode username


def get_session_cookie() -> str:
    cookies = browser_cookie3.brave()
    for cookie in cookies:
        if cookie.name == 'LEETCODE_SESSION':
            return cookie.value
    raise Exception("Session cookie not found. Please log into LeetCode in your browser.")

def graphql_request(query: str, variables: dict, session_token: str) -> dict:
    headers = {
        'Content-Type': 'application/json',
        'Referer': 'https://leetcode.com/problemset/all/',
        'Cookie': f'LEETCODE_SESSION={session_token};'
    }
    payload = {
        "query": query,
        "variables": variables
    }
    response = requests.post(GRAPHQL_URL, json=payload, headers=headers)
    if not response.ok:
        print("GraphQL error:", response.text)
        response.raise_for_status()
    return response.json()



def get_solved_problem_slugs(session_token: str) -> List[str]:
    slugs = set()
    offset = 0
    limit = 20

    while True:
        query = """
        query mySubmissions($offset: Int!, $limit: Int!) {
          submissionList(offset: $offset, limit: $limit) {
            submissions {
              titleSlug
              statusDisplay
            }
            hasNext
          }
        }
        """
        variables = {"offset": offset, "limit": limit}
        data = graphql_request(query, variables, session_token)

        submissions = data["data"]["submissionList"]["submissions"]
        for sub in submissions:
            if sub["statusDisplay"] == "Accepted":
                slugs.add(sub["titleSlug"])

        if not data["data"]["submissionList"]["hasNext"]:
            break

        offset += limit

    return list(slugs)



def get_problem_data(slug: str, session_token: str) -> Dict:
    query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        title
        content
        codeSnippets {
          lang
          code
        }
      }
    }
    """
    variables = {"titleSlug": slug}
    data = graphql_request(query, variables, session_token)
    return data["data"]["question"]


def save_problem(problem_data: Dict):
    slug = problem_data["title"].replace(" ", "_")
    os.makedirs(slug, exist_ok=True)

    # Save problem statement
    with open(f"{slug}/README.md", "w", encoding="utf-8") as f:
        f.write(f"# {problem_data['title']}\n\n")
        f.write(problem_data['content'] or "No description available.")

    # Save Python3 code snippet if available
    for snippet in problem_data.get("codeSnippets", []):
        if snippet["lang"] == "Python3":
            with open(f"{slug}/solution.py", "w", encoding="utf-8") as f:
                f.write(snippet["code"])
            break


def main():
    session_token = get_session_cookie()
    print("Fetching solved problem slugs...")
    slugs = get_solved_problem_slugs(session_token)
    print(f"Found {len(slugs)} solved problems.")

    for slug in slugs:
        print(f"Processing {slug}...")
        problem_data = get_problem_data(slug, session_token)
        save_problem(problem_data)
    print("Done.")


# Uncomment the line below to run the script
main()
