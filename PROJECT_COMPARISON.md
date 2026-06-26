# Project Comparison Report: Project 1 vs. Project 2

This report compares the specifications of **Project 1** (defined in `implementation_plan.md`, `.agents-cli-spec.md`, and `frontend_spec.md`) and **Project 2** (defined in `PROJECT_PLAN.md`).

---

## 1. Architectural & Structural Differences

The primary difference lies in the **agent count and consolidation of responsibilities**.

| Dimension | Project 1 (5-Agent Setup) | Project 2 (4-Agent Setup) |
| :--- | :--- | :--- |
| **Orchestration** | 1 Parent + 4 Specialist Subagents | 1 Parent + 3 Specialist Subagents |
| **Agent Roles** | 1. **Coordinator Agent** (Parent)<br>2. **ATS Analyzer Agent**<br>3. **Resume Builder Agent**<br>4. **Job Alerts Agent**<br>5. **Form Filler Agent** | 1. **Coordinator Agent** (Parent)<br>2. **Resume Agent** (Consolidated)<br>3. **Job Intelligence Agent** (Consolidated)<br>4. **Application Agent** (Consolidated) |
| **Consolidation Details** | Splits resume tasks into two separate agents (ATS scoring vs. content styling/customization). Splits job scraping/matching tasks. | Merges ATS Analysis and Resume Building/Optimization into the **Resume Agent**. Merges Job Scrapes, Matching, and Email Alert prep into the **Job Intelligence Agent**. |
| **Workflow Control** | Less formal state transitions; agents operate as distinct services. | Strictly enforced workflow order controlled by the parent Coordinator Agent with structured state records. |

---

## 2. Feature & Capability Mapping

### A. What is in Project 1 but MISSING in Project 2?
*   **Visual Style Copier**: Project 1's Resume Builder can emulate layout structures (e.g., 2-column sidebar vs. 1-column list) and typography choices from uploaded PDF/Docx visual templates, and inherit CSS rules from HTML templates. Project 2 only mentions standard exports.
*   **Additional Job Search Deliverables**: Project 1 generates **Custom Cover Letters**, **Recruiter Outreach Messages** (LinkedIn connection requests), and drafts answers to custom screening questions directly visible on the Streamlit UI with copy-to-clipboard options.
*   **Playwright Cookie Session State Management**: Project 1 details using a persistent browser context to save LinkedIn session cookies in `playwright_session/` to bypass daily multi-factor/login gates for automated scrapers.
*   **Paraphrasing Agent / Answer Polisher**: Project 1 utilizes a specialized paraphraser to polish raw user answers (from human-in-the-loop prompts) into professional responses before filling them into the form.

### B. What is in Project 2 but MISSING in Project 1?
*   **Threshold-Based Auto-Apply Filtering**: Project 2 implements a strict auto-apply threshold. Only jobs exceeding a user-defined match percentage are routed to the Application Agent.
*   **Lower-Match Review & Re-Match Workflow**:
    *   For jobs *below* the threshold, the system displays missing skills/keywords.
    *   It prompts the user to confirm if they have experience with these missing skills and write brief notes.
    *   It updates the resume *only* with these confirmed, truthful facts.
    *   It re-scoring the jobs; if the new match meets the threshold, they are automatically routed to be applied to.
*   **Explicit State Schema**: Project 2 defines the precise data models to persist (e.g., `candidate_profile`, `resume_versions`, `ats_scores`, `auto_apply_enabled`, `application_threshold`, `application_log`, `missing_skill_responses`, `email_alert_settings`, `audit_log`).
*   **Detailed Application Logging & Screenshots**: Project 2 includes specific tools/actions like `capture_application_screenshot` and logs application outcomes into clear statuses (`applied`, `skipped`, `failed`, `unsupported`, `needs user input`).
*   **Truthfulness Guardrails**: Project 2 has strict rules prohibiting the fabrication of credentials, education, or skills.

---

## 3. Recommendations: What is Best to Implement?

For common components, here is a recommendation on which version/approach is best to implement:

### 🚀 1. Agent Architecture: Choose Project 2 (4-Agent Consolidated Setup)
> [!TIP]
> **Why?** Having 4 agents reduces LLM API token consumption, prompt complexity, and latency. Merging ATS evaluation and resume builder tasks into a single **Resume Agent** ensures a unified context when writing resume updates.

### 🔑 2. Login Persistence: Choose Project 1 (Persistent Cookie Context)
> [!IMPORTANT]
> **Why?** Scraping LinkedIn or other portals repeatedly will trigger 2FA or bot detection. Preserving cookies in `playwright_session/` is essential to prevent the scraper from breaking daily.

### ✍️ 3. HITL Form Filling: Combine Project 1's Polisher + Project 2's Log
> [!TIP]
> **Why?** Project 1's **Paraphrasing Agent** is highly valuable because user answers on the fly are often short and informal (e.g., "yes 2 yrs in sql"). Translating this into professional prose before inputting it into the form improves application quality. Meanwhile, Project 2's detailed status logging (`needs user input`, `failed`, etc.) is better for tracking application state.

### 📈 4. Tailoring & Matching: Choose Project 2 (Threshold & Lower-Match Re-Scoring)
> [!TIP]
> **Why?** The **Lower-Match Review & Re-Match** loop is a highly intelligent, interactive feature. It allows the candidate to safely expand their resume with real experience they might have omitted, driving up application matches organically and truthfully.

### 🎨 5. Resume Styling: Start with Project 2 (Standard Templates), defer Project 1 (Style Copier)
> [!WARNING]
> **Why?** A visual style copier (parsing a PDF layout and matching its visual styling to compiled HTML/CSS) is highly error-prone and complex. It is better to start with predefined CSS themes (*Modern*, *Minimalist*, *Creative*) and implement standard HTML-to-PDF / Docx exports first.
