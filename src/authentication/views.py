from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import role_required


@login_required
def login_view(request):
    return redirect('dashboard')


@login_required
def logout_view(request):

    return redirect('login')


@role_required(['ADMIN', 'DIRECTOR'])
def create_user(request):
    from django.contrib import messages

    from .forms import CustomUserCreationForm

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, current_user=request.user)
        if form.is_valid():
            new_user = form.save(commit=False)

            # Vérifier si on essaie de créer un Admin
            # alors qu'on n'est pas Admin
            if new_user.role == 'ADMIN' and request.user.role != 'ADMIN':
                messages.error(
                    request,
                    "Seul un administrateur peut créer un autre "
                    "administrateur."
                )
                return redirect('staff_management')

            new_user.created_by = request.user
            new_user.save()
            return redirect('staff_management')
    else:
        form = CustomUserCreationForm(current_user=request.user)

    return render(request, 'create_user.html', {'form': form})


@role_required(['ADMIN', 'DIRECTOR'])
def change_user(request, user_id):
    from django.contrib import messages

    from .forms import CustomUserChangeForm
    from .models import User

    user = User.objects.get(id=user_id)

    # Vérifier si l'utilisateur cible est un Admin et si
    # l'utilisateur connecté n'est pas Admin
    if user.role == 'ADMIN' and request.user.role != 'ADMIN':
        messages.error(
            request,
            "Seul un administrateur peut modifier un autre "
            "administrateur."
        )
        return redirect('staff_management')

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"L'utilisateur {user.username} a été modifié avec succès."
            )
            return redirect('staff_management')
        else:
            messages.error(
                request,
                "Erreur lors de la modification. "
                "Veuillez vérifier les champs du formulaire."
            )
    else:
        form = CustomUserChangeForm(instance=user)

    return render(
        request,
        'change_user.html',
        {'form': form, 'user_id': user_id}
    )


@role_required(['ADMIN', 'DIRECTOR'])
def delete_user(request, user_id):
    from django.contrib import messages

    from .models import User

    user = User.objects.get(id=user_id)

    # Empêcher un utilisateur de se supprimer lui-même
    if user.id == request.user.id:
        messages.error(
            request,
            "Vous ne pouvez pas supprimer votre propre compte."
        )
        return redirect('staff_management')

    # Vérifier si l'utilisateur cible est un Admin et si
    # l'utilisateur connecté n'est pas Admin
    if user.role == 'ADMIN' and request.user.role != 'ADMIN':
        messages.error(
            request,
            "Seul un administrateur peut supprimer un autre "
            "administrateur."
        )
        return redirect('staff_management')

    user.delete()
    return redirect('staff_management')


@login_required
def change_password(request):
    """Permet à l'utilisateur connecté de modifier son mot de passe."""
    from django.contrib import messages
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important pour ne pas déconnecter l'utilisateur
            update_session_auth_hash(request, user)
            messages.success(
                request, 'Votre mot de passe a été mis à jour avec succès!')
            return redirect('staff_management')
        else:
            messages.error(
                request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})
