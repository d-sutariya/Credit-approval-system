from decimal import Decimal
from datetime import datetime, date
from django.db.models import Sum, Count, Q, F
from .models import Customer, Loan


class CreditScoreService:
    """Service for calculating credit scores and loan eligibility"""
    
    @staticmethod
    def calculate_credit_score(customer):
        """
        Calculate credit score (0-100) based on:
        1. Past loans paid on time
        2. Number of loans taken in past
        3. Loan activity in current year
        4. Loan approved volume
        5. Current debt vs approved limit
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
        Check loan eligibility based on credit score and business rules
        Returns: (approval, corrected_interest_rate, monthly_installment)
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


class LoanService:
    """Service for loan operations"""
    
    @staticmethod
    def create_loan(customer, loan_amount, interest_rate, tenure):
        """Create a new loan if eligible"""
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
        """Get detailed loan information"""
        try:
            return Loan.objects.get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return None
    
    @staticmethod
    def get_customer_loans(customer_id):
        """Get all loans for a customer"""
        try:
            customer = Customer.objects.get(customer_id=customer_id)
            return customer.loans.all()
        except Customer.DoesNotExist:
            return [] 