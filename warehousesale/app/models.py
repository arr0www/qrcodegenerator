from django.db import models
from django.utils import timezone
import random

class Relative(models.Model):
    entry_id = models.AutoField(primary_key=True)
    r_fname = models.CharField(max_length=50, blank=False, null=False)
    r_lname = models.CharField(max_length=50, blank=False, null=False)
    r_department = models.CharField(max_length=50, choices=[
        ('', 'Select'),
        ('MIS','MIS'),
        ('OPERATIONS','OPERATIONS'),
        ('FINANCE','FINANCE'),
        ('HR','HR'),
        ('MERCH','MERCH'),
        ('SALES','SALES'),
        ('MARKETING','MARKETING'),
    ],blank=False, null=False)

    def __str__(self):
        return f"{self.r_fname} {self.r_lname} - {self.r_department}"
    
    class Meta:
        unique_together = ('r_fname', 'r_lname')


class UserEntry(models.Model):
    entry_id = models.AutoField(primary_key=True)
    fname = models.CharField(max_length=50)
    lname = models.CharField(max_length=50)
    arrival_date = models.DateTimeField()
    relative = models.ForeignKey(
        'Relative', on_delete=models.CASCADE, related_name='user_entries'
    )  # ForeignKey to Relative table
    relationship = models.CharField(
        max_length=50, choices=[
            ('', 'Select'),  # Default empty value with --Select--
            ('Grandparent', 'Grandparent'),
            ('Parent', 'Parent'),
            ('Aunt', 'Aunt'),
            ('Uncle', 'Uncle'),
            ('Sibling', 'Sibling'),
            ('Cousin', 'Cousin'),
            ('Spouse', 'Spouse'),
            ('Partner', 'Partner'),
        ], blank=False, null=False
    )  # Dropdown for relationships
    voucher_id = models.CharField(max_length=9, unique=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.voucher_id:
            self.voucher_id = self.generate_unique_voucher_id()
        super().save(*args, **kwargs)

    def generate_unique_voucher_id(self):
        """Generates a unique voucher ID with the format BE-XXXXXX"""
        while True:
            voucher_id = f"BE-00{random.randint(0000, 9999)}"  # Changed to ensure 6-digit format
            if not UserEntry.objects.filter(voucher_id=voucher_id).exists():
                return voucher_id

    def __str__(self):
        return f"{self.fname} {self.lname}"

    class Meta:
        ordering = ['-updated']

class QRCode(models.Model):
    entry_id = models.ForeignKey(UserEntry, on_delete=models.CASCADE, related_name='qrcodes')  # ForeignKey to UserEntry table
    qr_code = models.TextField()  # Store QR code in base64 format
    status = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    status_updated = models.DateTimeField(null=True, blank=True)  # New field to track status change time

    def save(self, *args, **kwargs):
        # Check if status has changed
        if self.pk:
            original = QRCode.objects.get(pk=self.pk)
            if original.status != self.status:
                self.status_updated = timezone.now()  # Update timestamp only if status has changed
        else:
            self.status_updated = timezone.now()  # Set initial timestamp when first saving

        super().save(*args, **kwargs)

    def __str__(self):
        return f"QRCode for {self.entry_id}"

    class Meta:
        ordering = ['-created', 'status']