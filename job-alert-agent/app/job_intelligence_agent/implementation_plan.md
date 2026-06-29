# Job Intelligence Agent: Explanation Plan

The **Job Intelligence Agent** handles job discovery, deduplication, match score metrics, and alerts.

---

## 🔑 Key Responsibilities

1. **LinkedIn Job Scraper**:
   - Uses Playwright to search and scrape job postings matching specified keywords, location, and posting frequency.
2. **Match Scorer**:
   - Calculates weighted match percentages using Candidate Profile vs Job Description across five criteria:
     - Skills (40%)
     - Experience (25%)
     - Role Alignment (20%)
     - Education (10%)
     - Keywords (5%)
3. **Deduplicator**:
   - Filters out duplicates by comparing Company Name, Location, and URL.
4. **Email Notification Service**:
   - Formats a beautiful HTML summary email and dispatches it via SMTP to the recipient.
