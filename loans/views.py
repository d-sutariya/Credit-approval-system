from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from decimal import Decimal

from .models import Customer, Loan
from .serializers import (
    CustomerSerializer, LoanEligibilitySerializer, LoanCreateSerializer,
    LoanDetailSerializer, CustomerLoanListSerializer
)
from .services import CreditScoreService, LoanService


@api_view(['POST'])
def register_customer(request):
    """Register a new customer"""
    serializer = CustomerSerializer(data=request.data)
    if serializer.is_valid():
        # Calculate approved limit
        monthly_salary = serializer.validated_data['monthly_income']
        approved_limit = Customer.calculate_approved_limit(monthly_salary)
        
        # Create customer with calculated approved limit
        customer_data = {
            'first_name': serializer.validated_data['first_name'],
            'last_name': serializer.validated_data['last_name'],
            'age': serializer.validated_data['age'],
            'phone_number': serializer.validated_data['phone_number'],
            'monthly_salary': monthly_salary,
            'approved_limit': approved_limit,
        }
        
        customer = Customer.objects.create(**customer_data)
        
        # Return response with calculated fields
        response_data = {
            'customer_id': customer.customer_id,
            'name': customer.name,
            'age': customer.age,
            'monthly_income': customer.monthly_salary,
            'approved_limit': customer.approved_limit,
            'phone_number': customer.phone_number
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_eligibility(request):
    """Check loan eligibility for a customer"""
    serializer = LoanEligibilitySerializer(data=request.data)
    if serializer.is_valid():
        customer_id = serializer.validated_data['customer_id']
        loan_amount = serializer.validated_data['loan_amount']
        interest_rate = serializer.validated_data['interest_rate']
        tenure = serializer.validated_data['tenure']
        
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check eligibility
        approval, corrected_interest_rate, monthly_installment = CreditScoreService.check_loan_eligibility(
            customer, loan_amount, interest_rate, tenure
        )
        
        response_data = {
            'customer_id': customer_id,
            'approval': approval,
            'interest_rate': float(interest_rate),
            'corrected_interest_rate': float(corrected_interest_rate),
            'tenure': tenure,
            'monthly_installment': float(monthly_installment) if monthly_installment else 0
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_loan(request):
    """Create a new loan"""
    serializer = LoanCreateSerializer(data=request.data)
    if serializer.is_valid():
        customer_id = serializer.validated_data['customer_id']
        loan_amount = serializer.validated_data['loan_amount']
        interest_rate = serializer.validated_data['interest_rate']
        tenure = serializer.validated_data['tenure']
        
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create loan
        loan, message = LoanService.create_loan(customer, loan_amount, interest_rate, tenure)
        
        if loan:
            response_data = {
                'loan_id': loan.loan_id,
                'customer_id': customer_id,
                'loan_approved': True,
                'message': message,
                'monthly_installment': float(loan.monthly_repayment)
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            response_data = {
                'loan_id': None,
                'customer_id': customer_id,
                'loan_approved': False,
                'message': message,
                'monthly_installment': 0
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def view_loan(request, loan_id):
    """View loan details"""
    try:
        loan = Loan.objects.get(loan_id=loan_id)
    except Loan.DoesNotExist:
        return Response(
            {'error': 'Loan not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = LoanDetailSerializer(loan)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def view_customer_loans(request, customer_id):
    """View all loans for a customer"""
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    loans = customer.loans.all()
    serializer = CustomerLoanListSerializer(loans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK) 