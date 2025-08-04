# Credit Approval System

A Django-based credit approval system that evaluates loan eligibility based on customer credit scores and historical data. The system automatically ingests data from Excel files and provides a unified entry point for all operations.

## Features

- **Unified Entry Point**: Single `app.py` command handles all operations
- **Automatic Data Ingestion**: Excel data loaded automatically on startup
- **Customer Registration**: Automatic approved limit calculation (36 × monthly salary)
- **Credit Score Calculation**: Based on historical loan data (0-100 scale)
- **Loan Eligibility Checking**: With interest rate adjustments
- **Loan Creation and Management**: Complete loan lifecycle
- **Background Tasks**: Celery for data processing
- **RESTful API**: Complete API for all operations
- **Dockerized Deployment**: Production-ready containerization
- **Cross-Platform**: Uses pathlib for Windows/Linux/macOS compatibility

## Technology Stack

- **Backend**: Django 4.2.7 + Django REST Framework 3.14.0
- **Database**: PostgreSQL 15
- **Background Tasks**: Celery 5.3.4 + Redis 7-alpine
- **Containerization**: Docker + Docker Compose
- **Data Processing**: Pandas 2.1.4 + OpenPyXL 3.1.2
- **Environment**: python-decouple 3.8

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Credit-approval-system
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

The application will automatically:
- Setup the PostgreSQL database
- Run Django migrations
- Ingest customer and loan data from Excel files
- Start the development server

The application will be available at:
- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/

### Local Development (Without Docker)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL database**
   - Create database: `credit_approval_db`
   - Update environment variables in `.env` file

3. **Run the application**
   ```bash
   python app.py
   ```

## Unified Command Interface

The `app.py` file provides a unified entry point for all operations:

```bash
# Start development server (default)
python app.py

# Setup database and run migrations
python app.py setup

# Ingest data from Excel files
python app.py ingest

# Run tests
python app.py test

# Run any Django management command
python app.py makemigrations
python app.py migrate
python app.py createsuperuser
python app.py shell
```

## API Endpoints

### 1. Register Customer
**POST** `/api/register/`

Register a new customer with automatic approved limit calculation.

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "monthly_income": 50000,
    "phone_number": 9876543210
}
```

**Response:**
```json
{
    "customer_id": 301,
    "name": "John Doe",
    "age": 30,
    "monthly_income": 50000,
    "approved_limit": 1800000,
    "phone_number": 9876543210
}
```

### 2. Check Loan Eligibility
**POST** `/api/check-eligibility/`

Check if a customer is eligible for a loan based on credit score.

**Request Body:**
```json
{
    "customer_id": 1,
    "loan_amount": 500000,
    "interest_rate": 12.5,
    "tenure": 24
}
```

**Response:**
```json
{
    "customer_id": 1,
    "approval": true,
    "interest_rate": 12.5,
    "corrected_interest_rate": 12.5,
    "tenure": 24,
    "monthly_installment": 23500.50
}
```

### 3. Create Loan
**POST** `/api/create-loan/`

Create a new loan if the customer is eligible.

**Request Body:**
```json
{
    "customer_id": 1,
    "loan_amount": 500000,
    "interest_rate": 12.5,
    "tenure": 24
}
```

**Response:**
```json
{
    "loan_id": 783,
    "customer_id": 1,
    "loan_approved": true,
    "message": "Loan approved successfully",
    "monthly_installment": 23500.50
}
```

### 4. View Loan Details
**GET** `/api/view-loan/{loan_id}/`

Get detailed information about a specific loan.

**Response:**
```json
{
    "loan_id": 1,
    "customer": {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": 9876543210,
        "age": 30
    },
    "loan_amount": 500000,
    "interest_rate": 12.5,
    "monthly_repayment": 23500.50,
    "tenure": 24,
    "repayments_left": 24
}
```

### 5. View Customer Loans
**GET** `/api/view-loans/{customer_id}/`

Get all loans for a specific customer.

**Response:**
```json
[
    {
        "loan_id": 1,
        "loan_amount": 500000,
        "interest_rate": 12.5,
        "monthly_repayment": 23500.50,
        "repayments_left": 24
    }
]
```

## Credit Score Calculation

The system calculates credit scores (0-100) based on:

1. **Past Loans Paid on Time (40 points)**
   - Percentage of loans where all EMIs were paid on time

2. **Number of Loans Taken (20 points)**
   - 0 loans: 10 points
   - 1-3 loans: 20 points
   - 4-5 loans: 15 points
   - 6+ loans: 10 points

3. **Loan Activity in Current Year (20 points)**
   - 0 loans: 10 points
   - 1 loan: 20 points
   - 2+ loans: 15 points

4. **Loan Approved Volume (20 points)**
   - 0 volume: 10 points
   - ≤10 lakhs: 15 points
   - ≤50 lakhs: 20 points
   - >50 lakhs: 18 points

## Loan Approval Criteria

- **Credit Score > 50**: Approve any loan
- **Credit Score 30-50**: Approve loans with interest rate > 12%
- **Credit Score 10-30**: Approve loans with interest rate > 16%
- **Credit Score < 10**: No loans approved
- **EMI > 50% of monthly salary**: No loans approved

## Data Models

### Customer
- `customer_id` (AutoField Primary Key)
- `first_name`, `last_name`, `age`
- `phone_number` (unique)
- `monthly_salary`, `approved_limit`, `current_debt`
- `created_at`, `updated_at`

### Loan
- `loan_id` (AutoField Primary Key)
- `customer` (Foreign Key to Customer)
- `loan_amount`, `tenure`, `interest_rate`
- `monthly_repayment`, `emis_paid_on_time`
- `start_date`, `end_date`, `status`
- `created_at`, `updated_at`

## Data Ingestion

The system automatically ingests data from Excel files:

### Customer Data (`data/customer_data.xlsx`)
Expected columns:
- Customer ID, First Name, Last Name, Age
- Phone Number, Monthly Salary, Approved Limit

### Loan Data (`data/loan_data.xlsx`)
Expected columns:
- Customer ID, Loan ID, Loan Amount, Tenure
- Interest Rate, Monthly payment, EMIs paid on Time
- Date of Approval, End Date

### Ingestion Process
1. **Automatic on startup** - Data loaded when running `python app.py`
2. **Manual ingestion** - Run `python app.py ingest`
3. **Sequence reset** - Auto-increment sequences updated after ingestion

## Development

### Running Tests
```bash
# Run all tests
python app.py test

# Run specific test classes
python app.py test loans.tests.CustomerModelTest
python app.py test loans.tests.LoanModelTest
python app.py test loans.tests.CreditScoreServiceTest
python app.py test loans.tests.APITest

# Run with verbose output
python app.py test -v 2
```

### Database Operations
```bash
# Setup database and run migrations
python app.py setup

# Create new migrations
python app.py makemigrations

# Apply migrations
python app.py migrate

# Create superuser
python app.py createsuperuser
```

### Background Tasks
```bash
# Start Celery worker (for background tasks)
celery -A credit_approval worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A credit_approval beat --loglevel=info
```

## Docker Deployment

### Production Deployment
```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### Services
- **web**: Django application (port 8000)
- **db**: PostgreSQL database (port 5432)
- **redis**: Redis cache (port 6379)
- **celery**: Background task worker

### Startup Sequence
The Docker container automatically runs:
1. Database setup and migrations
2. Data ingestion from Excel files
3. Django development server

## Error Handling

The API includes comprehensive error handling:
- **400 Bad Request**: Invalid input data
- **404 Not Found**: Customer/Loan not found
- **500 Internal Server Error**: Server-side errors

All errors return structured JSON responses with descriptive messages.

## File Structure

```
Credit-approval-system/
├── app.py                 # Unified entry point
├── start.sh              # Docker startup script
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Service orchestration
├── data/                # Excel data files
│   ├── customer_data.xlsx
│   └── loan_data.xlsx
├── credit_approval/     # Django project
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── loans/              # Django app
│   ├── models.py       # Data models
│   ├── views.py        # API views
│   ├── serializers.py  # Data serialization
│   ├── services.py     # Business logic
│   ├── tasks.py        # Background tasks
│   └── tests.py        # Unit tests
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes as part of an internship assignment. 