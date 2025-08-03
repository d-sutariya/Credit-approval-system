from rest_framework import serializers
from .models import Customer, Loan
from decimal import Decimal


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer model.
    
    Handles serialization and deserialization of Customer objects for API operations.
    Includes validation for phone number, age, and monthly income.
    
    Fields:
        customer_id: Auto-generated unique identifier (read-only)
        first_name: Customer's first name
        last_name: Customer's last name
        name: Computed full name (read-only)
        age: Customer's age (18-100)
        monthly_income: Monthly salary/income
        phone_number: Contact phone number (min 10 digits)
        approved_limit: Calculated credit limit (read-only)
    """
    name = serializers.CharField(read_only=True)
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        model = Customer
        fields = [
            'customer_id', 'first_name', 'last_name', 'name', 'age', 
            'monthly_income', 'phone_number', 'approved_limit'
        ]
        read_only_fields = ['customer_id', 'approved_limit']

    def validate_phone_number(self, value):
        """
        Validate phone number format.
        
        Args:
            value: Phone number to validate
            
        Returns:
            str: Validated phone number
            
        Raises:
            ValidationError: If phone number is less than 10 digits
        """
        if len(str(value)) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value

    def validate_age(self, value):
        """
        Validate age range.
        
        Args:
            value: Age to validate
            
        Returns:
            int: Validated age
            
        Raises:
            ValidationError: If age is not between 18 and 100
        """
        if value < 18 or value > 100:
            raise serializers.ValidationError("Age must be between 18 and 100")
        return value

    def validate_monthly_income(self, value):
        """
        Validate monthly income.
        
        Args:
            value: Monthly income to validate
            
        Returns:
            Decimal: Validated monthly income
            
        Raises:
            ValidationError: If monthly income is not positive
        """
        if value <= 0:
            raise serializers.ValidationError("Monthly income must be greater than 0")
        return value


class LoanSerializer(serializers.ModelSerializer):
    """
    Serializer for Loan model.
    
    Handles serialization and deserialization of Loan objects for general operations.
    Includes validation for loan amount, interest rate, and tenure.
    
    Fields:
        loan_id: Auto-generated unique identifier (read-only)
        customer_id: Customer ID for loan creation (write-only)
        customer: Full customer details (read-only)
        loan_amount: Requested loan amount
        interest_rate: Annual interest rate (0-100%)
        tenure: Loan duration in months (1-120)
        monthly_repayment: Calculated EMI (read-only)
        repayments_left: Remaining EMIs (read-only)
        start_date: Loan start date (read-only)
        end_date: Loan end date (read-only)
        status: Loan status (read-only)
    """
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
        """
        Validate loan amount.
        
        Args:
            value: Loan amount to validate
            
        Returns:
            Decimal: Validated loan amount
            
        Raises:
            ValidationError: If loan amount is not positive
        """
        if value <= 0:
            raise serializers.ValidationError("Loan amount must be greater than 0")
        return value

    def validate_interest_rate(self, value):
        """
        Validate interest rate.
        
        Args:
            value: Interest rate to validate
            
        Returns:
            Decimal: Validated interest rate
            
        Raises:
            ValidationError: If interest rate is not between 0 and 100
        """
        if value <= 0 or value > 100:
            raise serializers.ValidationError("Interest rate must be between 0 and 100")
        return value

    def validate_tenure(self, value):
        """
        Validate tenure.
        
        Args:
            value: Tenure to validate
            
        Returns:
            int: Validated tenure
            
        Raises:
            ValidationError: If tenure is not between 1 and 120 months
        """
        if value < 1 or value > 120:
            raise serializers.ValidationError("Tenure must be between 1 and 120 months")
        return value


class LoanEligibilitySerializer(serializers.Serializer):
    """
    Serializer for loan eligibility check requests.
    
    Used for the /check-eligibility endpoint to validate loan eligibility
    based on customer credit score and loan parameters.
    
    Fields:
        customer_id: Customer ID to check eligibility for
        loan_amount: Requested loan amount
        interest_rate: Proposed interest rate
        tenure: Loan duration in months
    """
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()

    def validate_customer_id(self, value):
        """
        Validate customer exists.
        
        Args:
            value: Customer ID to validate
            
        Returns:
            int: Validated customer ID
            
        Raises:
            ValidationError: If customer does not exist
        """
        try:
            Customer.objects.get(customer_id=value)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Customer not found")
        return value


class LoanCreateSerializer(serializers.Serializer):
    """
    Serializer for loan creation requests.
    
    Used for the /create-loan endpoint to validate and process new loan applications.
    
    Fields:
        customer_id: Customer ID applying for loan
        loan_amount: Requested loan amount
        interest_rate: Proposed interest rate
        tenure: Loan duration in months
    """
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()

    def validate_customer_id(self, value):
        """
        Validate customer exists.
        
        Args:
            value: Customer ID to validate
            
        Returns:
            int: Validated customer ID
            
        Raises:
            ValidationError: If customer does not exist
        """
        try:
            Customer.objects.get(customer_id=value)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Customer not found")
        return value


class LoanDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed loan view.
    
    Used for the /view-loan/{loan_id} endpoint to return comprehensive
    loan details including customer information.
    
    Fields:
        loan_id: Loan identifier
        customer: Customer details (nested object)
        loan_amount: Loan amount
        interest_rate: Interest rate
        monthly_repayment: Monthly EMI
        tenure: Loan duration
        repayments_left: Remaining EMIs
    """
    customer = serializers.SerializerMethodField()
    repayments_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'loan_id', 'customer', 'loan_amount', 'interest_rate',
            'monthly_repayment', 'tenure', 'repayments_left'
        ]

    def get_customer(self, obj):
        """
        Get customer details for loan.
        
        Args:
            obj: Loan object
            
        Returns:
            dict: Customer details including id, name, phone, and age
        """
        return {
            'id': obj.customer.customer_id,
            'first_name': obj.customer.first_name,
            'last_name': obj.customer.last_name,
            'phone_number': obj.customer.phone_number,
            'age': obj.customer.age
        }


class CustomerLoanListSerializer(serializers.ModelSerializer):
    """
    Serializer for customer loan list view.
    
    Used for the /view-loans/{customer_id} endpoint to return
    a list of all loans for a specific customer.
    
    Fields:
        loan_id: Loan identifier
        loan_amount: Loan amount
        interest_rate: Interest rate
        monthly_repayment: Monthly EMI
        repayments_left: Remaining EMIs
    """
    repayments_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'loan_id', 'loan_amount', 'interest_rate',
            'monthly_repayment', 'repayments_left'
        ] 