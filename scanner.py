import os
import logging
import requests
import json
from jobspy import scrape_jobs
import pandas as pd
import google.generativeai as genai

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

SEARCH_CONFIGS = [
    {"search_term": "Machine Learning Engineer", "location": "India"},
    {"search_term": "AI Engineer", "location": "India"},
    {"search_term": "Data Scientist", "location": "India"},
    {"search_term": "Deep Learning Engineer", "location": "India"},
    {"search_term": "NLP Engineer", "location": "India"},
    {"search_term": "MLOps Engineer", "location": "India"},
    {"search_term": "Computer Vision Engineer", "location": "India"},
    {"search_term": "Data Analyst", "location": "India"},
    {"search_term": "Machine Learning Engineer", "location": "Remote"},
    {"search_term": "AI Engineer", "location": "Remote"},
]

JOBSPY_SITES = ["linkedin", "indeed", "glassdoor", "naukri", "google", "zip_recruiter", "bayt"]

FREE_JOB_APIS = [
    "https://remotive.com/api/remote-jobs?category=software-dev&limit=50",
    "https://jobicy.com/api/v2/remote-jobs?count=50&tag=machine-learning",
    "https://jobicy.com/api/v2/remote-jobs?count=50&tag=data-science",
    "https://jobicy.com/api/v2/remote-jobs?count=50&tag=artificial-intelligence",
]


def fetch_free_api_jobs():
    """Fetch from free public job APIs (no key needed)"""
    jobs = []

    # Remotive
    try:
        r = requests.get("https://remotive.com/api/remote-jobs?category=software-dev&limit=50", timeout=10)
        if r.status_code == 200:
            data = r.json()
            for j in data.get("jobs", []):
                title = j.get("title", "")
                if any(kw in title.lower() for kw in ["machine learning", "ml", "ai", "data science", "nlp", "deep learning", "data analyst", "python"]):
                    jobs.append({
                        "title": title,
                        "company": j.get("company_name", ""),
                        "location": "Remote",
                        "job_url": j.get("url", ""),
                        "description": j.get("description", "")[:1000],
                        "date_posted": j.get("publication_date", "")[:10],
                        "site": "Remotive"
                    })
    except Exception as e:
        logger.error(f"Remotive error: {e}")

    # Jobicy
    for tag in ["machine-learning", "data-science", "artificial-intelligence", "python"]:
        try:
            r = requests.get(f"https://jobicy.com/api/v2/remote-jobs?count=30&tag={tag}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                for j in data.get("jobs", []):
                    jobs.append({
                        "title": j.get("jobTitle", ""),
                        "company": j.get("companyName", ""),
                        "location": "Remote",
                        "job_url": j.get("url", ""),
                        "description": j.get("jobDescription", "")[:1000],
                        "date_posted": j.get("pubDate", "")[:10],
                        "site": "Jobicy"
                    })
        except Exception as e:
            logger.error(f"Jobicy error ({tag}): {e}")

    return jobs


def fetch_jobspy_jobs(search_term, location):
    """Fetch from JobSpy (LinkedIn, Indeed, Naukri, Glassdoor, Google Jobs, etc.)"""
    try:
        df = scrape_jobs(
            site_name=JOBSPY_SITES,
            search_term=search_term,
            location=location,
            results_wanted=20,
            hours_old=8,
            country_indeed="India",
        )
        if df is None or df.empty:
            return []

        jobs = []
        for _, row in df.iterrows():
            jobs.append({
                "title": str(row.get("title", "")),
                "company": str(row.get("company", "")),
                "location": str(row.get("location", "")),
                "job_url": str(row.get("job_url", "")),
                "description": str(row.get("description", ""))[:1000],
                "date_posted": str(row.get("date_posted", ""))[:10],
                "site": str(row.get("site", ""))
            })
        return jobs
    except Exception as e:
        logger.error(f"JobSpy error ({search_term}, {location}): {e}")
        return []


def score_job_with_gemini(resume_text: str, job: dict) -> int:
    """Score a job 1-10 against a resume using Gemini"""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"""You are a job matching expert. Score how well this job matches the resume on a scale of 1-10.

RESUME:
{resume_text[:2000]}

JOB TITLE: {job.get('title', '')}
COMPANY: {job.get('company', '')}
LOCATION: {job.get('location', '')}
DESCRIPTION: {job.get('description', '')[:800]}

Respond with ONLY a single integer from 1 to 10. Nothing else."""

        response = model.generate_content(prompt)
        score_text = response.text.strip()
        score = int(''.join(filter(str.isdigit, score_text))[:2])
        return min(max(score, 1), 10)
    except Exception as e:
        logger.error(f"Gemini scoring error: {e}")
        return 5


def deduplicate(jobs: list) -> list:
    seen_urls = set()
    unique = []
    for j in jobs:
        url = j.get("job_url", "")
        if url and url not in seen_urls and url != "nan" and url != "None":
            seen_urls.add(url)
            unique.append(j)
    return unique


def scan_and_score(resume_text: str) -> list:
    """Main function: scrape all platforms, score, return sorted results"""
    logger.info("Starting job scan across all platforms...")
    all_jobs = []

    # Layer 1: JobSpy
    for config in SEARCH_CONFIGS:
        jobs = fetch_jobspy_jobs(config["search_term"], config["location"])
        logger.info(f"JobSpy [{config['search_term']} / {config['location']}]: {len(jobs)} jobs")
        all_jobs.extend(jobs)

    # Layer 2: Free APIs
    free_jobs = fetch_free_api_jobs()
    logger.info(f"Free APIs: {len(free_jobs)} jobs")
    all_jobs.extend(free_jobs)

    # Deduplicate
    all_jobs = deduplicate(all_jobs)
    logger.info(f"Total unique jobs after dedup: {len(all_jobs)}")

    # Score with Gemini (only score top candidates to save API quota)
    # Filter obvious mismatches first by title keywords
    ml_keywords = ["machine learning", "ml", "ai", "data science", "data scientist",
                   "nlp", "deep learning", "computer vision", "mlops", "python",
                   "data analyst", "artificial intelligence", "llm", "neural"]

    filtered = []
    for job in all_jobs:
        title_lower = job.get("title", "").lower()
        desc_lower = job.get("description", "").lower()
        if any(kw in title_lower or kw in desc_lower for kw in ml_keywords):
            filtered.append(job)

    logger.info(f"After keyword filter: {len(filtered)} jobs to score")

    # Score each job
    scored = []
    for job in filtered[:50]:  # Cap at 50 to respect Gemini free tier
        score = score_job_with_gemini(resume_text, job)
        job["score"] = score
        scored.append(job)

    # Sort by score descending, return jobs scoring 6+
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    good_matches = [j for j in scored if j.get("score", 0) >= 6]

    logger.info(f"Good matches (6+): {len(good_matches)}")
    return good_matches
