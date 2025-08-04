#!/usr/bin/env python
"""
Unified entry point for the Credit Approval System.

Handles database setup, migrations, and running the Django application.
Provides a single command-line interface for all application operations
including development server, testing, data ingestion, and database management.

Usage:
    python app.py [command] [options]
    
Commands:
    runserver    - Start development server (default)
    setup        - Setup database and run migrations
    test         - Run test suite
    ingest       - Ingest customer and loan data
    [other]      - Pass through to Django management commands
"""
import os
import sys
import django
import psycopg2
from pathlib import Path
from django.core.management import execute_from_command_line
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database_if_not_exists():
    """
    Create PostgreSQL database if it doesn't exist.
    
    Attempts to connect to the target database. If the database doesn't exist,
    creates it using the default 'postgres' database connection. Includes
    retry logic for handling database server startup delays.
    
    Environment Variables:
        POSTGRES_HOST: Database host (default: localhost)
        POSTGRES_PORT: Database port (default: 5432)
        POSTGRES_USER: Database user (default: postgres)
        POSTGRES_PASSWORD: Database password (default: postgres)
        POSTGRES_DB: Target database name (default: credit_approval_db)
    
    Raises:
        SystemExit: If database creation fails or connection cannot be established
    """
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
    """
    Set up database and run migrations.
    
    Creates the database if it doesn't exist, sets up Django environment,
    creates and runs database migrations. This function ensures the
    database is ready for the application to run.
    
    Environment Variables:
        DJANGO_SETTINGS_MODULE: Django settings module (default: credit_approval.settings)
    
    Raises:
        SystemExit: If database setup fails
    """
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
    """
    Main entry point for the application.
    
    Parses command-line arguments and executes the appropriate action:
    - setup: Database setup only
    - runserver: Setup database and start development server
    - test: Setup database and run tests
    - ingest: Setup database and ingest data
    - other: Pass through to Django management commands
    
    If no command is provided, defaults to running the development server.
    
    Command Line Arguments:
        sys.argv[1]: Command to execute (optional)
        sys.argv[2:]: Additional arguments passed to Django commands
    
    Environment Variables:
        DJANGO_SETTINGS_MODULE: Django settings module
    """
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
            
            # Import and run ingestion directly
            from loans.tasks import ingest_customer_data_direct, ingest_loan_data_direct
            
            try:
                # Run customer ingestion
                print("Ingesting customer data...")
                customer_result = ingest_customer_data_direct()
                print(f"Customer data ingestion completed!")
                print(f"Status: {customer_result['status']}")
                print(f"Customers created: {customer_result.get('customers_created', 0)}")
                print(f"Customers updated: {customer_result.get('customers_updated', 0)}")
                print(f"Message: {customer_result['message']}")
                
                # Run loan ingestion
                print("\nIngesting loan data...")
                loan_result = ingest_loan_data_direct()
                print(f"Loan data ingestion completed!")
                print(f"Status: {loan_result['status']}")
                print(f"Loans created: {loan_result.get('loans_created', 0)}")
                print(f"Loans updated: {loan_result.get('loans_updated', 0)}")
                print(f"Message: {loan_result['message']}")
                
            except Exception as e:
                print(f"Error during data ingestion: {str(e)}")
                sys.exit(1)
            return
        else:
            # Pass through to Django management commands
            setup_database()
            execute_from_command_line(['manage.py'] + sys.argv[1:])
            return
    
    # Default: setup and run server
    setup_database()
    print("Starting development server...")
    # execute_from_command_line(['manage.py', 'ingest_data'])
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])

if __name__ == "__main__":
    main() 