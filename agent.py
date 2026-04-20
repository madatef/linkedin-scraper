from __future__ import annotations

import os
from enum import StrEnum

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

SYS_PROMPT = """
You are a helpful assistant that helps fill job application forms on behalf of the user.
You will recieve the application form HTML segment and provide the answer to each filed.
The form will have multiple input types, you will provide structured output that specifies the element by a CSS selector, a type (radio, text, etc), the question/label,  and the value. 
Use the following user data to fill the form fields:
- Name: Mohammad Atef Diab
- Title: AI system Engineer
- Years of Experience: 4
- Email: itsmadatef@gmail.com
- Phone Number: +20 1028968199
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

if __name__ == "__main__":
    op = agent.invoke({"messages": [
        {
            "role": "user", 
            "content": """this is the first step of the application. Here's the HTML:
            <div class="ph5">
                <div class="ZUUShDeOxdGnMdvQmxeDIEvgGMcUMCpiOWfKc">
                    <h3 class="t-16 t-bold">
                    Contact info
                    </h3>
                    <div id="ember346" class="mt3 flex-wrap artdeco-entity-lockup artdeco-entity-lockup--size-4 ember-view">
                    <div id="ember347" class="artdeco-entity-lockup__image artdeco-entity-lockup__image--type-circle ember-view" type="circle">
                        <img width="56" title="Mohammad Atef" src="https://media.licdn.com/dms/image/v2/D4D03AQH7_BfkGopcjA/profile-displayphoto-scale_100_100/B4DZzB6d77I4Ag-/0/1772779858197?e=1778112000&amp;v=beta&amp;t=N4TWb3-9Y12Ao_EQCsi6-W_J9yYo0aM-ZgNBYku5ULc" loading="lazy" height="56" alt="Mohammad Atef" id="ember348" class="evi-image lazy-image ember-view">
                    </div>
                    <div id="ember349" class="artdeco-entity-lockup__content ember-view">
                        <div id="ember350" class="artdeco-entity-lockup__title ember-view">
                        Mohammad Atef
                        </div>
                        <div id="ember351" class="artdeco-entity-lockup__subtitle ember-view">
                        AI Systems Engineer | AI-First Applications � Multi-Agent Architectures � Intelligent Data Platforms
                        </div>
                        <div id="ember352" class="artdeco-entity-lockup__metadata ember-view">
                        Cairo, Egypt
                        </div>
                    </div>
                    </div>
                    <div class="hpRBiPaXSaSOWuLKUEYZBDHSAWEkEscZEyUgfQ">
                    <div class="fb-dash-form-element BgNOYdLeMpSEjSWrvZrMEhKIwVVwEyDYv mt1" style="width:100%" tabindex="-1" data-test-form-element="">
                        <div data-test-text-entity-list-form-component="">
                        <label for="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4400717130-27984797348-multipleChoice" class="fb-dash-form-element__label fb-dash-form-element__label-title--is-required" data-test-text-entity-list-form-title="">
                            <span aria-hidden="true"><!---->Email address<!----></span>
                            <span class="visually-hidden"><!---->Email address<!----></span>
                        </label>
                        <span class="visually-hidden" data-test-text-entity-list-form-required="">
                            Required
                        </span>
                        <select id="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4400717130-27984797348-multipleChoice" class="fb-dash-form-element__select-dropdown" aria-describedby="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4400717130-27984797348-multipleChoice-error" aria-required="true" required="" data-test-text-entity-list-form-select="">
                            <option value="Select an option">
                            Select an option
                            </option>
                            <option value="itsmadatef@gmail.com">
                            itsmadatef@gmail.com
                            </option>
                        </select>
                        </div>
                    </div>
                    </div>
                    <div class="hpRBiPaXSaSOWuLKUEYZBDHSAWEkEscZEyUgfQ">
                    <div class="fb-dash-form-element BgNOYdLeMpSEjSWrvZrMEhKIwVVwEyDYv mt4" style="width:100%" tabindex="-1" data-test-form-element="">
                        <div data-test-text-entity-list-form-component="">
                        <label for="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4400717130-27984797340-phoneNumber-country" class="fb-dash-form-element__label fb-dash-form-element__label-title--is-required" data-test-text-entity-list-form-title="">
                            <span aria-hidden="true"><!---->Phone country code<!----></span>
                            <span class="visually-hidden"><!---->Phone country code<!----></span>
                        </label>
                        <span class="visually-hidden" data-test-text-entity-list-form-required="">
                            Required
                        </span>
                        <select id="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4400717130-27984797340-phoneNumber-country" class="fb-dash-form-element__select-dropdown" aria-describedby="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4400717130-27984797340-phoneNumber-country-error" aria-required="true" required="" data-test-text-entity-list-form-select="">
                            <option value="Select an option">
                            Select an option
                            </option>
                            <option value="Egypt (+20)">
                            Egypt (+20)
                            </option>
                        </select>
                        </div>
                    </div>
                    </div>
                    <div class="hpRBiPaXSaSOWuLKUEYZBDHSAWEkEscZEyUgfQ">
                    <div class="fb-dash-form-element BgNOYdLeMpSEjSWrvZrMEhKIwVVwEyDYv mt4" style="width:100%" tabindex="-1" data-test-form-element="">
                        <div data-test-single-line-text-form-component="" data-live-test-single-line-text-form-component="">
                        <div id="ember353" class="artdeco-text-input artdeco-text-input--type-text artdeco-text-input--color-default artdeco-text-input--state-required ember-view">
                            <div id="ember354" class="artdeco-text-input--container ember-view">
                            <label for="single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4400717130-27984797340-phoneNumber-nationalNumber" class="artdeco-text-input--label">Mobile phone number</label>
                            <input inputmode="text" class=" artdeco-text-input--input" id="single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4400717130-27984797340-phoneNumber-nationalNumber" required="" aria-describedby="single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4400717130-27984797340-phoneNumber-nationalNumber-error" dir="auto" type="text">
                            </div>
                        </div>
                        <div id="single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4400717130-27984797340-phoneNumber-nationalNumber-error"></div>
                        </div>
                    </div>
                    </div>
                </div>
            </div>
            """
        }
    ]})
    print(op.get("structured_response"))