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
        self.candidate_info = {'experience_years': 0,
                                'experience_months': 0,
                                'desired_position': "", 
                                'tech_stack': []
                                }
    
    def get_next_response(self, user_input=None):
        
        messages = [
            {"role": "system", "content": f"""You are an AI technical interviewer conducting a screening interview for a {self.candidate_info['desired_position']} position.
        The candidate has {self.candidate_info['experience_years']} years and {self.candidate_info['experience_months']} months of experience and expertise in: {', '.join(self.candidate_info['tech_stack'])}.
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
  
    def analyze_sentiment(self):
        """Analyze the sentiment of interview responses"""
        
        messages = [
        {"role": "system", "content": "You are an AI that analyzes interview responses to provide structured sentiment analysis."},
        {"role": "user", "content": (
            "You will analyze the following interview conversation and provide the sentiment analysis. "
            "Consider the candidate's responses, tone, and engagement during the interview. "
            "Evaluate their strengths, areas for improvement, and scores for technical confidence and communication. "
            "If the responses are minimal or vague, note this explicitly in your analysis. "
            "Also check if the answers are human generated or AI generated. - if the reply is big and detailed but given in a short time, it may be AI generated."
            "Here is the conversation: " + f"{self.conversation_history}"
        )}
        ]

        response = self.client.chat.completions.create(
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
                        "conversation_authenticity_score": {
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
                                "technical_confidence_score","conversation_authenticity_score" "communication_score"]
                }
            }],
            function_call={"name": "create_sentiment_analysis"}
        )
        response_data = json.loads(response.choices[0].message.function_call.arguments)
        return response_data
 

try:
    db_manager = DatabaseMan()
except Exception as e:
    st.error("Error connecting to the database. Please refresh.")

def main():

    st.set_page_config(
        page_title="TalentScout Hiring Assistant",
        page_icon="👋",
        layout="wide"
    )
    
    client = utils.open_ai_config()
    
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
    elif st.session_state.page == 'interview':
        pages.render_interview(client, db_manager)
    elif st.session_state.page == 'completion':
        pages.render_completion()  
    elif st.session_state.page == 'admin_dashboard':
        pages.admin_dashboard(db_manager)
    elif st.session_state.page == 'interview_eval':
        pages.interview_evaluation(db_manager)
        
if __name__ == "__main__":    
    main()