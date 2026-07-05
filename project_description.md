# NextRole.Ai Project Description

This document provides a concise overview of the core components and architectures currently implemented in the NextRole.Ai project.

---

### 1. Multi-Agents using ADK
NextRole.Ai uses the Google Agent Development Kit (ADK) to establish a hierarchical multi-agent structure. The system defines a parent Coordinator Agent (`root_agent`) that manages orchestration and delegates specific tasks like safety validation, job searching, and form automation to modular sub-agents.

### 2. Security Features
Security is enforced by a dedicated Security Agent that acts as the final validation gate before any browser task runs. It restricts virtual browser navigation strictly to `linkedin.com` and `www.linkedin.com`, whitelists allowed interaction steps, enforces application limits, and prevents sensitive resume information from being logged.

### 3. Agent Skills
System capabilities are split into specialized sub-agents with dedicated skills: the Job Intelligence Agent handles board scraping and SMTP email alerting; the Application and Easy Apply Agents manage background browser form-filling automation; and the Security Agent executes safety guardrails.
