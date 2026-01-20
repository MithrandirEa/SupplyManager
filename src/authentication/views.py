from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required


@login_required
def login_view(request):
    form = AuthenticationForm()
    return redirect('home')


@login_required
def logout_view(request):

    return redirect('login')


@login_required
def create_user(request):
    from .forms import CustomUserCreationForm

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.created_by = request.user
            new_user.save()
            return redirect('staff_management')
    else:
        form = CustomUserCreationForm()

    return render(request, 'create_user.html', {'form': form})


@login_required
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


@login_required
def delete_user(request, user_id):
    from .models import User

    user = User.objects.get(id=user_id)
    user.delete()
    return redirect('staff_management')