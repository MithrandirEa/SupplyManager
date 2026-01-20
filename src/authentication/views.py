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
    from django.contrib import messages

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, current_user=request.user)
        if form.is_valid():
            new_user = form.save(commit=False)
            
            # Vérifier si on essaie de créer un Admin alors qu'on n'est pas Admin
            if new_user.role == 'ADMIN' and request.user.role != 'ADMIN':
                messages.error(request, "Seul un administrateur peut créer un autre administrateur.")
                return redirect('staff_management')
            
            new_user.created_by = request.user
            new_user.save()
            return redirect('staff_management')
    else:
        form = CustomUserCreationForm(current_user=request.user)

    return render(request, 'create_user.html', {'form': form})


@login_required
def change_user(request, user_id):
    from .forms import CustomUserChangeForm
    from .models import User
    from django.contrib import messages

    user = User.objects.get(id=user_id)
    
    # Vérifier si l'utilisateur cible est un Admin et si l'utilisateur connecté n'est pas Admin
    if user.role == 'ADMIN' and request.user.role != 'ADMIN':
        messages.error(request, "Seul un administrateur peut modifier un autre administrateur.")
        return redirect('staff_management')

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
    from django.contrib import messages

    user = User.objects.get(id=user_id)
    
    # Empêcher un utilisateur de se supprimer lui-même
    if user.id == request.user.id:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('staff_management')
    
    # Vérifier si l'utilisateur cible est un Admin et si l'utilisateur connecté n'est pas Admin
    if user.role == 'ADMIN' and request.user.role != 'ADMIN':
        messages.error(request, "Seul un administrateur peut supprimer un autre administrateur.")
        return redirect('staff_management')
    
    user.delete()
    return redirect('staff_management')