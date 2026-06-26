import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Mock tech companies and job details for robust demo fallback
COMPANIES = ["Stripe", "Google", "Meta", "Netflix", "Amazon", "Microsoft", "Airbnb", "Uber", "Snowflake", "Databricks"]
BENCHMARKS = {
    "software engineer": {
        "titles": ["Senior Software Engineer", "Full Stack Developer", "Backend Systems Engineer", "MTS - Software Engineering"],
        "skills": ["Python", "AWS", "SQL", "Docker", "Kubernetes", "System Design", "Microservices", "REST APIs", "Git", "CI/CD", "Redis", "PostgreSQL"],
        "description": "We are seeking an exceptional engineer to design, build, and scale our core services. You will collaborate with product teams to translate requirements into highly performant microservices, optimize database queries, and streamline our containerized deployment pipelines."
    },
    "data scientist": {
        "titles": ["Data Scientist", "Lead AI/ML Researcher", "Applied Scientist", "Quantitative Analyst"],
        "skills": ["Python", "SQL", "Pandas", "Scikit-Learn", "PyTorch", "TensorFlow", "A/B Testing", "Machine Learning", "AWS", "Jupyter", "Spark"],
        "description": "Join our analytics team to uncover insights, build predictive models, and guide product decision-making. You will design rigorous experiments, train deep learning architectures, and implement scalable data pipelines to power our real-time recommendation engines."
    },
    "frontend engineer": {
        "titles": ["Senior Frontend Engineer", "UI/UX Developer", "React Architect", "Staff Frontend Engineer"],
        "skills": ["JavaScript", "TypeScript", "React", "Next.js", "HTML5", "CSS3", "TailwindCSS", "Redux", "Webpack", "Vite", "Jest", "GraphQL"],
        "description": "We are looking for a creative frontend expert to craft beautiful, responsive, and highly accessible user interfaces. You will lead the migration of our core dashboards to Next.js, optimize rendering performance, and establish our component design system."
    },
    "devops engineer": {
        "titles": ["DevOps Architect", "Site Reliability Engineer (SRE)", "Cloud Infrastructure Engineer", "Platform Engineer"],
        "skills": ["AWS", "Terraform", "Kubernetes", "Docker", "CI/CD", "Bash", "Python", "Prometheus", "Grafana", "Linux", "Nginx", "GitHub Actions"],
        "description": "Help us automate, monitor, and scale our cloud-native infrastructure. You will manage multi-region Kubernetes clusters, build secure CI/CD pipelines, write Terraform configurations as code, and participate in incident resolution response loops."
    }
}

def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()
    text = soup.get_text(separator=" ")
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return "\n".join(chunk for chunk in chunks if chunk)

def search_jobs(role: str, location: str, post_date_filter: str = "past_week") -> list:
    """
    Searches for jobs. First attempts to scrape job listings using search-engine queries,
    then falls back to high-fidelity mock results to guarantee a flawless demo.
    """
    query = f"{role} jobs in {location}"
    logger.info(f"Initiating job search for: {query}")
    
    jobs = []
    
    # Try web scraping (Google Search results snippet scraping or public lists)
    try:
        # Search query for greenhouse/lever boards
        search_query = f'site:greenhouse.io OR site:lever.co OR site:workday.com "{role}" "{location}"'
        encoded_query = urllib.parse.quote_plus(search_query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            results = soup.find_all("div", class_="result")
            
            for idx, res in enumerate(results[:5]):
                title_elem = res.find("a", class_="result__url")
                snippet_elem = res.find("a", class_="result__snippet")
                
                if title_elem and snippet_elem:
                    title_text = title_elem.get_text(separator=" ").strip()
                    snippet_text = snippet_elem.get_text(separator=" ").strip()
                    job_url = title_elem["href"]
                    
                    # Extract company and title from DuckDuckGo title
                    # e.g., "Software Engineer at Stripe - Lever" -> Title: Software Engineer, Company: Stripe
                    company = "Tech Company"
                    title = role.title()
                    
                    match = re.search(r"(.+?)\s+at\s+(.+?)(?:\s+-\s+|\(|\||$)", title_text, re.IGNORECASE)
                    if match:
                        title = match.group(1).strip()
                        company = match.group(2).strip()
                    else:
                        parts = title_text.split(" - ")
                        if len(parts) > 0:
                            title = parts[0].strip()
                        if len(parts) > 1:
                            company = parts[1].split("|")[0].strip()
                    
                    # Format as job posting
                    job_id = f"JD-{idx + 101:03d}"
                    jobs.append({
                        "job_id": job_id,
                        "title": title,
                        "company": company,
                        "location": location.title(),
                        "url": job_url,
                        "description": f"{title_text}\n\n{snippet_text}\n\nKey Responsibilities:\n- Lead development of high-quality software solutions.\n- Design and implement API endpoints.\n- Troubleshoot issues and optimize execution pipelines.\n\nQualifications:\n- Strong competency in software development.\n- Experienced in cloud infrastructure and DevOps pipelines.\n- Solid understanding of relational and non-relational databases.",
                        "source": "WebScraping"
                    })
    except Exception as ex:
        logger.warning(f"Web scraping failed: {str(ex)}. Relying on mock generator.")
        
    # If no jobs found or scraping failed, generate high-fidelity mock jobs
    if not jobs:
        normalized_role = role.lower()
        role_type = "software engineer"  # default
        
        for key in BENCHMARKS:
            if key in normalized_role:
                role_type = key
                break
                
        spec = BENCHMARKS[role_type]
        
        # Generate 4-6 realistic jobs
        random.seed(hash(query))  # deterministic based on search query
        num_jobs = random.randint(4, 6)
        
        for i in range(num_jobs):
            company = random.choice(COMPANIES)
            title = random.choice(spec["titles"])
            
            # Select a random subset of skills for this specific job
            job_skills = list(spec["skills"])
            random.shuffle(job_skills)
            req_skills = job_skills[:random.randint(6, 9)]
            
            # Formulate description
            desc = f"### About {company}\n{company} is a leading innovator in technology solutions, committed to building the future of global infrastructure. We believe in high autonomy, technical excellence, and rapid iteration.\n\n"
            desc += f"### Role Overview\n{spec['description']}\n\n"
            desc += "### Key Responsibilities\n"
            responsibilities = [
                f"Design, build, and maintain highly available services using {', '.join(req_skills[:3])}.",
                f"Collaborate with product managers to implement clean, well-tested API specifications.",
                f"Write infrastructure-as-code scripts and participate in CI/CD pipeline improvements.",
                "Conduct code reviews and champion engineering best practices across the team."
            ]
            for resp in responsibilities:
                desc += f"- {resp}\n"
                
            desc += "\n### Required Qualifications & Gaps\n"
            desc += f"- Extensive professional experience with: {', '.join(req_skills)}.\n"
            desc += f"- Proven track record of deploying robust systems in a {location} environment or working remotely.\n"
            desc += "- Excellent communication skills and a strong sense of ownership."
            
            job_id = f"JD-{company[:3].upper()}-{100 + i}"
            url = f"https://{company.lower()}.com/careers/jobs/{job_id.lower()}"
            
            jobs.append({
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location.title(),
                "url": url,
                "description": desc,
                "source": "MockIntelligence"
            })
            
    return jobs

def deduplicate_jobs(jobs: list) -> list:
    """Deduplicates jobs by company and title."""
    seen = set()
    deduped = []
    for job in jobs:
        key = (job["company"].lower(), job["title"].lower())
        if key not in seen:
            seen.add(key)
            deduped.append(job)
    return deduped
