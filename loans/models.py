from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import math


class Customer(models.Model):
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
        return f"{self.first_name} {self.last_name} (ID: {self.customer_id})"

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def monthly_income(self):
        return self.monthly_salary

    @staticmethod
    def calculate_approved_limit(monthly_salary):
        """Calculate approved limit as 36 * monthly_salary rounded to nearest lakh"""
        limit = float(monthly_salary) * 36
        # Round to nearest lakh (100000)
        return round(limit / 100000) * 100000

    def get_current_loans_total(self):
        """Get total amount of current active loans"""
        return self.loans.filter(end_date__isnull=True).aggregate(
            total=models.Sum('loan_amount')
        )['total'] or 0

    def get_current_emis_total(self):
        """Get total monthly EMIs for current loans"""
        return self.loans.filter(end_date__isnull=True).aggregate(
            total=models.Sum('monthly_repayment')
        )['total'] or 0


class Loan(models.Model):
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
        return f"Loan {self.loan_id} - {self.customer.name}"

    def calculate_monthly_repayment(self):
        """Calculate monthly EMI using compound interest formula"""
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
        """Calculate remaining EMIs"""
        if self.end_date:
            return 0
        return self.tenure - self.emis_paid_on_time

    def is_loan_paid_on_time(self):
        """Check if loan was paid on time (all EMIs paid)"""
        return self.emis_paid_on_time >= self.tenure

    def get_loan_activity_score(self):
        """Get loan activity score based on payment history"""
        if self.tenure == 0:
            return 0
        return (self.emis_paid_on_time / self.tenure) * 100

    @staticmethod
    def calculate_monthly_emi(loan_amount, interest_rate, tenure):
        """Calculate monthly EMI using compound interest formula"""
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