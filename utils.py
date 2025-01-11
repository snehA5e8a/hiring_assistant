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
    experience: str
    desired_position: str
    location: str
    tech_stack: List[str]
    consent_timestamp: str
    
    def to_dict(self):
        return asdict(self)

def analyze_sentiment(client, conversation_history):
    """Analyze the sentiment of interview responses"""
    
    messages = [
    {"role": "system", "content": "You are an AI that analyzes interview responses to provide structured sentiment analysis."},
    {"role": "user", "content": (
        "You will analyze the following interview conversation and provide the sentiment analysis. "
        "Consider the candidate's responses, tone, and engagement during the interview. "
        "Evaluate their strengths, areas for improvement, and scores for technical confidence and communication. "
        "If the responses are minimal or vague, note this explicitly in your analysis. "
        "Here is the conversation: " + f"{conversation_history}"
    )}
]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        functions=[{
            "name": "create_sentiment_analysis",
            "description": "Create a structured sentiment analysis from the interview",
            "parameters": {
                "type": "object",
                "properties": {
                    "overall_sentiment": {
                        "type": "string",
                        "enum": ["positive", "neutral", "negative"]
                    },
                    "key_strengths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 3
                    },
                    "areas_for_improvement": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 3
                    },
                    "technical_confidence_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 10
                    },
                    "communication_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 10
                    }
                },
                "required": ["overall_sentiment", "key_strengths", "areas_for_improvement",
                            "technical_confidence_score", "communication_score"]
            }
        }],
        function_call={"name": "create_sentiment_analysis"}
    )

    return response.choices[0].message.function_call.arguments
