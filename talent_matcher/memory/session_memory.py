class SessionMemory:
    """
    In-memory state manager to cache candidate profiles and resume summaries.
    Avoids duplicate processing and serves as simple runtime persistence.
    """
    def __init__(self):
        self.summaries = {}     # Key: filename, Value: summary text
        self.history = []       # List of past generation metadata dicts

    def store_summary(self, filename: str, summary: str):
        self.summaries[filename] = summary

    def get_summary(self, filename: str) -> str:
        return self.summaries.get(filename)

    def log_generation(self, job_id: str, candidate_name: str, score: int):
        self.history.append({
            "job_id": job_id,
            "candidate": candidate_name,
            "score": score
        })

    def get_history(self):
        return self.history

    def clear(self):
        self.summaries.clear()
        self.history.clear()

# Global memory instance
memory_store = SessionMemory()
