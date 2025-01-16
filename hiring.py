import streamlit as st
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import pages, utils  
from db_utils import DatabaseMan

class HiringAssistant:
    def __init__(self, client):
        self.client = client
        self.conversation_history = []
        self.topics_covered = set()
        self.candidate_info = None
    
    def get_next_response(self, user_input=None):
        
        messages = [
            {"role": "system", "content": f"""You are an AI technical interviewer conducting a screening interview for a {self.candidate_info.desired_position} position.
        The candidate has {self.candidate_info.experience_years} years and {self.candidate_info.experience_months} months of experience and expertise in: {', '.join(self.candidate_info.tech_stack)}.
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
        
    
        response = utils.generate_openai_response(self.client, messages, model='gpt-4o-mini')
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
        response = utils.generate_openai_response(self.client, messages)
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

    def add_sentiment_analysis(self, client):
        analysis = utils.analyze_sentiment(client, self.conversation_history)
        
        # Update the latest interview file with sentiment analysis
        latest_file = max(glob.glob('interviews/*.json'), key=os.path.getctime)
        with open(latest_file, 'r') as f:
            interview_data = json.load(f)
        
        # analysis is already JSON string, no need to load it
        interview_data['sentiment_analysis'] = json.loads(analysis)
        
        with open(latest_file, 'w') as f:
            json.dump(interview_data, f, indent=2)

db_manager = DatabaseMan()

def main():

    client = utils.open_ai_config()

    st.set_page_config(
        page_title="TalentScout Hiring Assistant",
        page_icon="👋",
        layout="wide"
    )
    
    # Initialize session states
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'assistant' not in st.session_state:
        st.session_state.assistant = HiringAssistant(client)
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if st.session_state.page == 'login':
        pages.login_page(db_manager)
    elif st.session_state.page == 'welcome':
        pages.render_welcome(db_manager)
    elif st.session_state.page == 'collect_info':
        pages.render_collect_info(db_manager)
    elif st.session_state.page == 'screening':
        pages.render_screening(client, db_manager)
    elif st.session_state.page == 'completion':
        pages.render_completion(db_manager)      
        
if __name__ == "__main__":    
    main()