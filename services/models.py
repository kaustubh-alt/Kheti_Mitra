from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import time
from datetime import date
from django.contrib.auth.models import User

from khetimitra import settings

def uniqueval():
    return str(uuid.uuid4().int)[:8]


class Farmer(models.Model):
    LITERACY_CHOICES = [
        ('ILLITERATE', 'Illiterate'),
        ('BASIC', 'Basic Reading'),
        ('FLUENT', 'Fluent'),
    ]
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='farmer_profile' # This is your shortcut
    )
    region = models.CharField(max_length=100, null=True, blank=True)
    govt_farmer_id = models.CharField(max_length=50, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(100)])
    literacy_level = models.CharField(max_length=15, choices=LITERACY_CHOICES)
    income_range = models.BigIntegerField( null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate age: (Today - Birth Date)
        today = date.today()
        calculated_age = today.year - self.dob.year - (
            (today.month, today.day) < (self.dob.month, self.dob.day)
        )
        
        self.age = calculated_age
        super(Farmer, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
    


class Land(models.Model):
    OWNERSHIP_CHOICES = [
        ('OWNER', 'Owner'),
        ('RENTED', 'Rented'),
    ]
    landid = models.IntegerField(auto_created=True,primary_key=True)
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='lands')
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    ownership = models.CharField(max_length=10, choices=OWNERSHIP_CHOICES)
    soil_type = models.CharField(max_length=100)
    nitrogen = models.FloatField(validators=[MinValueValidator(0.1)])
    phosphorus = models.FloatField(max_length=50, null=True, blank=True)
    potassium = models.FloatField(max_length=100, null=True, blank=True)
    crops = models.TextField(null=True, blank=True)  # store past crops
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Land {self.id} - {self.farmer.name}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.landid:
            val = self.farmer.name+"LAND"+uniqueval()+str(int(time.time()))
        else:
            val = self.landid
        return super().save(landid=val, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
    

class Plan(models.Model):
    user = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='plans')
    plan_name = models.CharField(max_length=100)
    details = models.JSONField()
    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name='plans', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        name = self.user.name+"PLAN"+uniqueval()+str(int(time.time()))
        self.plan_name = name
        return super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __str__(self):
        return f"Plan {self.plan_name} for {self.user.name}"
