from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import math


class Customer(models.Model):
    """
    Customer model representing individuals who can apply for loans.
    
    Stores customer information including personal details, financial information,
    and credit limits. Provides methods for calculating approved limits and
    tracking current loan obligations.
    
    Attributes:
        customer_id: Auto-generated unique identifier
        first_name: Customer's first name
        last_name: Customer's last name
        age: Customer's age (18-100)
        phone_number: Unique contact phone number
        monthly_salary: Monthly income/salary
        approved_limit: Calculated credit limit (36 * monthly_salary)
        current_debt: Current outstanding debt amount
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField(validators=[MinValueValidator(18), MaxValueValidator(100)])
    phone_number = models.BigIntegerField(unique=True)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2)
    approved_limit = models.DecimalField(max_digits=12, decimal_places=2)
    current_debt = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'

    def __str__(self):
        """
        String representation of the customer.
        
        Returns:
            str: Customer name and ID
        """
        return f"{self.first_name} {self.last_name} (ID: {self.customer_id})"

    @property
    def name(self):
        """
        Get customer's full name.
        
        Returns:
            str: Concatenated first and last name
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def monthly_income(self):
        """
        Get customer's monthly income (alias for monthly_salary).
        
        Returns:
            Decimal: Monthly salary/income
        """
        return self.monthly_salary

    @staticmethod
    def calculate_approved_limit(monthly_salary):
        """
        Calculate approved credit limit based on monthly salary.
        
        Formula: 36 * monthly_salary, rounded to nearest lakh (100,000)
        
        Args:
            monthly_salary: Customer's monthly income
            
        Returns:
            Decimal: Calculated approved limit rounded to nearest lakh
        """
        limit = float(monthly_salary) * 36
        # Round to nearest lakh (100000)
        return round(limit / 100000) * 100000

    def get_current_loans_total(self):
        """
        Get total amount of current active loans for this customer.
        
        Returns:
            Decimal: Sum of all active loan amounts (0 if no active loans)
        """
        return self.loans.filter(end_date__isnull=True).aggregate(
            total=models.Sum('loan_amount')
        )['total'] or 0

    def get_current_emis_total(self):
        """
        Get total monthly EMIs for current active loans.
        
        Returns:
            Decimal: Sum of all active loan EMIs (0 if no active loans)
        """
        return self.loans.filter(end_date__isnull=True).aggregate(
            total=models.Sum('monthly_repayment')
        )['total'] or 0


class Loan(models.Model):
    """
    Loan model representing individual loan applications and their status.
    
    Stores loan details including amount, terms, payment history, and status.
    Provides methods for calculating EMIs, tracking payments, and determining
    loan activity scores for credit assessment.
    
    Attributes:
        loan_id: Auto-generated unique identifier
        customer: Foreign key to Customer model
        loan_amount: Principal loan amount
        tenure: Loan duration in months (1-120)
        interest_rate: Annual interest rate percentage
        monthly_repayment: Calculated monthly EMI
        emis_paid_on_time: Number of EMIs paid on time
        start_date: Loan start date
        end_date: Loan end date (null if active)
        status: Loan status (active/completed/defaulted)
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    LOAN_STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
    ]

    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loans')
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tenure = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])  # 1-120 months
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 12.50%
    monthly_repayment = models.DecimalField(max_digits=12, decimal_places=2)
    emis_paid_on_time = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=LOAN_STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loans'

    def __str__(self):
        """
        String representation of the loan.
        
        Returns:
            str: Loan ID and customer name
        """
        return f"Loan {self.loan_id} - {self.customer.name}"

    def calculate_monthly_repayment(self):
        """
        Calculate monthly EMI using compound interest formula.
        
        Uses the standard EMI formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
        where P = principal, r = monthly interest rate, n = tenure in months
        
        Returns:
            float: Calculated monthly EMI rounded to 2 decimal places
        """
        if self.tenure <= 0 or self.interest_rate <= 0:
            return 0
        
        # Convert annual interest rate to monthly
        monthly_rate = float(self.interest_rate) / 100 / 12
        
        # EMI formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
        principal = float(self.loan_amount)
        n = self.tenure
        
        if monthly_rate == 0:
            return principal / n
        
        emi = principal * monthly_rate * (1 + monthly_rate)**n / ((1 + monthly_rate)**n - 1)
        return round(emi, 2)

    def get_repayments_left(self):
        """
        Calculate remaining EMIs for the loan.
        
        Returns:
            int: Number of remaining EMIs (0 if loan is completed)
        """
        if self.end_date:
            return 0
        return self.tenure - self.emis_paid_on_time

    def is_loan_paid_on_time(self):
        """
        Check if loan was paid on time (all EMIs paid).
        
        Returns:
            bool: True if all EMIs have been paid, False otherwise
        """
        return self.emis_paid_on_time >= self.tenure

    def get_loan_activity_score(self):
        """
        Get loan activity score based on payment history.
        
        Calculates percentage of EMIs paid on time relative to total tenure.
        
        Returns:
            float: Activity score as percentage (0-100)
        """
        if self.tenure == 0:
            return 0
        return (self.emis_paid_on_time / self.tenure) * 100

    @staticmethod
    def calculate_monthly_emi(loan_amount, interest_rate, tenure):
        """
        Calculate monthly EMI using compound interest formula (static method).
        
        Static version of calculate_monthly_repayment for use without instance.
        Uses the standard EMI formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
        
        Args:
            loan_amount: Principal loan amount
            interest_rate: Annual interest rate percentage
            tenure: Loan duration in months
            
        Returns:
            float: Calculated monthly EMI rounded to 2 decimal places
        """
        if tenure <= 0 or interest_rate <= 0:
            return 0
        
        # Convert annual interest rate to monthly
        monthly_rate = float(interest_rate) / 100 / 12
        
        # EMI formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
        principal = float(loan_amount)
        n = tenure
        
        if monthly_rate == 0:
            return principal / n
        
        emi = principal * monthly_rate * (1 + monthly_rate)**n / ((1 + monthly_rate)**n - 1)
        return round(emi, 2) 