# Credit Approval System

A Django-based credit approval system that evaluates loan eligibility based on customer credit scores and historical data.

## Features

- Customer registration with automatic approved limit calculation
- Credit score calculation based on historical loan data
- Loan eligibility checking with interest rate adjustments
- Loan creation and management
- Background data ingestion from Excel files
- RESTful API endpoints
- Dockerized deployment

## Technology Stack

- **Backend**: Django 4.2.7 + Django REST Framework
- **Database**: PostgreSQL
- **Background Tasks**: Celery + Redis
- **Containerization**: Docker + Docker Compose
- **Data Processing**: Pandas + OpenPyXL

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

3. **Run database migrations**
   ```bash
   docker-compose exec web python app.py migrate
   ```

4. **Ingest initial data from Excel files**
   ```bash
   docker-compose exec web python app.py ingest
   ```

5. **Create a superuser (optional)**
   ```bash
   docker-compose exec web python app.py createsuperuser
   ```

The application will be available at:
- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/

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
    "customer_id": 1,
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
    "loan_id": 1,
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
- `customer_id` (Primary Key)
- `first_name`, `last_name`
- `age`, `phone_number`
- `monthly_salary`, `approved_limit`, `current_debt`
- `created_at`, `updated_at`

### Loan
- `loan_id` (Primary Key)
- `customer` (Foreign Key)
- `loan_amount`, `tenure`, `interest_rate`
- `monthly_repayment`, `emis_paid_on_time`
- `start_date`, `end_date`, `status`
- `created_at`, `updated_at`

## Background Tasks

The system uses Celery for background data ingestion:

- **Customer Data Ingestion**: Processes `customer_data.xlsx`
- **Loan Data Ingestion**: Processes `loan_data.xlsx`
- **Combined Ingestion**: Runs both tasks

## Development

### Running Tests
The project includes comprehensive unit tests for models, services, and API endpoints.

```bash
# Run all tests
docker-compose exec web python app.py test

# Run specific test classes
docker-compose exec web python app.py test loans.tests.CustomerModelTest
docker-compose exec web python app.py test loans.tests.LoanModelTest
docker-compose exec web python app.py test loans.tests.CreditScoreServiceTest
docker-compose exec web python app.py test loans.tests.APITest

# Run with verbose output
docker-compose exec web python app.py test -v 2

# Run tests locally (if not using Docker)
python app.py test
python app.py test loans.tests.APITest -v 2
```

### Code Quality
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes

### Database Migrations
```bash
docker-compose exec web python app.py makemigrations
docker-compose exec web python app.py migrate
```

## Deployment

The application is fully containerized and can be deployed using:

```bash
docker-compose up -d
```

All services (Django, PostgreSQL, Redis, Celery) are orchestrated through Docker Compose.

## Error Handling

The API includes comprehensive error handling:
- **400 Bad Request**: Invalid input data
- **404 Not Found**: Customer/Loan not found
- **500 Internal Server Error**: Server-side errors

All errors return structured JSON responses with descriptive messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes as part of an internship assignment. 