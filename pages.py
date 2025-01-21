import streamlit as st
import utils
from datetime import datetime
import pandas as pd


def admin_dashboard(db_manager):

    data = db_manager.fetch_user_table()
    if not data:
        st.warning("No candidates found.")
        return
    
    # Convert to DataFrame for Streamlit table
    df = pd.DataFrame(data, columns=["Name", "Desired Designation", "User ID"])

    # Display table
    st.title("Candidates Table")

    col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
    col1.markdown("**Name**")
    col2.markdown("**Desired Designation**")
    col4.markdown("**More Details**")

    for index, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
        col1.write(row["Name"])
        col2.write(row["Desired Designation"])
        if col4.button(f"Select", key=f"select_{row['User ID']}"):
            st.session_state.selected_user_id = row["User ID"]
            st.session_state.selected_user_name = row["Name"]
            st.session_state.page = 'interview_eval'
            st.rerun()
          
def interview_evaluation(db_manager):
    user_id = st.session_state.selected_user_id
    name = st.session_state.selected_user_name
    evaluation_data = db_manager.fetch_interview_evaluation(user_id)
    st.session_state.interview_history = db_manager.get_interviews(user_id)

    if not evaluation_data:
        st.warning("No interview evaluations found.")
    else:
        st.title(f"Interview Evaluation Results of {name}")

        # Display each field in a structured way
        st.subheader("Evaluation Overview")
        st.markdown(f"**Overall Sentiment:** {evaluation_data['Overall Sentiment']}")
        st.markdown(f"**Technical Confidence Score:** {evaluation_data['Technical Confidence Score']}")
        st.markdown(f"**Conversation Authenticity Score:** {evaluation_data['Conversation Authenticity Score']}")
        st.markdown(f"**Communication Score:** {evaluation_data['Communication Score']}")

        st.subheader("Key Strengths")
        if evaluation_data["Key Strengths"]:
            for strength in evaluation_data["Key Strengths"]:
                st.markdown(f"- {strength}")
        else:
            st.markdown("No strengths identified.")

        st.subheader("Areas for Improvement")
        if evaluation_data["Areas for Improvement"]:
            for improvement in evaluation_data["Areas for Improvement"]:
                st.markdown(f"- {improvement}")
        else:
            st.markdown("No areas for improvement identified.")
        
        if st.button("read_interview"):
            st.session_state.page = 'interview'
            st.rerun()            

def login_page(db_manager):
    st.title("User Login")

    # Tabs for Login and Signup
    tab_login, tab_signup = st.tabs(["Login", "Signup"])
    with tab_login:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            is_authenticated, role, user_id = db_manager.login_user(username, password)
            if is_authenticated:
                st.session_state['user'] = {'username': username, 'role': role, 'user_id': user_id}
                if role == 'Admin':
                    st.success(f"Welcome {username}! Redirecting to the Admin Dashboard...")
                    st.session_state.page = 'admin_dashboard'
                elif role == 'Candidate':
                    st.success(f"Welcome {username}! Redirecting to the Welcome Page...")
                    st.session_state.page = 'welcome'
                st.rerun()
            else:
                st.error("Invalid username or password!")

    with tab_signup:
        st.subheader("Sign Up")
        username = st.text_input("Username", key="signup_username")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        role = st.selectbox("Role", ["Candidate", "Admin"], key="role")
        if st.button("Sign Up"):
            if password != confirm_password:
                st.error("Passwords do not match!")
            elif len(username.strip()) == 0:
                st.error("Username cannot be empty.")       
            else:
                try:
                    if db_manager.check_username_availability(username):
                        user_id = db_manager.register_user(username, password, role)
                        st.success("User registered successfully! ")
                        st.session_state['user'] = {'username': username, 'role': role, 'user_id': user_id}
                        if role == 'Admin':
                            st.session_state.page = 'admin_dashboard'
                        elif role == 'Candidate':
                            st.session_state.page = 'welcome'
                        st.rerun()
                    else: 
                        st.error("Username already taken. Please choose a different username.")
                except Exception as e:
                    st.error(f"Error registering user: {e}")

def render_welcome(db_manager):
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

def render_collect_info(db_manager):
    # Fetch existing user data
    user_id = st.session_state['user']['user_id']
    user_data = db_manager.get_candidate_info(user_id)
    st.session_state.interview_history = db_manager.get_interviews(user_id)
    
    if user_data:
        st.write(f"Welcome back, {user_data['full_name']}!")
        st.info("You have already submitted your information. You can modify it.")
        # Pre-fill the form with existing data
        full_name = st.text_input("Full Name*", value=user_data['full_name'])
        email = st.text_input("Email Address*", value=user_data['email'])
        phone = st.text_input("Phone Number*", value=user_data['phone'])
        education = st.text_input("Education*", value=user_data['education'])
        col1, col2 = st.columns(2)
        with col1:
            experience_years = st.number_input("Years of Experience*", min_value=0, step=1, format="%d", 
                                               value=int(user_data['experience_years']))
        with col2:
            experience_months = st.number_input("Months of Experience*", min_value=0, max_value=11, step=1, format="%d", 
                                                value=int(user_data['experience_months']))
        desired_position = st.text_input("Desired Position*", value=user_data['desired_position'])
        location = st.text_input("Current Location*", value=user_data['location'])
        tech_stack = st.text_input("Tech Stack (comma-separated list)*", 
                                    value=", ".join(user_data['tech_stack']))

        modify_button = st.button("Modify")
        delete_button = st.button("Delete")
        go_to_interview = st.button("Go to Interview")
        
        if modify_button:
            is_valid, error_message = utils.validate_inputs(full_name, email, phone, desired_position, location, tech_stack)
            if is_valid:
                updated_info = {
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "education": education,
                    "experience_years": experience_years,
                    "experience_months": experience_months,
                    "desired_position": desired_position,
                    "location": location,
                    "tech_stack": [tech.strip() for tech in tech_stack.split(',')],
                }
                db_manager.update_candidate_info(user_id, updated_info)
                st.success("Your information has been updated!")
                st.session_state.assistant.candidate_info = {
                    "experience_years": updated_info["experience_years"],
                    "experience_months": updated_info["experience_months"],
                    "desired_position": updated_info["desired_position"],
                    "tech_stack": updated_info['tech_stack']
                }
                if st.session_state.interview_history:
                    st.session_state.page = 'interview'    
                    st.rerun()    
                else:
                    initial_response = st.session_state.assistant.get_next_response()
                    st.session_state.messages = [{"role": "assistant", "content": initial_response}]
                    st.session_state.page = 'interview'    
                    st.rerun()
            else:
                st.error(error_message)
        
        if delete_button:
            db_manager.delete_candidate_info(user_id)
            st.success("Your information has been deleted!")
            st.rerun()
        
        if go_to_interview:
            st.session_state.page = 'interview'
            st.rerun()
    
    else:    
        st.title("Let's Get to Know You")
        
        with st.form("candidate_info_form"):
            full_name = st.text_input("Full Name*")
            email = st.text_input("Email Address*")
            phone = st.text_input("Phone Number*")
            education = st.text_input("Education*", help="Example: Bachelor's in Computer Science")
            col1, col2 = st.columns(2)
            with col1:
                experience_years = st.number_input("Years of Experience*", min_value=0, step=1, format="%d")
            with col2:
                experience_months = st.number_input("Months of Experience*", min_value=0, max_value=11, step=1, format="%d")
            desired_position = st.text_input("Desired Position*")
            location = st.text_input("Current Location*")
            tech_stack = st.text_input("Tech Stack (comma-separated list)*", 
                                        help="Example: Python, React, MongoDB")
            
            submit_button = st.form_submit_button("Submit")
            
            if submit_button:
                # Validate required fields
                is_valid, error_message = utils.validate_inputs(full_name, email, phone, desired_position, location, tech_stack)
                if is_valid:
                    candidate_info = {
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "education": education,
                    "experience_years": experience_years,
                    "experience_months": experience_months,
                    "desired_position": desired_position,
                    "location": location,
                    "tech_stack": [tech.strip() for tech in tech_stack.split(',')],
                    "consent_timestamp" : datetime.now().isoformat()
                    }
                    user_id = st.session_state['user']['user_id']
                    db_manager.save_candidate(user_id, candidate_data=candidate_info)
                    st.session_state.assistant.candidate_info = {
                        "experience_years": experience_years,
                        "experience_months": experience_months,
                        "desired_position": desired_position,
                        "tech_stack": [tech.strip() for tech in tech_stack.split(',')]
                    }
                    initial_response = st.session_state.assistant.get_next_response()
                    st.session_state.messages = [{"role": "assistant", "content": initial_response}]
                    st.session_state.page = 'interview'
                    st.rerun()
                else:
                    st.error(error_message)

def render_interview(client, db_manager):
    
    interview_history = st.session_state.interview_history
    
    if interview_history:
        st.subheader("Interview Details")
        for interview in interview_history:
            st.markdown(f"**{interview['role'].capitalize()}**: {interview['content']}\n")
        if st.button("Go Back", key="back_button"):
            if st.session_state['user']['role'] == 'Admin':
                st.session_state.page = 'admin_dashboard'
            else:
                st.session_state.page = 'collect_info'
                st.rerun()

        if st.button("Logout"):
            st.session_state.page = 'login'
            st.session_state['user'] = {}
            st.rerun()

    else:
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
            st.write("Would you like to end the interview now? Or do you have more questions or answers?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, End Interview", key="end_button"):
                    st.write("Analysing and Saving interview...")
                    sentiment_data = st.session_state.assistant.analyze_sentiment()
                    db_manager.save_conversation_to_db(st.session_state['user']['user_id'], st.session_state.messages, sentiment_data)
                    st.session_state.page = "completion"
                    st.rerun()
            with col2:
                if st.button("No, Continue Chat", key="continue_button"):
                    st.session_state.interview_ending = False
                    st.rerun()
        
def render_completion():
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