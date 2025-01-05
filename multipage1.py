import streamlit as st
from dataclasses import dataclass, asdict
import json
from datetime import datetime
from openai import OpenAI
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)


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

def generate_openai_response(client: OpenAI, system_prompt, user_prompt, model='gpt-4o',temperature = 0.1, 
                        functions = None, function_call= None, max_tokens = 1000):
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]
    
    kwargs = {
        "model": model,
        "messages": messages,
        'temperature': temperature,
        'max_tokens' : max_tokens
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
    
class HiringAssistant:
    def __init__(self, candidate_info):
        self.candidate_info = candidate_info
        self.conversation_history = []
        self.evaluation_notes = []
        self.current_topic = None
        self.topics_covered = set()
        self.conversation_history = []
        self.current_question_index = 0
        
    def save_candidate_info(self, info: CandidateInfo):
        """Save candidate information to JSON file"""
        filename = f"candidates/{info.email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('candidates', exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(info.to_dict(), f, indent=2)
            
    def generate_initial_prompt(self) -> str:
        """Generate the system prompt based on candidate information"""
        return f"""You are an AI technical interviewer conducting a screening interview for a {self.candidate_info['desired_position']} position.
        The candidate has {self.candidate_info['experience']} years of experience and expertise in: {', '.join(self.candidate_info['tech_stack'])}.
        
        Your task is to:
        1. Ask relevant technical questions about each technology in their stack
        2. Ask follow-up questions based on their responses
        3. Maintain conversation context
        4. Keep track of topics covered
        5. Stay focused on technical assessment
        
        Guidelines:
        - Ask one question at a time
        - Follow up on interesting points in their answers
        - If an answer is unclear, ask for clarification
        - Keep questions relevant to their experience level
        - Be professional but friendly
        - Mark topics as covered when sufficiently discussed
        
        Start by introducing yourself and asking the first technical question."""
    
        
    def get_next_response(self, user_input: str = None) -> str:
        """Get next assistant response based on conversation context"""
        messages = [
            {"role": "system", "content": self.generate_initial_prompt()}
        ]
        
        # Add conversation history
        for msg in self.conversation_history:
            messages.append(msg)
            
        # Add user's latest input if provided
        if user_input:
            messages.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "user", "content": user_input})
        
        

        try:
            response = generate_openai_response(client,messages)
            assistant_response = response.content if response else "No reply generated due to an error." 
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
            # Update topics covered (simplified version)
            for tech in self.candidate_info['tech_stack']:
                if tech.lower() in user_input.lower() if user_input else False:
                    self.topics_covered.add(tech)
            
            return assistant_response
            
        except Exception as e:
            return "I apologize for the technical difficulty. Could you please rephrase your response or let me ask another question?"

    def should_end_interview(self) -> bool:
        """Determine if the interview should be concluded"""
        # Check if all topics have been covered
        all_topics_covered = all(tech in self.topics_covered for tech in self.candidate_info['tech_stack'])
        
        # Check conversation length
        sufficient_conversation = len(self.conversation_history) >= 10
        
        return all_topics_covered and sufficient_conversation

    def save_interview_record(self):
        """Save the complete interview record"""
        record = {
            "candidate_info": self.candidate_info,
            "conversation_history": self.conversation_history,
            "topics_covered": list(self.topics_covered),
            "timestamp": datetime.now().isoformat()
        }
        
        filename = f"interviews/{self.candidate_info['email']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('interviews', exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(record, f, indent=2)
    
    
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