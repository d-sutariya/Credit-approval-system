import pandas as pd
from datetime import datetime
from decimal import Decimal
from celery import shared_task
from django.db import transaction
from .models import Customer, Loan


@shared_task
def ingest_customer_data():
    """
    Ingest customer data from Excel file using background worker.
    
    Reads customer data from 'data/customer_data.xlsx' and creates or updates
    Customer records in the database. Uses atomic transactions to ensure data
    consistency.
    
    Expected Excel columns:
        customer_id: Unique customer identifier
        first_name: Customer's first name
        last_name: Customer's last name
        phone_number: Contact phone number
        monthly_salary: Monthly income
        approved_limit: Credit limit
        current_debt: Current outstanding debt
    
    Returns:
        dict: Processing result with status, counts, and message
            - status: 'success' or 'error'
            - customers_created: Number of new customers created
            - customers_updated: Number of existing customers updated
            - message: Success or error message
    """
    try:
        # Read customer data from Excel
        df = pd.read_excel('data/customer_data.xlsx')
        
        customers_created = 0
        customers_updated = 0
        
        with transaction.atomic():
            for _, row in df.iterrows():
                # Check if customer already exists
                customer, created = Customer.objects.get_or_create(
                    customer_id=row['customer_id'],
                    defaults={
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'age': 25,  # Default age since not in original data
                        'phone_number': row['phone_number'],
                        'monthly_salary': Decimal(str(row['monthly_salary'])),
                        'approved_limit': Decimal(str(row['approved_limit'])),
                        'current_debt': Decimal(str(row['current_debt'])),
                    }
                )
                
                if created:
                    customers_created += 1
                else:
                    # Update existing customer
                    customer.first_name = row['first_name']
                    customer.last_name = row['last_name']
                    customer.phone_number = row['phone_number']
                    customer.monthly_salary = Decimal(str(row['monthly_salary']))
                    customer.approved_limit = Decimal(str(row['approved_limit']))
                    customer.current_debt = Decimal(str(row['current_debt']))
                    customer.save()
                    customers_updated += 1
        
        return {
            'status': 'success',
            'customers_created': customers_created,
            'customers_updated': customers_updated,
            'message': f'Successfully processed {customers_created + customers_updated} customers'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error ingesting customer data: {str(e)}'
        }


@shared_task
def ingest_loan_data():
    """
    Ingest loan data from Excel file using background worker.
    
    Reads loan data from 'data/loan_data.xlsx' and creates or updates
    Loan records in the database. Links loans to existing customers and
    handles date parsing for start and end dates.
    
    Expected Excel columns:
        customer_id: Customer identifier (must exist in database)
        loan_id: Unique loan identifier
        loan_amount: Principal loan amount
        tenure: Loan duration in months
        interest_rate: Annual interest rate
        monthly_repayment: Monthly EMI amount
        EMIs_paid_on_time: Number of EMIs paid on time
        start_date: Loan start date
        end_date: Loan end date (can be null for active loans)
    
    Returns:
        dict: Processing result with status, counts, and message
            - status: 'success' or 'error'
            - loans_created: Number of new loans created
            - loans_updated: Number of existing loans updated
            - message: Success or error message
            
    Note:
        Loans for non-existent customers are skipped
    """
    try:
        # Read loan data from Excel
        df = pd.read_excel('data/loan_data.xlsx')
        
        loans_created = 0
        loans_updated = 0
        
        with transaction.atomic():
            for _, row in df.iterrows():
                try:
                    # Get customer
                    customer = Customer.objects.get(customer_id=row['customer_id'])
                    
                    # Parse dates
                    start_date = pd.to_datetime(row['start_date']).date()
                    end_date = pd.to_datetime(row['end_date']).date() if pd.notna(row['end_date']) else None
                    
                    # Check if loan already exists
                    loan, created = Loan.objects.get_or_create(
                        loan_id=row['loan_id'],
                        defaults={
                            'customer': customer,
                            'loan_amount': Decimal(str(row['loan_amount'])),
                            'tenure': int(row['tenure']),
                            'interest_rate': Decimal(str(row['interest_rate'])),
                            'monthly_repayment': Decimal(str(row['monthly_repayment'])),
                            'emis_paid_on_time': int(row['EMIs_paid_on_time']),
                            'start_date': start_date,
                            'end_date': end_date,
                        }
                    )
                    
                    if created:
                        loans_created += 1
                    else:
                        # Update existing loan
                        loan.customer = customer
                        loan.loan_amount = Decimal(str(row['loan_amount']))
                        loan.tenure = int(row['tenure'])
                        loan.interest_rate = Decimal(str(row['interest_rate']))
                        loan.monthly_repayment = Decimal(str(row['monthly_repayment']))
                        loan.emis_paid_on_time = int(row['EMIs_paid_on_time'])
                        loan.start_date = start_date
                        loan.end_date = end_date
                        loan.save()
                        loans_updated += 1
                        
                except Customer.DoesNotExist:
                    # Skip loans for non-existent customers
                    continue
        
        return {
            'status': 'success',
            'loans_created': loans_created,
            'loans_updated': loans_updated,
            'message': f'Successfully processed {loans_created + loans_updated} loans'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error ingesting loan data: {str(e)}'
        }


@shared_task
def ingest_all_data():
    """
    Ingest both customer and loan data using background workers.
    
    Initiates parallel processing of customer and loan data ingestion.
    Returns task IDs for monitoring the progress of both operations.
    
    Returns:
        dict: Task information
            - customer_task_id: Celery task ID for customer ingestion
            - loan_task_id: Celery task ID for loan ingestion
            - message: Confirmation message
    """
    customer_result = ingest_customer_data.delay()
    loan_result = ingest_loan_data.delay()
    
    return {
        'customer_task_id': customer_result.id,
        'loan_task_id': loan_result.id,
        'message': 'Data ingestion tasks started'
    } 