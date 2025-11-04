import fitz  
import docx
import re

def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text
def extract_github_url(text):
    match = re.search(r'https?://github\.com/[A-Za-z0-9_-]+', text)
    return match.group(0) if match else None

def extract_linkedin_url(text):
    # Match with or without https
    pattern = r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9\-_/]+"
    match = re.search(pattern, text)
    return f"https://{match.group(0).lstrip('https://')}" if match else None

import requests

import requests

def fetch_full_github_data(github_url):
    try:
        # Extract username from URL
        username = github_url.rstrip("/").split("/")[-1]

        # 1. Fetch Profile Data
        profile_url = f"https://api.github.com/users/{username}"
        profile_response = requests.get(profile_url)

        if profile_response.status_code != 200:
            return {"error": "Failed to fetch GitHub profile."}

        profile_data = profile_response.json()
        profile_info = {
            "username": profile_data.get("login"),
            "name": profile_data.get("name"),
            "bio": profile_data.get("bio"),
            "repos_count": profile_data.get("public_repos"),
            "followers": profile_data.get("followers"),
            "created_at": profile_data.get("created_at"),
            "profile_url": profile_data.get("html_url")
        }

        # 2. Fetch Repositories Data
        repos_url = f"https://api.github.com/users/{username}/repos"
        repos_response = requests.get(repos_url)

        if repos_response.status_code != 200:
            return {"error": "Failed to fetch GitHub repositories."}

        repos_data = repos_response.json()
        repositories = []

        for repo in repos_data:
            repositories.append({
                "name": repo.get("name"),
                "description": repo.get("description"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count"),
                "forks": repo.get("forks_count"),
                "url": repo.get("html_url"),
                "last_updated": repo.get("updated_at")
            })

        return {
            "profile": profile_info,
            "repositories": repositories
        }

    except Exception as e:
        return {"error": str(e)}
