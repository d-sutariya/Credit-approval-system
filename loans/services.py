from decimal import Decimal
from datetime import datetime, date
from django.db.models import Sum, Count, Q, F
from .models import Customer, Loan


class CreditScoreService:
    """
    Service for calculating credit scores and determining loan eligibility.
    
    Provides methods to calculate credit scores based on customer loan history
    and determine loan approval based on credit score and business rules.
    Implements the credit scoring algorithm as specified in the requirements.
    """
    
    @staticmethod
    def calculate_credit_score(customer):
        """
        Calculate credit score (0-100) based on multiple criteria.
        
        Credit score is calculated using the following components:
        1. Past loans paid on time (40 points)
        2. Number of loans taken in past (20 points)
        3. Loan activity in current year (20 points)
        4. Loan approved volume (20 points)
        5. Current debt vs approved limit (automatic 0 if exceeded)
        
        Args:
            customer: Customer object to calculate credit score for
            
        Returns:
            int: Credit score between 0 and 100
            
        Note:
            Returns 0 immediately if current loans exceed approved limit
        """
        # Check if current loans exceed approved limit
        current_loans_total = customer.get_current_loans_total()
        if current_loans_total > float(customer.approved_limit):
            return 0
        
        # Get all past and current loans
        all_loans = customer.loans.all()
        past_loans = all_loans.filter(end_date__isnull=False)
        current_year = datetime.now().year
        
        # 1. Past loans paid on time (40 points)
        loans_paid_on_time = past_loans.filter(
            emis_paid_on_time__gte=F('tenure')
        ).count()
        total_past_loans = past_loans.count()
        
        if total_past_loans > 0:
            payment_score = (loans_paid_on_time / total_past_loans) * 40
        else:
            payment_score = 20  # Default score for new customers
        
        # 2. Number of loans taken in past (20 points)
        loan_count = all_loans.count()
        if loan_count == 0:
            loan_count_score = 10
        elif loan_count <= 3:
            loan_count_score = 20
        elif loan_count <= 5:
            loan_count_score = 15
        else:
            loan_count_score = 10
        
        # 3. Loan activity in current year (20 points)
        current_year_loans = all_loans.filter(start_date__year=current_year).count()
        if current_year_loans == 0:
            activity_score = 10
        elif current_year_loans == 1:
            activity_score = 20
        else:
            activity_score = 15
        
        # 4. Loan approved volume (20 points)
        total_loan_volume = all_loans.aggregate(
            total=Sum('loan_amount')
        )['total'] or 0
        
        if total_loan_volume == 0:
            volume_score = 10
        elif total_loan_volume <= 1000000:  # 10 lakhs
            volume_score = 15
        elif total_loan_volume <= 5000000:  # 50 lakhs
            volume_score = 20
        else:
            volume_score = 18
        
        # Calculate total credit score
        total_score = payment_score + loan_count_score + activity_score + volume_score
        
        return min(100, max(0, round(total_score)))
    
    @staticmethod
    def check_loan_eligibility(customer, loan_amount, interest_rate, tenure):
        """
        Check loan eligibility based on credit score and business rules.
        
        Evaluates loan eligibility using credit score and applies business rules:
        - Credit score > 50: Approve any loan
        - Credit score 30-50: Approve loans with interest rate > 12%
        - Credit score 10-30: Approve loans with interest rate > 16%
        - Credit score < 10: No loans approved
        - Total EMIs > 50% of monthly salary: No loans approved
        
        Args:
            customer: Customer object applying for loan
            loan_amount: Requested loan amount
            interest_rate: Proposed interest rate
            tenure: Loan duration in months
            
        Returns:
            tuple: (approval, corrected_interest_rate, monthly_installment)
                - approval: Boolean indicating if loan is approved
                - corrected_interest_rate: Interest rate after correction (if needed)
                - monthly_installment: Calculated monthly EMI
        """
        credit_score = CreditScoreService.calculate_credit_score(customer)
        
        # Check if current EMIs exceed 50% of monthly salary
        current_emis_total = customer.get_current_emis_total()
        if current_emis_total > float(customer.monthly_salary) * 0.5:
            return False, interest_rate, 0
        
        # Calculate monthly installment for the new loan
        monthly_installment = CreditScoreService.calculate_monthly_emi(
            loan_amount, interest_rate, tenure
        )
        
        # Check if total EMIs (including new loan) exceed 50% of monthly salary
        total_emis = float(current_emis_total) + float(monthly_installment)
        if total_emis > float(customer.monthly_salary) * 0.5:
            return False, interest_rate, 0
        
        # Determine approval and interest rate based on credit score
        corrected_interest_rate = interest_rate
        
        if credit_score > 50:
            approval = True
        elif credit_score > 30:
            if interest_rate > 12:
                approval = True
            else:
                approval = False
                corrected_interest_rate = 16  # Lowest of the slab
        elif credit_score > 10:
            if interest_rate > 16:
                approval = True
            else:
                approval = False
                corrected_interest_rate = 20  # Lowest of the slab
        else:
            approval = False
        
        return approval, corrected_interest_rate, monthly_installment
    
    @staticmethod
    def calculate_monthly_emi(loan_amount, interest_rate, tenure):
        """
        Calculate monthly EMI using compound interest formula.
        
        Uses the standard EMI formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
        where P = principal, r = monthly interest rate, n = tenure in months
        
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


class LoanService:
    """
    Service for loan operations and management.
    
    Provides methods for creating loans, retrieving loan details,
    and managing loan-related operations. Integrates with CreditScoreService
    for eligibility checks.
    """
    
    @staticmethod
    def create_loan(customer, loan_amount, interest_rate, tenure):
        """
        Create a new loan if the customer is eligible.
        
        Checks loan eligibility using CreditScoreService and creates the loan
        if approved. Sets the loan start date to today and calculates the
        monthly repayment amount.
        
        Args:
            customer: Customer object applying for the loan
            loan_amount: Requested loan amount
            interest_rate: Proposed interest rate
            tenure: Loan duration in months
            
        Returns:
            tuple: (loan, message)
                - loan: Loan object if created, None if not approved
                - message: Success or rejection message
        """
        approval, corrected_interest_rate, monthly_installment = CreditScoreService.check_loan_eligibility(
            customer, loan_amount, interest_rate, tenure
        )
        
        if not approval:
            return None, f"Loan not approved. Credit score criteria not met or interest rate too low."
        
        # Create the loan
        loan = Loan.objects.create(
            customer=customer,
            loan_amount=loan_amount,
            tenure=tenure,
            interest_rate=corrected_interest_rate,
            monthly_repayment=monthly_installment,
            start_date=date.today()
        )
        
        return loan, "Loan approved successfully"
    
    @staticmethod
    def get_loan_details(loan_id):
        """
        Get detailed loan information by loan ID.
        
        Args:
            loan_id: Unique identifier of the loan
            
        Returns:
            Loan: Loan object if found, None if not found
        """
        try:
            return Loan.objects.get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return None
    
    @staticmethod
    def get_customer_loans(customer_id):
        """
        Get all loans for a specific customer.
        
        Args:
            customer_id: Unique identifier of the customer
            
        Returns:
            QuerySet: All loans for the customer, empty list if customer not found
        """
        try:
            customer = Customer.objects.get(customer_id=customer_id)
            return customer.loans.all()
        except Customer.DoesNotExist:
            return [] 