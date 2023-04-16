import openai
from decouple import config
from typing import Optional

OPENAI_API_KEY = config("OPENAI_API_KEY", default=None)

openai.api_key = OPENAI_API_KEY

system_prompt = "You are a helpful assistant that generates summaries of texts extracted from PDF files or webpages."
prompt_structure = """Generate an executive summary in English of the text in the following format{words_limit_text}:
Theme: [theme]
Key points:
- [key point 1]
- ...

The text is:
{text}
"""


def generate_summary(
    text: str,
    temperature: float = 0.7,
    input_limit: int = 1048,
    words_limit: Optional[int] = None,
) -> str:
    text_words = text.split()[:input_limit]
    text = " ".join(text_words)
    if words_limit is not None:
        prompt = prompt_structure.format(
            words_limit_text=f" and less than {words_limit} words", text=text
        )
    else:
        prompt = prompt_structure.format(words_limit_text="", text=text)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )

    return response.choices[0].message["content"]


if __name__ == "__main__":
    from bot.utilities.pdf_reader import extract_text_from_pdf
    from pathlib import Path

    pdf_path = Path("/Users/miguel/Downloads/s41586-023-05781-7.pdf")
    text = extract_text_from_pdf(pdf_path)
    print(generate_summary(text, words_limit=50))
