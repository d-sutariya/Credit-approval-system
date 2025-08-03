#!/usr/bin/env python
"""
Unified entry point for the Credit Approval System
Handles database setup, migrations, and running the Django application
"""
import os
import sys
import django
import psycopg2
from django.core.management import execute_from_command_line
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database_if_not_exists():
    """Create PostgreSQL database if it doesn't exist"""
    import time
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Try to connect to the target database
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                database=os.getenv('POSTGRES_DB', 'credit_approval_db')
            )
            conn.close()
            print("Database connection successful")
            return
        except psycopg2.OperationalError as e:
            if "does not exist" in str(e):
                # Database doesn't exist, create it
                try:
                    conn = psycopg2.connect(
                        host=os.getenv('POSTGRES_HOST', 'localhost'),
                        port=os.getenv('POSTGRES_PORT', '5432'),
                        user=os.getenv('POSTGRES_USER', 'postgres'),
                        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                        database='postgres'
                    )
                    conn.autocommit = True
                    cursor = conn.cursor()
                    db_name = os.getenv('POSTGRES_DB', 'credit_approval_db')
                    cursor.execute(f"CREATE DATABASE {db_name}")
                    cursor.close()
                    conn.close()
                    print(f"Created database '{db_name}'")
                    return
                except Exception as create_error:
                    print(f"Error creating database: {create_error}")
                    sys.exit(1)
            else:
                # Database server not ready, retry
                if attempt < max_retries - 1:
                    print(f"Database not ready, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to connect to database after {max_retries} attempts")
                    sys.exit(1)

def setup_database():
    """Set up database and run migrations"""
    print("Setting up database...")
    
    # Create database if it doesn't exist
    create_database_if_not_exists()
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'credit_approval.settings')
    
    # Setup Django
    django.setup()
    
    # Create migrations
    print("Creating migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    # Run migrations
    print("Running migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    print("Database setup complete!")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'setup':
            # Just setup database
            setup_database()
            return
        elif command == 'runserver':
            # Setup database and run server
            setup_database()
            print("Starting development server...")
            execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
            return
        elif command == 'test':
            # Setup database and run tests
            setup_database()
            print("Running tests...")
            execute_from_command_line(['manage.py', 'test'])
            return
        elif command == 'ingest':
            # Setup database and ingest data
            setup_database()
            print("Ingesting data...")
            execute_from_command_line(['manage.py', 'ingest_data'])
            return
        else:
            # Pass through to Django management commands
            setup_database()
            execute_from_command_line(['manage.py'] + sys.argv[1:])
            return
    
    # Default: setup and run server
    setup_database()
    print("Starting development server...")
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])

if __name__ == "__main__":
    main() 