<<<<<<< HEAD
<<<<<<< HEAD
# TalentAI Suite: Resume Semantic Matcher

## The Problem
In modern recruitment, matching candidates to job descriptions is highly inefficient. 
1. **High Volume:** Recruiters are inundated with hundreds of resumes for a single job posting, making manual screening nearly impossible.
2. **Keyword Disconnect:** Traditional Applicant Tracking Systems (ATS) rely on exact keyword matches. A candidate might be highly qualified but rejected simply because they used the term "Data Manipulation" instead of "Data Engineering", or "GCP" instead of "Google Cloud Platform".
3. **Generic Resumes:** Candidates often submit a single, generic resume for all applications. These generic resumes fail to highlight the specific experiences and skills relevant to the target job, making it harder for recruiters to see the alignment.
4. **Token Limits & Costs:** When using Large Language Models (LLMs) to analyze resumes, sending raw, full-length PDF text for thousands of candidates consumes massive amounts of context tokens, leading to high API costs and latency.

## The Solution
**TalentAI Suite** is an intelligent, dual-pronged recruitment platform built to solve these inefficiencies using semantic matching and generative AI.

### 1. Semantic Resume Matching (The Evaluation Phase)
Instead of exact keyword matching, the application uses **TF-IDF Vectorization and Cosine Similarity** to evaluate the semantic alignment between a candidate's resume and a scraped job description.
- **Job Scraping:** Recruiters can input a job posting URL, and the system automatically scrapes and cleans the requirements.
- **Intelligent Scoring:** The system calculates a similarity score and identifies specific "Matched Skills" and "Missing Skills" based on semantic relevance, allowing recruiters to instantly see where a candidate aligns and where gaps exist.

### 2. Token-Optimized Generative Tailoring (The Synthesis Phase)
Once a strong candidate is identified, the system helps tailor their resume to the specific job description.
- **Token Reduction via MiniLM:** Before sending the resume to the LLM, the backend uses `sentence-transformers` (all-MiniLM-L6-v2) to extract and summarize only the most essential semantic content from the raw resume. This drastically reduces the context window size, saving token costs and reducing latency.
- **Gemini-Powered Synthesis:** The summarized resume, along with the job description and required skills, is passed to **Google Gemini** (via the Google Agent Development Kit). Gemini synthesizes a brand-new, structured resume tailored specifically to highlight the candidate's experiences in the context of the target job.
- **Automated Formatting:** The generated JSON payload is automatically compiled into a professionally formatted Microsoft Word (`.docx`) file by the Streamlit frontend, ready for the recruiter to download and present to hiring managers.

## Technical Architecture
- **Frontend (`resume-matcher`):** A responsive, premium-styled **Streamlit** dashboard acting as the Recruiter Portal.
- **Backend Core (`talent_matcher`):** A modular **FastAPI** service that exposes secure endpoints for summarization and generation.
- **Agent Orchestration:** Powered by the **Google Agent Development Kit (ADK)**, the logic is encapsulated in conversational agents and tools, natively deployable to Google Cloud's Agent Runtime.
- **Security:** API Key authorization secures the connection between the frontend client and the backend agent logic.

## Setup Instructions

### Frontend
```bash
cd resume-matcher
pip install -r requirements.txt
streamlit run app.py
```

### Backend
```bash
cd talent_matcher
pip install -r requirements.txt
python run.py
```
