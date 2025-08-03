from django.core.management.base import BaseCommand
from loans.tasks import ingest_all_data


class Command(BaseCommand):
    help = 'Ingest customer and loan data from Excel files using background workers'

    def handle(self, *args, **options):
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