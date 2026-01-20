from django.shortcuts import render
from authentication.models import User


def home(request):
    return render(request, 'home.html')


def staff_management(request):
    users = User.objects.all().order_by('role', 'username')
    return render(request, 'staff_management.html', {'users': users})


def supplies_management(request):
    return render(request, 'supplies_management.html')


def suppliers_management(request):
    return render(request, 'suppliers_management.html')



