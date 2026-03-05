from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.urls import reverse

from authentication.decorators import role_required
from supplier.models import Supplier
from supply.models import Item

from .forms import (ChangeItemForm, CreateCategoryForm, CreateItemForm,
                    ImportItemsForm)


@role_required(['ADMIN', 'DIRECTOR'])
def create_category(request):
    if request.method == 'POST':
        form = CreateCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('supplies_management')}#items")
    else:
        form = CreateCategoryForm()

    return render(request, 'create_category.html', {'form': form})


@role_required(['ADMIN', 'DIRECTOR'])
def create_item(request):
    if request.method == 'POST':
        form = CreateItemForm(request.POST)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.available_quantity = (
                new_item.total_quantity - new_item.outside_quantity
            )
            new_item.created_by = request.user
            new_item.save()

            # Récupérer les fournisseurs sélectionnés depuis les inputs hidden
            selected_suppliers = request.POST.getlist('suppliers')
            if selected_suppliers:
                new_item.suppliers.set(selected_suppliers)

            return redirect(f"{reverse('supplies_management')}#items")
    else:
        form = CreateItemForm()

    all_suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'create_item.html', {
        'form': form,
        'all_suppliers': all_suppliers,
        'selected_supplier_ids': []
    })


@role_required(['ADMIN', 'DIRECTOR'])
def change_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        form = ChangeItemForm(request.POST, instance=item)
        if form.is_valid():
            change_item = form.save(commit=False)
            change_item.available_quantity = (
                change_item.total_quantity - change_item.outside_quantity
            )
            change_item.save()

            # Récupérer les fournisseurs sélectionnés depuis les inputs hidden
            selected_suppliers = request.POST.getlist('suppliers')
            change_item.suppliers.set(selected_suppliers)

            return redirect(f"{reverse('supplies_management')}#items")
    else:
        form = ChangeItemForm(instance=item)

    all_suppliers = Supplier.objects.all().order_by('name')
    selected_supplier_ids = list(item.suppliers.values_list('id', flat=True))

    return render(request, 'change_item.html', {
        'form': form,
        'item': item,
        'all_suppliers': all_suppliers,
        'selected_supplier_ids': selected_supplier_ids
    })


@require_POST
@role_required(['ADMIN', 'DIRECTOR'])
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    item.delete()
    return redirect(f"{reverse('supplies_management')}#items")


@role_required(['ADMIN', 'DIRECTOR'])
def import_items(request):
    """
    Vue pour importer des articles depuis un fichier CSV ou Excel.
    """
    if request.method == 'POST':
        form = ImportItemsForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                from .services import process_import

                import_file = request.FILES['import_file']
                update_existing = form.cleaned_data['update_existing']

                created_count, updated_count, errors = process_import(
                    import_file, update_existing, request.user
                )

                if errors:
                    msg = (
                        f"Import terminé avec {len(errors)} erreurs. "
                        f"(Succès : {created_count} créés, {updated_count} maj)"
                    )
                    messages.warning(request, msg)
                else:
                    msg = (
                        f"Import terminé avec succès ! "
                        f"({created_count} créés, {updated_count} mis à jour)"
                    )
                    messages.success(request, msg)

                return redirect(f"{reverse('supplies_management')}#items")

            except Exception as e:
                messages.error(
                    request, f"Erreur critique lors de l'import : {e}")
                return redirect(f"{reverse('supplies_management')}#items")
    else:
        form = ImportItemsForm()

    return render(request, 'import_items.html', {'form': form})
