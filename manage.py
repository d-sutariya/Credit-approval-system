#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

This file provides the standard Django management command interface.
It loads environment variables and sets up the Django environment
before executing management commands.

Usage:
    python manage.py [command] [options]
    
Examples:
    python manage.py runserver
    python manage.py makemigrations
    python manage.py migrate
    python manage.py test
    python manage.py ingest_data
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """
    Run administrative tasks.
    
    Sets up the Django environment and executes management commands.
    This function is the entry point for all Django management operations.
    
    Environment Variables:
        DJANGO_SETTINGS_MODULE: Django settings module (default: credit_approval.settings)
    
    Command Line Arguments:
        sys.argv: Command and arguments to execute
        
    Raises:
        ImportError: If Django is not installed or not available in PYTHONPATH
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'credit_approval.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main() 