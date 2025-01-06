# TalentScout Hiring Assistant

## Project Overview
TalentScout is an AI-powered technical screening assistant built with Streamlit that automates the initial interview process for technical positions. The assistant conducts structured technical interviews, analyzes candidate responses, and provides sentiment analysis to help hiring teams make informed decisions.

Key Features:
- Automated technical screening interviews
- Dynamic question generation based on candidate's tech stack
- Real-time sentiment analysis
- Structured data collection and storage
- Professional candidate experience with consent management

## Installation Instructions

### Prerequisites
- Python 3.8+
- OpenAI API key

### Setup Steps

1. Clone the repository:
```bash
git clone https://github.com/snehA5e8a/hiring_assistant
cd hiring_assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required dependencies:
```bash
pip install streamlit openai python-dotenv
```

4. Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

5. Run the application:
```bash
streamlit run hiring.py
```

## Usage Guide

### For Hiring Teams

1. Start the application using the command above
2. Share the provided URL with candidates
3. Interview records and analysis will be stored in the `interviews/` directory
4. Candidate information is stored in the `candidates/` directory

### For Candidates

1. Access the provided interview URL
2. Review and accept the consent form
3. Fill in your personal and professional information
4. Participate in the technical screening interview
5. Receive confirmation of completion

## Technical Details

### Libraries Used
- `streamlit`: Web application framework
- `openai`: OpenAI API integration
- `python-dotenv`: Environment variable management
- `dataclasses`: Data structure management
- `datetime`: Timestamp handling
- `json`: Data storage

### Architecture

The application follows a modular design with these key components:

1. `CandidateInfo`: Dataclass for structured candidate data
2. `HiringAssistant`: Core class managing the interview process
3. `analyze_sentiment`: Function for response analysis
4. Streamlit UI components for user interaction

### Data Flow
1. Candidate information collection
2. Technical interview conducting
3. Response analysis and storage
4. Interview record generation

### Storage
- Candidate profiles: JSON files in `candidates/`
- Interview records: JSON files in `interviews/`
- Each file includes conversation history and sentiment analysis

## Prompt Design

The system uses carefully crafted prompts for different stages of the interview process:

### Technical Interview Prompt
The main interview prompt instructs the AI to:
1. Validate mentioned technical skills
2. Ask relevant technical questions
3. Follow up based on responses
4. Track covered topics
5. Maintain professional tone

### Sentiment Analysis Prompt
The sentiment analyzer evaluates:
- Overall sentiment (positive/neutral/negative)
- Key strengths (up to 3)
- Areas for improvement (up to 3)
- Technical confidence score (0-10)
- Communication score (0-10)

### Challenges Faced and solution

- Maintaining state across interactions - used streamlit session_state variable
- Getting consistent responses from LLM - reduced temperature for less random responses
- Carrying out interview and checking whether the interview has ended - using dedicated LLM calls

### Scope of improvement

- Moving data storage from json or datastructures to DBMS system
- Deploying on server
- Modularisation, better error handling
- Multi lingual support
- Performance optimization