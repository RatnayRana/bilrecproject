from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model


# Create your models here.
class User(AbstractUser):
    employee_id = models.CharField(max_length=200, unique=True)
    cid = models.BigIntegerField(unique=True)
    status = models.CharField(max_length=150, default='Inactive')
    user_created = models.DateTimeField(auto_now_add=True)

class System(models.Model):
    name=models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Bank(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class BankAccount(models.Model):
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='accounts')
    system_name = models.ForeignKey(System,on_delete=models.CASCADE)
    account_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.account_number


    

class BankStatement(models.Model):
    date = models.DateField(null=True)
    journal_number = models.CharField(max_length=500, null=True)
    rr_number = models.CharField(max_length=1000, null=True,blank=True)       # Use CharField for large numbers or strings
    instrument_number = models.CharField(max_length=400, null=True,blank=True)  # Use CharField for numbers
    reference_no = models.CharField(max_length=400, null=True,blank=True) 
    transaction_type=models.CharField(max_length=60,null=True,blank=True)  # Use CharField for large numbers or strings
    debit = models.DecimalField(max_digits= 20, decimal_places=2, null=True, blank=True)
    credit = models.DecimalField(max_digits= 20, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits= 20, decimal_places=2, null=True,blank=True)
    bank_name = models.ForeignKey(Bank,on_delete=models.CASCADE)
    bank_account_number= models.CharField(max_length=40, null=True,blank=True)
    status = models.CharField(max_length=50, default='Pending')
    system_name = models.ForeignKey(System,on_delete=models.CASCADE)
    bankstatement_uploaded =models.DateTimeField(auto_now_add=True)
    useruploaded = models.ForeignKey(get_user_model(),on_delete=models.CASCADE, null=True, blank=True)
    class Meta:
        unique_together = ('date', 'journal_number')

    def __str__(self):
        return f"{self.date} - {self.journal_number} - {self.reference_no}"
    

class DailyReportBankStatement(models.Model):
    tran_date = models.DateField(null=True)
    voucher_no = models.CharField(max_length=240,null=True)
    # customer_name = models.CharField(max_length=500, null=True)
    # ref_number = models.CharField(max_length=500, null=True)
    # tran_mode = models.CharField(max_length=100, null=True)
    instrument_number = models.CharField(max_length=200, null=True)
    instrument_date = models.DateField(null=True)
    # bank_name= models.CharField(max_length=30,null=True)
    credit_amount = models.DecimalField(max_digits= 20, decimal_places=2, null=True, blank=True)
    debit_amount = models.DecimalField(max_digits= 20, decimal_places=2, null=True, blank=True)
    system_name = models.ForeignKey(System,on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default='Pending')
    bank_account_number= models.CharField(max_length=40, null=True,blank=True)
    daily_uploaded = models.DateTimeField(auto_now_add=True)

    useruploaded = models.ForeignKey(get_user_model(),on_delete=models.CASCADE, null=True, blank=True)






