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
            candidate_id INT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
            conversation_history JSONB,
            topics_covered TEXT[],
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.cursor.execute(CREATE_USERS_TABLE)
        self.cursor.execute(CREATE_CANDIDATES_TABLE)
        self.cursor.execute(CREATE_INTERVIEWS_TABLE)
        self.conn.commit()

    def check_username_availability(self, username):
        query = """
        SELECT COUNT(*) FROM USERS WHERE username = %s
        """
        self.cursor.execute(query, (username,))
        count = self.cursor.fetchone()[0]
        return count == 0  # Return True if username does not exist

    def register_user(self, username, password, role):
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
        """Verify the user credentials."""
        query = "SELECT password, role, id FROM users WHERE username = %s"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()
        
        if result:
            stored_password, role, user_id = result
            print('line97 login user fun', type(user_id)) # debugging
            if verify_password(password, stored_password):
                return True, role, user_id
            else:
                return False, None, None
        else:
            return False, None, None

    def save_candidate(self, **candidate_data):
        query = """
        INSERT INTO candidates (full_name, email, phone, experience_years, experience_months, desired_position, location, tech_stack, consent_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        values = (
        candidate_data['full_name'],
        candidate_data['email'],
        candidate_data['phone'],
        candidate_data['education'],
        candidate_data['experience_years'],
        candidate_data['experience_months'],
        candidate_data['desired_position'],
        candidate_data['location'],
        candidate_data['tech_stack'],
        candidate_data['consent_timestamp'],
    )

        self.cursor.execute(query, values)
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

    def get_candidate_info(self, user_id):
        """
        Fetch candidate information for a given user_id, handling missing columns gracefully.
        """
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
            WHERE id = %s
        """
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()

        user_info = default_columns.copy()

        if result:
        # Map the result to the expected columns
            for col, val in zip(selected_columns, result):
                user_info[col] = val
        return user_info

    def update_candidate_info(self, user_id, updated_info):
        """
        Update candidate information for a given user_id.
        """
        query = """
        UPDATE candidates
        SET full_name = %s, email = %s, phone = %s, education = %s, 
            experience_years = %d, experience_months=%d, desired_position = %s, location = %s, tech_stack = %s, consent_timestamp = %s
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
        """
        Delete candidate information for a given user_id.
        """
        query = "DELETE FROM candidates WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        self.conn.commit()

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
