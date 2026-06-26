import re
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Load sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def split_into_sentences(text):
    """
    Split text into clean, distinct sentences.
    """
    sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]

def summarize_resume_tool(resume_text, num_sentences=20):
    """
    Summarize a resume using sentence embedding matching against targeted context queries.
    It reduces tokens for LLM interactions.
    """
    sentences = split_into_sentences(resume_text)
    if len(sentences) <= num_sentences:
        return resume_text

    queries = [
        "Professional work experience, job duties and key achievements.",
        "Technical skills, programming languages, databases and tools.",
        "System architectures, cloud engineering, projects led.",
        "Educational qualifications, degrees, certifications."
    ]

    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
    query_embeddings = model.encode(queries, convert_to_tensor=True)

    cosine_scores = util.cos_sim(sentence_embeddings, query_embeddings)
    max_scores = np.max(cosine_scores.cpu().numpy(), axis=1)

    top_indices = np.argsort(max_scores)[-num_sentences:]
    top_indices.sort()

    summarized_sentences = [sentences[idx] for idx in top_indices]
    return "\n\n".join(summarized_sentences)
