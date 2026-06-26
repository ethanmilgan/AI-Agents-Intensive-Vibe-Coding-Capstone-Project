from ..tools.parser_tool import extract_text_from_bytes
from ..tools.summarizer_tool import summarize_resume_tool

class SummarizationTask:
    """
    Orchestrates candidate resume parsing and token reduction.
    """
    @staticmethod
    def execute(file_bytes: bytes, filename: str) -> dict:
        raw_text = extract_text_from_bytes(file_bytes, filename)
        summary = summarize_resume_tool(raw_text)
        return {
            "raw_text": raw_text,
            "summary": summary
        }

class ResumeGenerationTask:
    """
    Defines the parameters for the tailoring model agent run.
    """
    def __init__(self, job_id: str, job_desc: str, job_skills: str, resume_summary: str):
        self.job_id = job_id
        self.job_desc = job_desc
        self.job_skills = job_skills
        self.resume_summary = resume_summary

class InterviewPrepTask:
    """
    Defines the parameters for the interview prep generation.
    """
    def __init__(self, job_id: str, job_desc: str, resume_summary: str):
        self.job_id = job_id
        self.job_desc = job_desc
        self.resume_summary = resume_summary
