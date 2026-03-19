import google.generativeai as genai
from app.core.config import get_settings

settings = get_settings()

genai.configure(api_key=settings.gemini_api_key)

model = genai.GenerativeModel("gemini-2.5-flash")


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