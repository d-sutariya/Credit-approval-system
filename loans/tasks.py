import pandas as pd
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from celery import shared_task
from django.db import transaction
from .models import Customer, Loan


def ingest_customer_data_direct():
    """
    Ingest customer data from Excel file directly (without Celery).
    
    Reads customer data from 'data/customer_data.xlsx' and creates or updates
    Customer records in the database. Uses atomic transactions to ensure data
    consistency.
    
    Expected Excel columns:
        Customer ID: Unique customer identifier
        First Name: Customer's first name
        Last Name: Customer's last name
        Age: Customer's age
        Phone Number: Contact phone number
        Monthly Salary: Monthly income
        Approved Limit: Credit limit
    
    Returns:
        dict: Processing result with status, counts, and message
            - status: 'success' or 'error'
            - customers_created: Number of new customers created
            - customers_updated: Number of existing customers updated
            - message: Success or error message
    """
    try:
        print("Reading customer data from Excel file...")
        # Read customer data from Excel using pathlib for cross-platform support
        data_file = Path('data/customer_data.xlsx')
        df = pd.read_excel(data_file)
        print(f"Found {len(df)} customer records in Excel file")
        
        customers_created = 0
        customers_updated = 0
        
        print("Processing customer records...")
        with transaction.atomic():
            for index, row in df.iterrows():
                # Check if customer already exists
                customer, created = Customer.objects.get_or_create(
                    customer_id=row['Customer ID'],
                    defaults={
                        'first_name': row['First Name'],
                        'last_name': row['Last Name'],
                        'age': int(row['Age']),
                        'phone_number': row['Phone Number'],
                        'monthly_salary': Decimal(str(row['Monthly Salary'])),
                        'approved_limit': Decimal(str(row['Approved Limit'])),
                        'current_debt': Decimal('0'),  # Default value since not in Excel
                    }
                )
                
                if created:
                    customers_created += 1
                    print(f"  Created customer: {row['First Name']} {row['Last Name']} (ID: {row['Customer ID']})")
                else:
                    # Update existing customer
                    customer.first_name = row['First Name']
                    customer.last_name = row['Last Name']
                    customer.age = int(row['Age'])
                    customer.phone_number = row['Phone Number']
                    customer.monthly_salary = Decimal(str(row['Monthly Salary']))
                    customer.approved_limit = Decimal(str(row['Approved Limit']))
                    customer.save()
                    customers_updated += 1
                    print(f"  Updated customer: {row['First Name']} {row['Last Name']} (ID: {row['Customer ID']})")
        
        # Reset the auto-increment sequence for customers table
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval('customers_customer_id_seq', (SELECT MAX(customer_id) FROM customers))")
        
        print(f"Customer data processing completed!")
        print(f"   Total records processed: {len(df)}")
        print(f"   New customers created: {customers_created}")
        print(f"   Existing customers updated: {customers_updated}")
        
        return {
            'status': 'success',
            'customers_created': customers_created,
            'customers_updated': customers_updated,
            'message': f'Successfully processed {customers_created + customers_updated} customers'
        }
        
    except Exception as e:
        print(f"Error ingesting customer data: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error ingesting customer data: {str(e)}'
        }


def ingest_loan_data_direct():
    """
    Ingest loan data from Excel file directly (without Celery).
    
    Reads loan data from 'data/loan_data.xlsx' and creates or updates
    Loan records in the database. Links loans to existing customers and
    handles date parsing for start and end dates.
    
    Expected Excel columns:
        Customer ID: Customer identifier (must exist in database)
        Loan ID: Unique loan identifier
        Loan Amount: Principal loan amount
        Tenure: Loan duration in months
        Interest Rate: Annual interest rate
        Monthly payment: Monthly EMI amount
        EMIs paid on Time: Number of EMIs paid on time
        Date of Approval: Loan start date
        End Date: Loan end date (can be null for active loans)
    
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
        print("Reading loan data from Excel file...")
        # Read loan data from Excel using pathlib for cross-platform support
        data_file = Path('data/loan_data.xlsx')
        df = pd.read_excel(data_file)
        print(f"Found {len(df)} loan records in Excel file")
        
        loans_created = 0
        loans_updated = 0
        skipped_loans = 0
        
        print("Processing loan records...")
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # Get customer
                    customer = Customer.objects.get(customer_id=row['Customer ID'])
                    
                    # Parse dates
                    start_date = pd.to_datetime(row['Date of Approval']).date()
                    end_date = pd.to_datetime(row['End Date']).date() if pd.notna(row['End Date']) else None
                    
                    # Check if loan already exists
                    loan, created = Loan.objects.get_or_create(
                        loan_id=row['Loan ID'],
                        defaults={
                            'customer': customer,
                            'loan_amount': Decimal(str(row['Loan Amount'])),
                            'tenure': int(row['Tenure']),
                            'interest_rate': Decimal(str(row['Interest Rate'])),
                            'monthly_repayment': Decimal(str(row['Monthly payment'])),
                            'emis_paid_on_time': int(row['EMIs paid on Time']),
                            'start_date': start_date,
                            'end_date': end_date,
                        }
                    )
                    
                    if created:
                        loans_created += 1
                        print(f"  Created loan: ID {row['Loan ID']} for customer {customer.first_name} {customer.last_name} (Amount: ₹{row['Loan Amount']:,})")
                    else:
                        # Update existing loan
                        loan.customer = customer
                        loan.loan_amount = Decimal(str(row['Loan Amount']))
                        loan.tenure = int(row['Tenure'])
                        loan.interest_rate = Decimal(str(row['Interest Rate']))
                        loan.monthly_repayment = Decimal(str(row['Monthly payment']))
                        loan.emis_paid_on_time = int(row['EMIs paid on Time'])
                        loan.start_date = start_date
                        loan.end_date = end_date
                        loan.save()
                        loans_updated += 1
                        print(f"  Updated loan: ID {row['Loan ID']} for customer {customer.first_name} {customer.last_name} (Amount: ₹{row['Loan Amount']:,})")
                        
                except Customer.DoesNotExist:
                    # Skip loans for non-existent customers
                    skipped_loans += 1
                    print(f"  Skipped loan ID {row['Loan ID']}: Customer ID {row['Customer ID']} not found")
                    continue
        
        # Reset the auto-increment sequence for loans table
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval('loans_loan_id_seq', (SELECT MAX(loan_id) FROM loans))")
        
        print(f"Loan data processing completed!")
        print(f"   Total records processed: {len(df)}")
        print(f"   New loans created: {loans_created}")
        print(f"   Existing loans updated: {loans_updated}")
        print(f"   Skipped loans (customer not found): {skipped_loans}")
        
        return {
            'status': 'success',
            'loans_created': loans_created,
            'loans_updated': loans_updated,
            'message': f'Successfully processed {loans_created + loans_updated} loans'
        }
        
    except Exception as e:
        print(f"Error ingesting loan data: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error ingesting loan data: {str(e)}'
        }


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
    return ingest_customer_data_direct()


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
    return ingest_loan_data_direct()


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