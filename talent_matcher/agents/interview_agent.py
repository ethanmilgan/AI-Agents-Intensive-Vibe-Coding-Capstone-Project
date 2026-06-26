import os
import json
import logging
import google.generativeai as genai
from ..prompts.templates import INTERVIEW_PREP_PROMPT
from ..tasks.match_tasks import InterviewPrepTask
from ..config.config_loader import app_config

logger = logging.getLogger(__name__)

class InterviewPrepAgent:
    """
    Agent responsible for interfacing with Gemini to synthesize an interview prep guide.
    """
    def __init__(self, model_name: str = None):
        self.model_name = model_name or app_config.get("geminiModel", "gemini-1.5-flash")
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def run(self, task: InterviewPrepTask) -> dict:
        try:
            model = genai.GenerativeModel(self.model_name)
            
            prompt = INTERVIEW_PREP_PROMPT.format(
                job_id=task.job_id,
                job_desc=task.job_desc,
                resume_summary=task.resume_summary
            )
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            return json.loads(text)
            
        except Exception as ex:
            logger.warning(f"Agent failed to synthesize interview prep: {str(ex)}. Applying fallback.")
            return self._run_fallback(task)

    def _run_fallback(self, task: InterviewPrepTask) -> dict:
        return {
            "candidate_profile_analysis": "Candidate shows strong foundational experience but may lack specific modern framework expertise. Their tenure demonstrates reliability.",
            "technical_questions": [
                {
                    "question": "Can you walk me through a time you had to optimize a slow-performing system?",
                    "rationale": "To evaluate their practical problem-solving skills which align with the target role's demands."
                }
            ],
            "behavioral_questions": [
                {
                    "question": "Describe a situation where you had to adapt to a sudden change in project requirements.",
                    "rationale": "Assesses adaptability and resilience, critical for fast-paced environments."
                }
            ]
        }
