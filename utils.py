from openai import OpenAI
import os
from dotenv import load_dotenv
import re
from dataclasses import dataclass, asdict
from typing import List

def open_ai_config():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    return client

def generate_openai_response(client, messages, model='gpt-3.5-turbo',temperature = 0.1, 
                        functions = None, function_call= None):
    kwargs = {
        "model": model,
        "messages": messages,
        'temperature': temperature
    }
    
    if functions:
        kwargs["functions"] = functions
    if function_call:
        kwargs["function_call"] = function_call

    try:
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message
    except Exception as e:
        print(f"Error in OpenAI API call: {e}")
        return None
    
def validate_inputs(full_name, email, phone, desired_position, location, tech_stack):
    """Validate all form inputs."""
    if not all([full_name, email, phone, desired_position, location, tech_stack]):
        return False, "Please fill in all required fields."
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email address. Please enter a valid email."
    if not re.match(r"^\d{10}$", phone):
        return False, "Invalid phone number. Please enter a valid 10-digit phone number."
    return True, ""

@dataclass
class CandidateInfo:
    full_name: str
    email: str
    phone: str
    experience_years: int
    experience_months: int
    desired_position: str
    location: str
    tech_stack: List[str]
    consent_timestamp: str
    
    def to_dict(self):
        return asdict(self)

    