from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CreateItemForm, ChangeItemForm

from supply.models import Item


@login_required
def create_item(request):
    if request.method == 'POST':
        form = CreateItemForm(request.POST)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.available_quantity = new_item.total_quantity - new_item.outside_quantity
            new_item.created_by = request.user
            new_item.save()
            return redirect('supplies_management')
    else:
        form = CreateItemForm()

    return render(request, 'create_item.html', {'form': form})


@login_required
def change_item(request, item_id):
    item = Item.objects.get(id=item_id)
    if request.method == 'POST':
        form = ChangeItemForm(request.POST, instance=item)
        if form.is_valid():
            change_item = form.save(commit=False)
            change_item.available_quantity = change_item.total_quantity - change_item.outside_quantity
            change_item.save()
            return redirect('supplies_management')
    else:
        form = ChangeItemForm(instance=item)
    
    return render(request, 'change_item.html', {'form': form, 'item': item})


@login_required
def delete_item(request, item_id):
    item = Item.objects.get(id=item_id)
    item.delete()
    return redirect('supplies_management')