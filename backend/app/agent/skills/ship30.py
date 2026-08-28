import logging
from app.rag.retriever import retrieve
from app.llm.provider import get_llm_client
from app.config import settings

logger = logging.getLogger(__name__)

SHIP30_SYSTEM_PROMPT = """You are an expert essayist trained in the Ship 30 for 30 writing methodology. Your job is to transform grounded knowledge into a polished, publishable essay following these exact principles:

STRUCTURE:
- Strong hook in the first 1-2 sentences — a bold claim, surprising fact, or provocative question that stops the scroll
- Clear narrative progression: don't just list facts, build an argument or story arc
- End with ONE specific, actionable takeaway the reader can apply immediately

FORMATTING (skimmable, not a wall of text):
- Use descriptive headings (##) to break up sections
- Use bullet points for lists of tactics, examples, or comparisons
- Use **bold** sparingly on the 3-5 most important phrases or claims — not every sentence
- Short paragraphs: 2-4 sentences max
- Vary sentence length for rhythm — mix short punchy lines with longer explanatory ones

CONTENT RULES:
- Every claim MUST be grounded in the provided transcript context — do not invent facts, numbers, or quotes
- Cite the source episode naturally in the prose (e.g., "As [Guest] explained on Lenny's Podcast...")
- Target length: approximately 1,250 words
- Voice: confident, direct, practical — write like a practitioner sharing hard-won lessons, not an academic

Do not include a title as an H1 — start directly with the hook. Do not add a meta-commentary intro like "Here's an essay about...". Just write the essay.

CONTEXT FROM LENNY'S PODCAST TRANSCRIPTS:
{context}
"""


def build_context(chunks: list[dict]) -> str:
    if not chunks:
        return "(no relevant transcript excerpts found)"
    parts = []
    for c in chunks:
        parts.append(f"[Episode: {c['episode_title']}]\n{c['chunk_text']}\n(source: {c['source_url']})")
    return "\n\n---\n\n".join(parts)


def run_ship30_skill(topic: str) -> dict:
    """Generates a Ship 30 for 30-style essay grounded in retrieved transcript chunks."""
    try:
        chunks, sufficient = retrieve(topic, top_k=8, similarity_threshold=0.25)
    except Exception:
        logger.exception("ship30 retrieval failed")
        raise

    context = build_context(chunks)
    system_prompt = SHIP30_SYSTEM_PROMPT.format(context=context)

    client = get_llm_client()
    essay = client.generate(
        messages=[{"role": "user", "content": f"Write a Ship 30 for 30-style essay about: {topic}"}],
        system=system_prompt,
        max_tokens=2500,
    )

    sources = [{"episode_title": c["episode_title"], "source_url": c["source_url"]} for c in chunks]
    return {
        "essay": essay,
        "sources": sources,
        "sufficient_context": sufficient,
        "model_used": settings.LLM_PROVIDER,
    }