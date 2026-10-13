
"""Explicitly list Gemini models available to the configured API key."""

import os

from dotenv import load_dotenv
from google import genai


def main() -> None:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY in .env before listing models.")

    client = genai.Client(api_key=api_key)
    for model in client.models.list():
        if "generateContent" in (model.supported_actions or []):
            print(model.name)


if __name__ == "__main__":
    main()
