# NextRole.Ai Multi-Agent Workflow Guide

This document visualizes how the hierarchical AI agents in **NextRole.Ai** cooperate, validate requests, and delegate tasks to handle your job hunt automatically.

---

## 1. Agent Interaction & Routing Flowchart

The following diagram tracks the flow of a user command through the security gates and sub-agent handoffs:

![Multi-Agent Workflow Flowchart](file:///c:/Users/sathw/Downloads/googlexkaggle_course/AI-Agents-Intensive-Vibe-Coding-Capstone-Project/assets/agent_workflow.png)

```mermaid
graph TD
    User([User Request]) --> Coord[Coordinator Agent]

    %% Security Gate
    Coord -->|1. Validate Action| Security[Security Agent]
    Security --> DecSecurity{Does request pass<br>safety constraints?}
    
    DecSecurity -- No --> Fail[Halt & Reject Request]
    DecSecurity -- Yes --> Success[Validation Approved]
    
    %% Handoff / Delegation
    Success --> CoordRoute[Coordinator evaluates task type]
    
    CoordRoute -->|Scraping / Alerts / Discovery| JobIntel[Job Intelligence Agent]
    CoordRoute -->|Standard Portal Applies| AppAgent[Application Agent]
    CoordRoute -->|LinkedIn Easy Apply| EasyAgent[Easy Apply Agent]

    %% Execution outputs
    JobIntel -->|Triggers Scraper| RunScrape[Scrape job listings & compute match scores]
    AppAgent -->|Spawns Subprocess| RunApp[Launch Playwright for Greenhouse/Lever]
    EasyAgent -->|Spawns Worker| RunEasy[Execute LinkedIn Form Filling loop]

    %% Colors and Styles
    style User fill:#0A84FF,stroke:#0A84FF,stroke-width:2px,color:#fff
    style Coord fill:#CDD6F4,stroke:#CBA6F7,stroke-width:2px,color:#11111B
    style Security fill:#FF453A,stroke:#FF453A,stroke-width:2px,color:#fff
    style DecSecurity fill:#F9E2AF,stroke:#F8BD96,stroke-width:1px,color:#11111B
    style Fail fill:#FF453A,stroke:#FF453A,stroke-width:2px,color:#fff
    style Success fill:#30D158,stroke:#30D158,stroke-width:1px,color:#11111B
    style CoordRoute fill:#CDD6F4,stroke:#CBA6F7,stroke-width:1px,color:#11111B
    style JobIntel fill:#FF9F0A,stroke:#FF9F0A,stroke-width:2px,color:#fff
    style AppAgent fill:#FF9F0A,stroke:#FF9F0A,stroke-width:2px,color:#fff
    style EasyAgent fill:#FF9F0A,stroke:#FF9F0A,stroke-width:2px,color:#fff
```

---

## 2. Agent Capabilities & Roles

NextRole.Ai uses a hierarchical **Coordinator-Worker** structure where the root agent orchestrates sub-agents specialized in specific tasks:

### 1. Coordinator Agent (The Controller)
* **Model**: `gemini-3.1-flash-lite`
* **Role**: Acts as the system dispatcher. It receives all instructions, monitors user choices, and directs traffic to specialized sub-agents. It prevents loops and coordinates data updates.

### 2. Security Agent (The Guardrail)
* **Role**: Validates every request before any browser window is launched or data is sent.
* **Checks performed**:
  - Validates that target URLs are legitimate job boards (prevents navigation to phishing domains).
  - Screens inputs to ensure no malicious code or scripts are injected into forms.

### 3. Job Intelligence Agent (The Scout)
* **Role**: Handles finding and ranking jobs.
* **Responsibilities**:
  - Launches background scraping of search results.
  - Matches descriptions against your uploaded resume and preferences.
  - Computes matching weights and compiles HTML alert payloads to dispatch via SMTP email.

### 4. Application Agent (The Form Specialist)
* **Role**: Orchestrates general web application automation.
* **Responsibilities**:
  - Handles application forms hosted on platforms like Greenhouse, Lever, and other company portal systems.
  - Spawns background worker instances to execute multi-step form-filling wizards.

### 5. Easy Apply Agent (The LinkedIn Specialist)
* **Role**: Manages LinkedIn-specific automation.
* **Responsibilities**:
  - Focuses specifically on LinkedIn's dynamic "Easy Apply" process.
  - Automates credential submission, handles 2FA challenge screens via the Agent Console UI, fills screening questions, and safely pauses before final submission.
