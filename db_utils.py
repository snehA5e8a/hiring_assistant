import psycopg2
from dotenv import load_dotenv
import os
import json
import bcrypt
from psycopg2.extras import Json
import ast


# Load environment variables
load_dotenv()

def hash_password(password):
    """Hash the password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify the provided password against the stored hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

class DatabaseMan:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('host'),
                database=os.getenv('database'),
                user=os.getenv('user'),
                password=os.getenv('password'),
                port=os.getenv('port'),
                sslmode='require'
            )
            self.cursor = self.conn.cursor()
            self.create_tables()
        except Exception as e:
            raise Exception(f"Database connection error: {e}")
        
    def ensure_connection(self):
        if self.conn.closed:
            self.conn = psycopg2.connect(
                host=os.getenv('host'),
                database=os.getenv('database'),
                user=os.getenv('user'),
                password=os.getenv('password'),
                port=os.getenv('port'),
                sslmode='require'
            )
        if self.cursor.closed:
            self.cursor = self.conn.cursor()

    def create_tables(self):
        CREATE_USERS_TABLE = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL
        );
        """
        CREATE_CANDIDATES_TABLE = """
        CREATE TABLE IF NOT EXISTS candidates (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(15),
            education VARCHAR(50),
            experience_years INT DEFAULT 0,
            experience_months INT DEFAULT 0,
            desired_position VARCHAR(50),
            location VARCHAR(100),
            tech_stack TEXT[],
            consent_timestamp TIMESTAMP
        );
        """
        CREATE_INTERVIEWS_TABLE = """
        CREATE TABLE IF NOT EXISTS interviews (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            conversation_history JSONB,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.cursor.execute(CREATE_USERS_TABLE)
        self.cursor.execute(CREATE_CANDIDATES_TABLE)
        self.cursor.execute(CREATE_INTERVIEWS_TABLE)
        self.conn.commit()

    def check_username_availability(self, username):
        self.ensure_connection()
        query = """
        SELECT COUNT(*) FROM USERS WHERE username = %s
        """
        self.cursor.execute(query, (username,))
        count = self.cursor.fetchone()[0]
        return count == 0  # Return True if username does not exist

    def register_user(self, username, password, role):
        self.ensure_connection()
        hashed_password = hash_password(password)
        query = """
        INSERT INTO users (username, password, role)
        VALUES (%s, %s, %s)
        RETURNING id
        """
        self.cursor.execute(query, (username, hashed_password, role))
        user_id = self.cursor.fetchone()[0]  # Retrieve the auto-generated user ID
        self.conn.commit()
        return user_id  # Return the user ID
    
    def login_user(self, username, password):
        self.ensure_connection()
        """Verify the user credentials."""
        query = "SELECT password, role, id FROM users WHERE username = %s"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()
        
        if result:
            stored_password, role, user_id = result
            if verify_password(password, stored_password):
                return True, role, user_id
            else:
                return False, None, None
        else:
            return False, None, None

    def save_candidate(self, user_id, candidate_data):

        self.ensure_connection()
        query = """
        INSERT INTO candidates (user_id, full_name, email, phone, education, experience_years, experience_months, desired_position, location, tech_stack, consent_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """

        # Prepare the values for insertion, including the user_id
        values = (
            user_id,  # Link the candidate to the user via user_id
            candidate_data['full_name'],
            candidate_data['email'],
            candidate_data.get('phone', None),
            candidate_data.get('education', None),
            candidate_data.get('experience_years', 0),
            candidate_data.get('experience_months', 0),
            candidate_data.get('desired_position', None),
            candidate_data.get('location', None),
            candidate_data.get('tech_stack', []),
            candidate_data.get('consent_timestamp', None)
        )

        # Execute the query and commit the transaction
        self.cursor.execute(query, values)
        self.conn.commit()

        # Return the id of the newly created candidate
        return self.cursor.fetchone()[0]  # This will return the newly inserted candidate's id

    def get_candidate_info(self, user_id):
        
        self.ensure_connection()
        if not isinstance(user_id, int):
            raise ValueError(f"Invalid user_id: Expected an integer, got {type(user_id).__name__}")

        # Fetch column names dynamically from the database
        self.cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'candidates'
        """)
        available_columns = [row[0] for row in self.cursor.fetchall()]

        # Define the expected columns and their defaults
        default_columns = {
            "full_name": None,
            "email": None,
            "phone": None,
            "education": None,
            "experience_years": None,
            "experience_months": None,
            "desired_position": None,
            "location": None,
            "tech_stack": None,
            "consent_timestamp": None
        }

        # Filter out columns that exist in the table
        selected_columns = [col for col in default_columns if col in available_columns]
        column_query = ", ".join(selected_columns)

        # Fetch candidate info using the available columns
        query = f"""
            SELECT {column_query}
            FROM candidates
            WHERE user_id = %s
        """
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        if not result:
            return False
        user_info = default_columns.copy()

        if result:
        # Map the result to the expected columns
            for col, val in zip(selected_columns, result):
                user_info[col] = val
        return user_info

    def update_candidate_info(self, user_id, updated_info):
        self.ensure_connection()
        query = """
        UPDATE candidates
        SET full_name = %s, email = %s, phone = %s, education = %s, 
            experience_years = %s, experience_months=%s, desired_position = %s, location = %s, tech_stack = %s, consent_timestamp = %s
        WHERE user_id = %s
        """
        self.cursor.execute(
            query,
            (
                updated_info["full_name"],
                updated_info["email"],
                updated_info["phone"],
                updated_info["education"],
                updated_info["experience_years"],
                updated_info["experience_months"],
                updated_info["desired_position"],
                updated_info["location"],
                updated_info["tech_stack"],  # TEXT[] type accepts Python lists directly
                updated_info.get("consent_timestamp"),  # Include if you want to update the timestamp
                user_id
            )
        )
        self.conn.commit()

    def delete_candidate_info(self, user_id):
        self.ensure_connection()
        query = "DELETE FROM candidates WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        self.conn.commit()

    def save_conversation_to_db(self, user_id, conversation_history, sentiment_data):
        try:
            if isinstance(sentiment_data, str):
                sentiment_data = json.loads(sentiment_data)

            # Insert conversation history and evaluation data into the interviews table
            insert_query = """
            INSERT INTO interviews (user_id, conversation_history, overall_sentiment, key_strengths, 
                                areas_for_improvement, technical_confidence_score, 
                                conversation_authenticity_score, communication_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.cursor.execute(insert_query, (
                user_id, 
                Json(conversation_history),
                sentiment_data.get('overall_sentiment'),
                sentiment_data.get('key_strengths'),
                sentiment_data.get('areas_for_improvement'),
                sentiment_data.get('technical_confidence_score'),
                sentiment_data.get('conversation_authenticity_score'),
                sentiment_data.get('communication_score')
            ))
            
            # Commit the transaction
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
        finally:
            self.cursor.close()
            self.conn.close()
    
    def get_interviews(self, user_id):
        self.ensure_connection()
        try:
            query = """
            SELECT conversation_history 
            FROM interviews 
            WHERE user_id = %s
            """
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()
            
            if result and result[0]:  # If a conversation history exists
                return result[0]  # Assuming JSON format in DB
            
            return False  # No conversation found
        except Exception as e:
            print(f"Error checking conversation: {e}")
            return False
        finally:
            self.cursor.close()
            self.conn.close()
              
    def fetch_user_table(self):
        self.ensure_connection()
        query = """
        SELECT 
            c.full_name, 
            c.desired_position, 
            u.id as user_id
        FROM 
            candidates c
        JOIN 
            users u
        ON 
            c.user_id = u.id
        WHERE 
            u.role = 'Candidate';
    """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        self.conn.close()
        return rows
    
    def fetch_interview_evaluation(self, user_id):
        self.ensure_connection()
        query = """
            SELECT overall_sentiment, key_strengths, technical_confidence_score, conversation_authenticity_score, communication_score, areas_for_improvement
            FROM interviews 
            WHERE user_id = %s
            """
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        
        if result:
            return {
            "Overall Sentiment": result[0],
            "Key Strengths": ast.literal_eval(result[1]) if result[1] else None,
            "Technical Confidence Score": result[2],
            "Conversation Authenticity Score": result[3] if result[3] is not None else "Not Evaluated",
            "Communication Score": result[4],
            "Areas for Improvement": ast.literal_eval(result[5]) if result[5] else None
            }
        else:
            return False
    