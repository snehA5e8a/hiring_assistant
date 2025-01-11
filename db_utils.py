import psycopg2
from dotenv import load_dotenv
import os
import bcrypt

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
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(15),
            experience VARCHAR(50),
            desired_position VARCHAR(50),
            location VARCHAR(100),
            tech_stack TEXT[],
            consent_timestamp TIMESTAMP
        );
        """
        CREATE_INTERVIEWS_TABLE = """
        CREATE TABLE IF NOT EXISTS interviews (
            id SERIAL PRIMARY KEY,
            candidate_id INT NOT NULL,
            conversation_history JSONB,
            topics_covered TEXT[],
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
        );
        """
        self.cursor.execute(CREATE_USERS_TABLE)
        self.cursor.execute(CREATE_CANDIDATES_TABLE)
        self.cursor.execute(CREATE_INTERVIEWS_TABLE)
        self.conn.commit()

    def register_user(self, username, password, role):
        hashed_password = hash_password(password)
        query = """
        INSERT INTO USERS (username, password, role)
        VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (username, hashed_password, role))
        self.conn.commit()

    

    def save_candidate(self, full_name, email, phone, experience, desired_position, location, tech_stack, consent_timestamp):
        query = """
        INSERT INTO candidates (full_name, email, phone, experience, desired_position, location, tech_stack, consent_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        self.cursor.execute(query, (full_name, email, phone, experience, desired_position, location, tech_stack, consent_timestamp))
        self.conn.commit()
        return self.cursor.fetchone()[0]  # Return candidate ID


    def execute_query(self, query, params=None):
        """Execute a query with optional parameters."""
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Database query failed: {e}")
            raise

    def fetch_one(self, query, params=None):
        """Fetch a single record."""
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetch_all(self, query, params=None):
        """Fetch all records."""
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        """Close the database connection."""
        self.cursor.close()
        self.conn.close()
