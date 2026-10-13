
import os

from dotenv import load_dotenv
from google import genai

def main() -> None:
    # This is an explicitly invoked, quota-consuming smoke check; importing this
    # module during test discovery must never send a request.
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY was not found in .env")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents="Reply with exactly: Gemini API connection successful.",
    )
    print(response.text)


if __name__ == "__main__":
    main()
