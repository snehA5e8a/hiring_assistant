import streamlit as st
from dataclasses import dataclass, asdict
import json
from datetime import datetime
from openai import OpenAI
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv


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
    
def generate_openai_response(client, messages, model='gpt-4o-mini',temperature = 0.1, 
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

class HiringAssistant:
    def __init__(self, client):
        self.client = client
        self.conversation_history = []
        self.evaluation_notes = []
        self.topics_covered = set()
        self.candidate_info = None
        
    def save_candidate_info(self, info: CandidateInfo):
        """Save candidate information to JSON file"""
        self.candidate_info = info
        filename = f"candidates/{info.email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('candidates', exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(info.to_dict(), f, indent=2)
    
    def get_next_response(self, user_input=None):
        
        messages = [
            {"role": "system", "content": f"""You are an AI technical interviewer conducting a screening interview for a {self.candidate_info.desired_position} position.
        The candidate has {self.candidate_info.experience} years of experience and expertise in: {', '.join(self.candidate_info.tech_stack)}.
        First you need to check if the expertise mentioned are relevant to the position, it may be some random words.
        If not a relevant skill, inform the candidate the same and move to next relevant skill

        And if it is relevant skill:
        1. Ask relevant technical questions about each technology in their stack
        2. Ask follow-up questions based on their responses, limiting follow-ups to 1-3 questions per topic.
        3. Transition to the next topic once follow-ups are exhausted or answers are complete or the user has no proper answer to the question.
        4. Keep track of topics covered
        5. End the conversation gracefully once all topics are covered.
        6. Stay focused on technical assessment
        
        Guidelines:
        - Ask one question at a time
        - Follow up on interesting points in their answers
        - If an answer is unclear, ask for clarification
        - Keep questions relevant to their experience level
        - Be professional but friendly
        - Mark topics as covered when sufficiently discussed
        
        Start by introducing yourself and asking the first technical question."""
        }]
        
        # Add conversation history
        for msg in self.conversation_history:
            messages.append(msg)
            
        # Add user's latest input if provided
        if user_input:
            messages.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "user", "content": user_input})
        
    
        response = generate_openai_response(self.client, messages)
        assistant_response = response.content
        self.conversation_history.append({"role": "assistant", "content": assistant_response})
        
        # Update topics covered
        for tech in self.candidate_info.tech_stack:
            if tech.lower() in user_input.lower() if user_input else False:
                self.topics_covered.add(tech)
        
        return assistant_response
        
        
    def should_end_interview(self):
        if len(self.conversation_history) < 2:
            return False  # Not enough data to evaluate
        assistant_message = self.conversation_history[-2]["content"]
        user_response = self.conversation_history[-1]["content"]

        # Take the latest assistant message and user: pass and see if its the last one, if flag is set, return True
        messages = [
        {"role": "system", "content": f"""You are an AI evaluator assisting in a technical interview.
        Your task is to determine if the interview has reached a natural conclusion based on the following context:
        Evaluate the most recent exchange between the interviewer and the candidate:
        - Interviewer's question: "{assistant_message}"
        - Candidate's response: "{user_response}"

        By considering the above conversation, 
        - check if they are in the middle of any conversation
        - did the interviewer has any pending question
        - did the candidate has any pending answer
    
        based on the above should the interview be ended?
        Provide the answer as 'yes' or 'no'
        """}]
        response = generate_openai_response(self.client, messages)
        return response.content.strip().lower() == "yes"

    
    def save_interview_record(self):
        """Save the complete interview record"""
        record = {
            "candidate_info": self.candidate_info.to_dict(),
            "conversation_history": self.conversation_history,
            "topics_covered": list(self.topics_covered),
            "timestamp": datetime.now().isoformat()
        }
        
        filename = f"interviews/{self.candidate_info.email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('interviews', exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(record, f, indent=2)

def main():

    # Configure OpenAI
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    st.set_page_config(
        page_title="TalentScout Hiring Assistant",
        page_icon="👋",
        layout="wide"
    )
    
    # Initialize session states
    if 'page' not in st.session_state:
        st.session_state.page = 'welcome'
    if 'assistant' not in st.session_state:
        st.session_state.assistant = HiringAssistant(client)
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    def change_page(new_page):
        st.session_state.page = new_page
        # Clear interview-specific states when leaving screening page
        if new_page == 'completion':
            if 'messages' in st.session_state:
                del st.session_state.messages
            if 'interview_ending' in st.session_state:
                del st.session_state.interview_ending
            if 'chat_disabled' in st.session_state:
                del st.session_state.chat_disabled

    # Welcome Page
    if st.session_state.page == 'welcome':
        st.title("Welcome to TalentScout! 👋")
        
        st.markdown("""
        Hello! I'm your AI Hiring Assistant, and I'll be conducting your initial screening interview.
        
        This process will involve:
        1. Collecting your name, email id, mobile number, professional information
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
                    
                    # Save candidate info and initialize chat
                    st.session_state.assistant.save_candidate_info(candidate_info)
                    initial_response = st.session_state.assistant.get_next_response()
                    st.session_state.messages = [{"role": "assistant", "content": initial_response}]
                    
                    st.session_state.page = 'screening'
                    st.rerun()
                else:
                    st.error("Please fill in all required fields.")
    
    # Screening Page
    elif st.session_state.page == 'screening':
        st.title("Technical Screening Interview")
        
        if 'interview_ending' not in st.session_state:
            st.session_state.interview_ending = False
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Only show chat input and handle messages if not in ending state
        if not st.session_state.interview_ending:
            if user_input := st.chat_input("Your response..."):
                with st.chat_message("user"):
                    st.write(user_input)
                
                assistant_response = st.session_state.assistant.get_next_response(user_input)
                
                with st.chat_message("assistant"):
                    st.write(assistant_response)
                
                st.session_state.messages.extend([
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": assistant_response}
                ])
                
                if st.session_state.assistant.should_end_interview():
                    st.session_state.interview_ending = True
                    st.rerun()
        
        # Show end interview confirmation if in ending state
        if st.session_state.interview_ending:
            st.write("Would you like to end the interview now?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, End Interview", key="end_button"):
                    st.session_state.assistant.save_interview_record()
                    change_page('completion')
                    st.rerun()
            with col2:
                if st.button("No, Continue Chat", key="continue_button"):
                    st.session_state.interview_ending = False
                    st.rerun()
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
        st.balloons()

if __name__ == "__main__":    
    st.server.listen(port=8080)
    main()