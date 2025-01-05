import streamlit as st
from openai import OpenAI
import os

def chatbot_response(prompt, client):
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
         {"role": "system", "content": "You are a technical interviewer evaluating candidate responses."},
         {"role": "system", "content": prompt}],    
    )
    return completion.choices[0].message

def main():

    # Set up OpenAI API
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
        

    # Streamlit UI
    st.title("TalentScout Hiring Assistant")

    # Collect candidate details
    st.header("Candidate Information")
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    phone = st.text_input("Phone Number")
    experience = st.number_input("Years of Experience", min_value=0, step=1)
    position = st.text_input("Desired Position(s)")
    location = st.text_input("Current Location")
    tech_stack = st.text_area("Tech Stack (e.g., Python, Django, React)")

    if st.button("Submit"):
        if not all([name, email, phone, experience, position, location, tech_stack]):
            st.error("Please fill out all fields.")
        else:
            # Generate questions
            prompt = f"""You are a hiring assistant. A candidate has provided the following tech stack: {tech_stack}.
            Generate 3-5 technical interview questions tailored to these technologies."""
            questions = chatbot_response(prompt, client)
            st.success("Here are the generated technical questions:")
            st.write(questions)

    # End conversation
    if st.button("End Conversation"):
        st.write("Thank you for using the TalentScout Hiring Assistant!")

if __name__ == "__main__":
    main()