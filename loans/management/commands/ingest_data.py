from django.core.management.base import BaseCommand
from loans.tasks import ingest_all_data


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

    def handle(self, *args, **options):
        """
        Execute the data ingestion command.
        
        Initiates background tasks for processing customer_data.xlsx and
        loan_data.xlsx files. Returns task IDs for monitoring progress.
        
        Args:
            *args: Additional command arguments (unused)
            *options: Command options (unused)
            
        Returns:
            None: Outputs results to stdout
            
        Raises:
            Exception: If task initiation fails
        """
        self.stdout.write('Starting data ingestion...')
        
        try:
            result = ingest_all_data.delay()
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