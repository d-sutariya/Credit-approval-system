from django.core.management.base import BaseCommand
from loans.tasks import ingest_all_data, ingest_customer_data, ingest_loan_data


class Command(BaseCommand):
    """
    Django management command for ingesting customer and loan data.
    
    This command initiates background processing of Excel data files to populate
    the database with customer and loan information. Uses Celery workers for
    asynchronous processing to handle large datasets efficiently.
    
    Usage:
        python manage.py ingest_data
        python app.py ingest_data
    """
    help = 'Ingest customer and loan data from Excel files using background workers'

    def add_arguments(self, parser):
        """
        Add command line arguments.
        
        Args:
            parser: Argument parser instance
        """
        parser.add_argument(
            '--direct',
            action='store_true',
            help='Run ingestion directly without Celery (for local development)',
        )

    def handle(self, *args, **options):
        """
        Execute the data ingestion command.
        
        Initiates background tasks for processing customer_data.xlsx and
        loan_data.xlsx files. Returns task IDs for monitoring progress.
        
        Args:
            *args: Additional command arguments (unused)
            *options: Command options including --direct flag
            
        Returns:
            None: Outputs results to stdout
            
        Raises:
            Exception: If task initiation fails
        """
        self.stdout.write('Starting data ingestion...')
        
        if options['direct']:
            # Direct ingestion without Celery
            self.stdout.write('Running direct ingestion (no Celery)...')
            try:
                # Run customer ingestion
                customer_result = ingest_customer_data()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Customer data ingestion completed!\n'
                        f'Status: {customer_result["status"]}\n'
                        f'Customers created: {customer_result.get("customers_created", 0)}\n'
                        f'Customers updated: {customer_result.get("customers_updated", 0)}\n'
                        f'Message: {customer_result["message"]}'
                    )
                )
                
                # Run loan ingestion
                loan_result = ingest_loan_data()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Loan data ingestion completed!\n'
                        f'Status: {loan_result["status"]}\n'
                        f'Loans created: {loan_result.get("loans_created", 0)}\n'
                        f'Loans updated: {loan_result.get("loans_updated", 0)}\n'
                        f'Message: {loan_result["message"]}'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error during direct ingestion: {str(e)}')
                )
        else:
            # Celery background task ingestion
            try:
                # Start the background task
                task_result = ingest_all_data.delay()
                
                # Get the actual result from the task
                result = task_result.get()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Data ingestion tasks started successfully!\n'
                        f'Customer task ID: {result["customer_task_id"]}\n'
                        f'Loan task ID: {result["loan_task_id"]}\n'
                        f'Message: {result["message"]}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error starting data ingestion: {str(e)}')
                ) 