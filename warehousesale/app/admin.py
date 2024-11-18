from django.contrib import admin
from . models import UserEntry,QRCode,Relative
# Register your models here.

admin.site.register(UserEntry)
admin.site.register(Relative)
admin.site.register(QRCode)