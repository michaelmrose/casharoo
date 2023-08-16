from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Account(models.Model):
    name = models.CharField(max_length=255)
    balance = models.DecimalField(max_digits=19, decimal_places=2)

    
class Transaction(models.Model):
    title = models.CharField(max_length=50)
    date = models.DateTimeField()
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    category = models.CharField(max_length=100)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
