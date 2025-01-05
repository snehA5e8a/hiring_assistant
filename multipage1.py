# app.py
import streamlit as st
from dataclasses import dataclass, asdict
import json
from datetime import datetime
import openai
from typing import List, Dict, Optional
import os
#from dotenv import load_dotenv

# Load environment variables
#load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

@dataclass
class CandidateInfo:
    full_name: str
    email: str
    phone: str
    experience: float
    desired_position: str
    location: str
    tech_stack: List[str]
    consent_timestamp: str
    
    def to_dict(self):
        return asdict(self)

class HiringAssistant:
    def __init__(self):
        self.conversation_history = []
        self.current_question_index = 0
        
    def save_candidate_info(self, info: CandidateInfo):
        """Save candidate information to JSON file"""
        filename = f"candidates/{info.email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('candidates', exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(info.to_dict(), f, indent=2)
            
    def generate_screening_questions(self, position: str, tech_stack: List[str]) -> List[str]:
        """Generate screening questions using LLM based on position and tech stack"""
        prompt = f"""As a technical interviewer, generate 5 relevant screening questions for a {position} position 
        with expertise in {', '.join(tech_stack)}. Questions should assess both technical knowledge and practical experience.
        Format: Return just the questions numbered 1-5."""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a technical interviewer generating screening questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content.strip().split('\n')
        except Exception as e:
            # Fallback questions if API call fails
            return [
                f"Describe your experience with {tech}" for tech in tech_stack
            ] + [
                f"What challenges have you faced while working as a {position}?",
                "Describe a complex technical problem you've solved recently."
            ]
    
    def evaluate_response(self, question: str, answer: str) -> str:
        """Evaluate candidate response using LLM"""
        prompt = f"""Question: {question}\nCandidate's Answer: {answer}\n
        Evaluate the response considering: clarity, technical accuracy, and depth of understanding.
        Provide a brief feedback and follow-up question if needed."""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a technical interviewer evaluating candidate responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "Thank you for your response. Let's move to the next question."

def main():
    st.set_page_config(
        page_title="TalentScout Hiring Assistant",
        page_icon="👋",
        layout="wide"
    )
    
    # Initialize session states
    if 'page' not in st.session_state:
        st.session_state.page = 'welcome'
    if 'assistant' not in st.session_state:
        st.session_state.assistant = HiringAssistant()
    if 'candidate_info' not in st.session_state:
        st.session_state.candidate_info = None
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    
    # Welcome Page
    if st.session_state.page == 'welcome':
        st.title("Welcome to TalentScout! 👋")
        
        st.markdown("""
        Hello! I'm your AI Hiring Assistant, and I'll be conducting your initial screening interview.
        
        This process will involve:
        1. Collecting some basic information about you
        2. Understanding your technical expertise
        3. Asking relevant screening questions
        
        The entire process should take about 15-20 minutes.
        """)
        
        # Consent Form
        st.subheader("Consent Form")
        consent_text = """By submitting your information, you consent to our collection and processing of your personal data 
        for recruitment purposes. We will use your details solely for evaluating your application and will not share them 
        with third parties without your permission. You have the right to withdraw your consent at any time."""
        
        st.info(consent_text)
        
        consent = st.checkbox("I have read and agree to the terms above")
        
        if consent:
            if st.button("Start Interview"):
                st.session_state.page = 'collect_info'
                st.rerun()
    
    # Collect Information Page
    elif st.session_state.page == 'collect_info':
        st.title("Let's Get to Know You")
        
        with st.form("candidate_info_form"):
            full_name = st.text_input("Full Name*")
            email = st.text_input("Email Address*")
            phone = st.text_input("Phone Number*")
            experience = st.number_input("Years of Experience*", min_value=0.0, step=0.5)
            desired_position = st.text_input("Desired Position*")
            location = st.text_input("Current Location*")
            tech_stack = st.text_input("Tech Stack (comma-separated list)*", 
                                     help="Example: Python, React, MongoDB")
            
            submit_button = st.form_submit_button("Submit")
            
            if submit_button:
                if all([full_name, email, phone, experience, desired_position, location, tech_stack]):
                    # Create and save candidate info
                    candidate_info = CandidateInfo(
                        full_name=full_name,
                        email=email,
                        phone=phone,
                        experience=experience,
                        desired_position=desired_position,
                        location=location,
                        tech_stack=[tech.strip() for tech in tech_stack.split(',')],
                        consent_timestamp=datetime.now().isoformat()
                    )
                    
                    st.session_state.assistant.save_candidate_info(candidate_info)
                    st.session_state.candidate_info = candidate_info
                    
                    # Generate screening questions
                    st.session_state.questions = st.session_state.assistant.generate_screening_questions(
                        desired_position,
                        candidate_info.tech_stack
                    )
                    
                    st.session_state.page = 'screening'
                    st.rerun()
                else:
                    st.error("Please fill in all required fields.")
    
    # Screening Page
    elif st.session_state.page == 'screening':
        st.title("Technical Screening")
        
        if st.session_state.current_question < len(st.session_state.questions):
            current_q = st.session_state.questions[st.session_state.current_question]
            st.write(f"Question {st.session_state.current_question + 1}:")
            st.write(current_q)
            
            answer = st.text_area("Your Answer")
            
            if st.button("Submit Answer"):
                if answer.strip():
                    # Evaluate response
                    feedback = st.session_state.assistant.evaluate_response(current_q, answer)
                    st.write("Feedback:")
                    st.write(feedback)
                    
                    st.session_state.current_question += 1
                    if st.session_state.current_question < len(st.session_state.questions):
                        if st.button("Next Question"):
                            st.rerun()
                    else:
                        st.session_state.page = 'completion'
                        st.rerun()
                else:
                    st.error("Please provide an answer before proceeding.")
        
    # Completion Page
    elif st.session_state.page == 'completion':
        st.title("Interview Complete! 🎉")
        
        st.markdown("""
        Thank you for completing the initial screening interview! Here's what happens next:

        1. Our hiring team will review your responses within 2-3 business days
        2. If your profile matches our requirements, we'll invite you for a detailed technical interview
        3. You'll receive an email with the results and next steps

        If you have any questions, please feel free to reach out to our HR team.

        Best of luck with your application! 👋
        """)

if __name__ == "__main__":
    main()