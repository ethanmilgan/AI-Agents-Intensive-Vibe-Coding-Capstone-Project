import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from talent_matcher.api.routes import router
from talent_matcher.config.config_loader import app_config

app = FastAPI(
    title="TalentMatcher API",
    description="Agentic Backend for Resume Summarization (MiniLM) and Tailored LLM Synthesis",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

if __name__ == "__main__":
    host = app_config.get("serverHost", "127.0.0.1")
    port = int(app_config.get("serverPort", "8000"))
    uvicorn.run("run:app", host=host, port=port, reload=True)
