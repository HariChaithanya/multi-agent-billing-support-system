import os

from langchain_openai import ChatOpenAI


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")),
        api_key=os.getenv("OPENAI_API_KEY") or None,
    )
