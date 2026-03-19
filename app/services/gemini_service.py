import google.generativeai as genai
import json
from app.core.config import get_settings

settings = get_settings()

genai.configure(api_key=settings.gemini_api_key)

model = genai.GenerativeModel("gemini-2.5-flash")


def _extract_json_block(raw_text: str) -> str:
    stripped = raw_text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stripped[start : end + 1]
    return stripped


def summarize_reviews(comments: list[str]) -> str:
    if not comments:
        return "No reviews available."

    prompt = f"""
    Summarize the following movie reviews in a concise way:

    Reviews:
    {" ".join(comments)}

    Provide a short summary of overall sentiment, highlights, and issues.
    """

    response = model.generate_content(prompt)
    return response.text.strip()


def recommend_movies_from_library(library_items: list[dict], max_recommendations: int = 10) -> list[dict]:
    if not library_items:
        return []

    prompt = f"""
    You are a movie and TV recommendation assistant.

    Use the user's current library and optional ratings to suggest new titles.
    Prefer recommendations that match genres, tone, and rating preferences.

    Return ONLY valid JSON with this exact structure:
    {{
      "recommendations": [
        {{"title": "...", "media_type": "movie" or "tv", "reason": "..."}}
      ]
    }}

    Rules:
    - Recommend up to {max_recommendations} items.
    - Do not recommend titles that already exist in the input library.
    - Keep each reason under 180 characters.
    - Output JSON only, no markdown, no explanation.

    Library input:
    {json.dumps(library_items, ensure_ascii=True)}
    """

    response = model.generate_content(prompt)
    raw_text = (response.text or "").strip()
    if not raw_text:
        return []

    try:
        parsed = json.loads(_extract_json_block(raw_text))
        recommendations = parsed.get("recommendations", []) if isinstance(parsed, dict) else []
    except (json.JSONDecodeError, AttributeError):
        recommendations = []

    normalized: list[dict] = []
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        media_type = str(item.get("media_type", "")).strip().lower()
        reason = str(item.get("reason", "")).strip()
        if not title or not reason or media_type not in {"movie", "tv"}:
            continue
        normalized.append(
            {
                "title": title,
                "media_type": media_type,
                "reason": reason,
            }
        )

    return normalized[:max_recommendations]