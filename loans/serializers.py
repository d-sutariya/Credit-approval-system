from rest_framework import serializers
from .models import Customer, Loan
from decimal import Decimal


class CustomerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    monthly_income = serializers.DecimalField(source='monthly_salary', max_digits=12, decimal_places=2)

    class Meta:
        model = Customer
        fields = [
            'customer_id', 'first_name', 'last_name', 'age', 
            'monthly_income', 'phone_number', 'approved_limit'
        ]
        read_only_fields = ['customer_id', 'approved_limit']

    def validate_phone_number(self, value):
        """Validate phone number format"""
        if len(str(value)) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value

    def validate_age(self, value):
        """Validate age range"""
        if value < 18 or value > 100:
            raise serializers.ValidationError("Age must be between 18 and 100")
        return value

    def validate_monthly_income(self, value):
        """Validate monthly income"""
        if value <= 0:
            raise serializers.ValidationError("Monthly income must be greater than 0")
        return value


class LoanSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(write_only=True)
    customer = CustomerSerializer(read_only=True)
    repayments_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'loan_id', 'customer_id', 'customer', 'loan_amount', 
            'interest_rate', 'tenure', 'monthly_repayment', 
            'repayments_left', 'start_date', 'end_date', 'status'
        ]
        read_only_fields = ['loan_id', 'monthly_repayment', 'repayments_left', 'start_date', 'end_date', 'status']

    def validate_loan_amount(self, value):
        """Validate loan amount"""
        if value <= 0:
            raise serializers.ValidationError("Loan amount must be greater than 0")
        return value

    def validate_interest_rate(self, value):
        """Validate interest rate"""
        if value <= 0 or value > 100:
            raise serializers.ValidationError("Interest rate must be between 0 and 100")
        return value

    def validate_tenure(self, value):
        """Validate tenure"""
        if value < 1 or value > 120:
            raise serializers.ValidationError("Tenure must be between 1 and 120 months")
        return value


class LoanEligibilitySerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()

    def validate_customer_id(self, value):
        """Validate customer exists"""
        try:
            Customer.objects.get(customer_id=value)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Customer not found")
        return value


class LoanCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()

    def validate_customer_id(self, value):
        """Validate customer exists"""
        try:
            Customer.objects.get(customer_id=value)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Customer not found")
        return value


class LoanDetailSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    repayments_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'loan_id', 'customer', 'loan_amount', 'interest_rate',
            'monthly_repayment', 'tenure', 'repayments_left'
        ]

    def get_customer(self, obj):
        return {
            'id': obj.customer.customer_id,
            'first_name': obj.customer.first_name,
            'last_name': obj.customer.last_name,
            'phone_number': obj.customer.phone_number,
            'age': obj.customer.age
        }


class CustomerLoanListSerializer(serializers.ModelSerializer):
    repayments_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'loan_id', 'loan_amount', 'interest_rate',
            'monthly_repayment', 'repayments_left'
        ] 