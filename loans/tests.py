from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Customer, Loan
from .services import CreditScoreService, LoanService


class CustomerModelTest(TestCase):
    def setUp(self):
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
        self.assertEqual(self.customer.name, "John Doe")
        self.assertEqual(self.customer.monthly_income, Decimal('50000'))

    def test_approved_limit_calculation(self):
        limit = Customer.calculate_approved_limit(Decimal('50000'))
        self.assertEqual(limit, 1800000)  # 36 * 50000 = 1800000


class LoanModelTest(TestCase):
    def setUp(self):
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
        self.assertEqual(self.loan.customer, self.customer)
        self.assertEqual(self.loan.get_repayments_left(), 12)

    def test_monthly_emi_calculation(self):
        emi = Loan.calculate_monthly_emi(
            Decimal('500000'), 
            Decimal('12.5'), 
            24
        )
        self.assertGreater(emi, 0)


class CreditScoreServiceTest(TestCase):
    def setUp(self):
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
        score = CreditScoreService.calculate_credit_score(self.customer)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_loan_eligibility_check(self):
        approval, corrected_rate, monthly_emi = CreditScoreService.check_loan_eligibility(
            self.customer,
            Decimal('500000'),
            Decimal('12.5'),
            24
        )
        self.assertIsInstance(approval, bool)
        self.assertGreaterEqual(corrected_rate, 0)


class APITest(TestCase):
    def setUp(self):
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
        url = reverse('view_customer_loans', kwargs={'customer_id': self.customer.customer_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list) 