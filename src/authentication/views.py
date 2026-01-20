from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm


def login_view(request):
    form = AuthenticationForm()
    return redirect('home')


def logout_view(request):
    
    return redirect('login')

def create_user(request):
    from .forms import CustomUserCreationForm

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('staff_management')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'create_user.html', {'form': form})


def change_user(request, user_id):
    from .forms import CustomUserChangeForm
    from .models import User

    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('staff_management')
    else:
        form = CustomUserChangeForm(instance=user)
    
    return render(request, 'change_user.html', {'form': form, 'user_id': user_id})


def delete_user(request, user_id):
    from .models import User

    user = User.objects.get(id=user_id)
    user.delete()
    return redirect('staff_management')