from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path

import yaml
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
key = os.getenv("OPENAI_API_KEY")

class FieldType(StrEnum):
    RADIO = "radio"
    CHECKBOX = "checkbox"
    SELECT = "select"
    FILE = "file"
    TEXT = "text"


class FormField(BaseModel):
    field_type: FieldType
    selector: str
    question: str
    value: str | None

class ModelOutput(BaseModel):
    inputs: list[FormField]


CV_PATH = Path(__file__).parent / "cv.yaml"
with open(CV_PATH, "r") as f:
    cv = yaml.safe_load(f)

SYS_PROMPT = f"""
You are a helpful assistant that helps fill job application forms on behalf of the user.
You will recieve the application form HTML segment and provide the answer to each filed.
The form will have multiple input types, you will provide structured output that specifies the element by a CSS selector, a type (radio, text, etc), the question/label,  and the value. 
Use the following user data to fill the form fields:
{str(cv)}
"""

llm = ChatOpenAI(
    model="gpt-5.2",
    api_key=key,
)

agent = create_agent(
    model=llm,
    system_prompt=SYS_PROMPT,
    response_format=ModelOutput,
)