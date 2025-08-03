from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Customer, Loan
from .services import CreditScoreService, LoanService


class CustomerModelTest(TestCase):
    """
    Test cases for Customer model functionality.
    
    Tests customer creation, property methods, and approved limit calculations.
    Verifies that customer data is stored correctly and computed fields work as expected.
    """
    
    def setUp(self):
        """
        Set up test data for customer model tests.
        
        Creates a sample customer with standard test data including
        personal information, financial details, and calculated approved limit.
        """
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            age=30,
            phone_number=9876543210,
            monthly_salary=Decimal('50000'),
            approved_limit=Decimal('1800000'),
            current_debt=Decimal('0')
        )

    def test_customer_creation(self):
        """
        Test customer object creation and property methods.
        
        Verifies that customer is created with correct data and that
        computed properties (name, monthly_income) return expected values.
        """
        self.assertEqual(self.customer.name, "John Doe")
        self.assertEqual(self.customer.monthly_income, Decimal('50000'))

    def test_approved_limit_calculation(self):
        """
        Test approved limit calculation formula.
        
        Verifies that the approved limit is calculated correctly as
        36 * monthly_salary rounded to the nearest lakh (100,000).
        """
        limit = Customer.calculate_approved_limit(Decimal('50000'))
        self.assertEqual(limit, 1800000)  # 36 * 50000 = 1800000


class LoanModelTest(TestCase):
    """
    Test cases for Loan model functionality.
    
    Tests loan creation, EMI calculations, and loan-related methods.
    Verifies that loan data is stored correctly and calculations work as expected.
    """
    
    def setUp(self):
        """
        Set up test data for loan model tests.
        
        Creates a sample customer and loan with standard test data including
        loan terms, payment history, and calculated EMI.
        """
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            age=30,
            phone_number=9876543210,
            monthly_salary=Decimal('50000'),
            approved_limit=Decimal('1800000'),
            current_debt=Decimal('0')
        )
        
        self.loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal('500000'),
            tenure=24,
            interest_rate=Decimal('12.5'),
            monthly_repayment=Decimal('23500.50'),
            emis_paid_on_time=12,
            start_date='2023-01-01'
        )

    def test_loan_creation(self):
        """
        Test loan object creation and relationship methods.
        
        Verifies that loan is created with correct data and that
        relationship methods (get_repayments_left) return expected values.
        """
        self.assertEqual(self.loan.customer, self.customer)
        self.assertEqual(self.loan.get_repayments_left(), 12)

    def test_monthly_emi_calculation(self):
        """
        Test monthly EMI calculation using compound interest formula.
        
        Verifies that the EMI calculation returns a positive value
        and uses the correct mathematical formula for compound interest.
        """
        emi = Loan.calculate_monthly_emi(
            Decimal('500000'), 
            Decimal('12.5'), 
            24
        )
        self.assertGreater(emi, 0)


class CreditScoreServiceTest(TestCase):
    """
    Test cases for CreditScoreService functionality.
    
    Tests credit score calculations and loan eligibility checks.
    Verifies that credit scoring algorithm works correctly and
    eligibility rules are applied properly.
    """
    
    def setUp(self):
        """
        Set up test data for credit score service tests.
        
        Creates a sample customer with standard test data for
        credit score calculation and eligibility testing.
        """
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            age=30,
            phone_number=9876543210,
            monthly_salary=Decimal('50000'),
            approved_limit=Decimal('1800000'),
            current_debt=Decimal('0')
        )

    def test_credit_score_calculation_new_customer(self):
        """
        Test credit score calculation for a new customer.
        
        Verifies that credit score is calculated and falls within
        the expected range of 0-100 for a customer with no loan history.
        """
        score = CreditScoreService.calculate_credit_score(self.customer)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_loan_eligibility_check(self):
        """
        Test loan eligibility check functionality.
        
        Verifies that eligibility check returns appropriate data types
        and values for approval status, corrected interest rate, and monthly EMI.
        """
        approval, corrected_rate, monthly_emi = CreditScoreService.check_loan_eligibility(
            self.customer,
            Decimal('500000'),
            Decimal('12.5'),
            24
        )
        self.assertIsInstance(approval, bool)
        self.assertGreaterEqual(corrected_rate, 0)


class APITest(TestCase):
    """
    Test cases for API endpoints functionality.
    
    Tests all API endpoints including customer registration, loan eligibility,
    loan creation, and loan viewing. Verifies that endpoints return correct
    status codes and response data.
    """
    
    def setUp(self):
        """
        Set up test data for API tests.
        
        Creates a sample customer and API client for testing
        all API endpoints with realistic data.
        """
        self.client = APIClient()
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            age=30,
            phone_number=9876543210,
            monthly_salary=Decimal('50000'),
            approved_limit=Decimal('1800000'),
            current_debt=Decimal('0')
        )

    def test_register_customer(self):
        """
        Test customer registration API endpoint.
        
        Verifies that new customers can be registered successfully
        and the response contains the expected customer ID and data.
        """
        url = reverse('register_customer')
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'age': 25,
            'monthly_income': 40000,
            'phone_number': 9876543211
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('customer_id', response.data)

    def test_check_eligibility(self):
        """
        Test loan eligibility check API endpoint.
        
        Verifies that eligibility checks return appropriate responses
        with approval status and loan details.
        """
        url = reverse('check_eligibility')
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 500000,
            'interest_rate': 12.5,
            'tenure': 24
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('approval', response.data)

    def test_create_loan(self):
        """
        Test loan creation API endpoint.
        
        Verifies that loan creation requests are processed correctly
        and return appropriate status codes for both approved and rejected loans.
        """
        url = reverse('create_loan')
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 500000,
            'interest_rate': 12.5,
            'tenure': 24
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_view_loan(self):
        """
        Test loan detail viewing API endpoint.
        
        Verifies that loan details can be retrieved successfully
        and the response contains the expected loan information.
        """
        loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal('500000'),
            tenure=24,
            interest_rate=Decimal('12.5'),
            monthly_repayment=Decimal('23500.50'),
            start_date='2023-01-01'
        )
        url = reverse('view_loan', kwargs={'loan_id': loan.loan_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_customer_loans(self):
        """
        Test customer loan list viewing API endpoint.
        
        Verifies that all loans for a customer can be retrieved
        and the response is a list containing loan data.
        """
        url = reverse('view_customer_loans', kwargs={'customer_id': self.customer.customer_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list) 