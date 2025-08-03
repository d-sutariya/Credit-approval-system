from django.contrib import admin
from .models import Customer, Loan


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'first_name', 'last_name', 'age', 'phone_number', 'monthly_salary', 'approved_limit', 'current_debt']
    list_filter = ['age', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number']
    readonly_fields = ['customer_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer_id', 'first_name', 'last_name', 'age', 'phone_number')
        }),
        ('Financial Information', {
            'fields': ('monthly_salary', 'approved_limit', 'current_debt')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['loan_id', 'customer', 'loan_amount', 'interest_rate', 'tenure', 'monthly_repayment', 'status', 'start_date']
    list_filter = ['status', 'start_date', 'interest_rate', 'tenure']
    search_fields = ['loan_id', 'customer__first_name', 'customer__last_name']
    readonly_fields = ['loan_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Loan Information', {
            'fields': ('loan_id', 'customer', 'loan_amount', 'interest_rate', 'tenure')
        }),
        ('Payment Information', {
            'fields': ('monthly_repayment', 'emis_paid_on_time', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 