import pypdf
import docx2txt
import io
from fastapi import HTTPException

def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Extracts text content from uploaded file bytes (supports PDF, DOCX, and TXT formats).
    """
    filename_lower = filename.lower()
    if filename_lower.endswith(".pdf"):
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    elif filename_lower.endswith(".docx"):
        return docx2txt.process(io.BytesIO(file_bytes))
    elif filename_lower.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Upload PDF, DOCX or TXT only.")
