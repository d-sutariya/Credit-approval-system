# Quick Start Guide

## Local Development Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start PostgreSQL (if not running)
```bash
# Option 1: Using Docker (recommended)
docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:13

# Option 2: If you have PostgreSQL installed locally
# Make sure PostgreSQL service is running
```

### 3. Run the Application
```bash
# Start the server (automatically sets up database and runs migrations)
python app.py

# Or use specific commands:
python app.py runserver    # Start server
python app.py test         # Run tests
python app.py setup        # Just setup database
python app.py ingest       # Ingest Excel data
```

### 4. Access API Endpoints
- Register Customer: `POST http://localhost:8000/api/register/`
- Check Eligibility: `POST http://localhost:8000/api/check-eligibility/`
- Create Loan: `POST http://localhost:8000/api/create-loan/`
- View Loan: `GET http://localhost:8000/api/view-loan/{loan_id}/`
- View Customer Loans: `GET http://localhost:8000/api/view-loans/{customer_id}/`

## Example API Calls

### Register a Customer
```bash
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "monthly_income": 50000,
    "phone_number": 9876543210
  }'
```

### Check Loan Eligibility
```bash
curl -X POST http://localhost:8000/api/check-eligibility/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "loan_amount": 500000,
    "interest_rate": 12.5,
    "tenure": 24
  }'
```

## Notes
- Uses PostgreSQL database as per assignment requirements
- Celery is disabled for local development
- All data is stored in PostgreSQL database 'credit_approval_db' 