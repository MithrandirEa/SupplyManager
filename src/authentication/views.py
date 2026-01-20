from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm


def login_view(request):
    form = AuthenticationForm()
    return redirect('home')


def logout_view(request):
    
    return redirect('login')