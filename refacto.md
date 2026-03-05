# PLAN DE REFACTORISATION — SupplyManager

> Ce document identifie les zones du code qui nécessitent une refactorisation, classées par priorité et par module.

---

## 1. Code dupliqué dans les formulaires

### 1.1 `supply/forms.py` — `CreateItemForm` / `ChangeItemForm`

**Problème** : Les deux formulaires sont quasi-identiques (mêmes champs, labels, widgets et méthode `clean()`).

**Fichiers** : `src/supply/forms.py` (lignes 18-108)

**Solution** : Créer une classe de base `BaseItemForm` contenant les champs, labels, widgets et la validation commune, puis en hériter.

```python
# Avant (dupliqué)
class CreateItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'total_quantity', ...]
        labels = { 'name': 'Nom', ... }
        widgets = { ... }
    def clean(self): ...

class ChangeItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'total_quantity', ...]  # identique
        labels = { 'name': 'Nom', ... }                       # identique
        widgets = { ... }                                      # identique
    def clean(self): ...                                       # identique

# Après (factorisé)
class BaseItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'total_quantity',
                  'outside_quantity', 'available_quantity', 'information']
        labels = { ... }
        widgets = { ... }
    def clean(self): ...

class CreateItemForm(BaseItemForm):
    pass

class ChangeItemForm(BaseItemForm):
    pass
```

---

### 1.2 `supplier/forms.py` — `CreateSupplierForm` / `ChangeSupplierForm`

**Problème** : Les deux formulaires sont strictement identiques (mêmes champs, labels, widgets, aucune différence).

**Fichiers** : `src/supplier/forms.py` (lignes 8-63)

**Solution** : Fusionner en un seul formulaire `SupplierForm` ou créer une classe de base commune.

```python
# Après
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'website', 'contact_email', 'phone_number', 'other_details']
        labels = { ... }
        widgets = { ... }

# Alias si nécessaire pour la rétrocompatibilité
CreateSupplierForm = SupplierForm
ChangeSupplierForm = SupplierForm
```

---

### 1.3 `supplier/forms.py` — `QuickOrderForm.clean_items` / `ChangeOrderForm.clean_items`

**Problème** : La méthode `clean_items()` est dupliquée entre les deux formulaires (validation JSON identique des items).

**Fichiers** : `src/supplier/forms.py` (lignes 111-157 et 247-288)

**Solution** : Extraire la logique de validation dans un mixin ou une fonction utilitaire.

```python
# Créer un mixin
class ItemsValidationMixin:
    def clean_items(self):
        """Validation commune des items JSON"""
        # ... logique partagée ...
```

---

### 1.4 `authentication/forms.py` — Validation des dates de contrat

**Problème** : La méthode `clean()` est dupliquée entre `CustomUserCreationForm` et `CustomUserChangeForm` (validation identique des dates de contrat pour le rôle CREW).

**Fichiers** : `src/authentication/forms.py` (lignes 20-41 et 77-98)

**Solution** : Créer un mixin `CrewContractValidationMixin` avec la logique `clean()` commune.

---

### 1.5 `core/forms.py` — `BulkInventoryForm.clean_items_data` / `ChangeInventoryForm.clean_items_data`

**Problème** : La méthode `clean_items_data()` est très similaire entre les deux formulaires. La principale différence est la gestion de `outside_quantity` dans `BulkInventoryForm`.

**Fichiers** : `src/core/forms.py` (lignes 26-68 et 139-165)

**Solution** : Extraire la logique de parsing/validation commune dans une méthode partagée via une classe de base ou un mixin.

---

## 2. Fichier `exports_monthly.py` dupliqué et défectueux

**Problème** : Le fichier `src/core/exports_monthly.py` duplique la section "MONTHLY STATS" de `src/core/exports.py`. De plus, il référence les fonctions utilitaires `_csv_response`, `_style_header_row` et `_autofit` sans les importer, ce qui causerait un `NameError` à l'exécution.

**Fichiers** : `src/core/exports_monthly.py` (88 lignes) et `src/core/exports.py` (lignes 456-550)

**Solution** : Supprimer `exports_monthly.py` ou le convertir en point d'import unique. La logique d'export mensuel est déjà fonctionnelle dans `exports.py`.

---

## 3. Vue `core/views.py` trop volumineuse (God Object)

**Problème** : Le fichier `core/views.py` (~517 lignes) concentre des responsabilités très différentes : gestion du personnel, gestion des fournitures, gestion des fournisseurs, dashboard, inventaires, exports (6+ types), et aide. Cela rend le fichier difficile à maintenir et à tester.

**Fichiers** : `src/core/views.py`

**Solution** : Découper en modules séparés :

```
src/core/
├── views/
│   ├── __init__.py         # Réexporte toutes les vues
│   ├── dashboard.py        # dashboard, create_order_ajax, update_inventory_ajax, extend_contract_ajax
│   ├── management.py       # staff_management, supplies_management, suppliers_management
│   ├── inventory.py        # change_inventory, print_inventory_sheet
│   └── exports.py          # export_items, export_orders, export_order, export_inventories, ...
```

---

## 4. Imports à l'intérieur des fonctions

**Problème** : De nombreuses vues effectuent leurs imports à l'intérieur du corps des fonctions au lieu du haut du fichier. Cela contrevient à PEP 8 et rend les dépendances implicites.

**Fichiers concernés** :
- `src/authentication/views.py` : `from django.contrib import messages`, `from .forms import ...`, `from .models import User` importés dans chaque fonction
- `src/supplier/views.py` : `import json`, `from django.contrib import messages`, `from supplier.forms import ...`, `from supplier.models import Order` importés dans les fonctions
- `src/core/views.py` : `from collections import defaultdict`, `from supplier.models import Order`, `from supply.models import ...` importés dans les fonctions

**Solution** : Déplacer tous les imports au début de chaque fichier conformément à PEP 8.

---

## 5. Utilisation de `Model.objects.get()` sans gestion d'erreur

**Problème** : Plusieurs vues utilisent `Model.objects.get()` directement sans `try/except` ni `get_object_or_404()`. Si l'objet n'existe pas, une exception `DoesNotExist` non gérée est levée, produisant une erreur 500.

**Fichiers et lignes concernés** :
- `src/authentication/views.py` : `change_user` (ligne 55), `delete_user` (ligne 98)
- `src/supply/views.py` : `change_item` (ligne 63), `delete_item` (ligne 94)
- `src/supplier/views.py` : `change_supplier` (ligne 35), `delete_supplier` (ligne 64), `change_order` (ligne 81), `delete_order` (ligne 126), `receive_order` (ligne 144)

**Solution** : Remplacer par `get_object_or_404()` (déjà importé dans `supply/views.py` mais non utilisé partout).

```python
# Avant
user = User.objects.get(id=user_id)

# Après
user = get_object_or_404(User, id=user_id)
```

---

## 6. Problèmes dans `settings.py`

### 6.1 Configuration `LOGGING` définie deux fois en mode frozen

**Problème** : La configuration `LOGGING` est définie une première fois (lignes 123-159), puis complètement écrasée (lignes 178-212) quand `sys.frozen` est `True`. La première définition est donc inutile.

**Fichiers** : `src/LaundryWatcher/settings.py` (lignes 97-212)

**Solution** : Supprimer la première définition de `LOGGING` en mode frozen et ne garder que la version finale.

### 6.2 `DEBUG = True` en production

**Problème** : Ligne 162-163, `DEBUG` est remis à `True` pour le mode frozen (production), ce qui annule le `DEBUG = False` initial (ligne 32). C'est un risque de sécurité et de fuite d'informations sensibles.

**Fichiers** : `src/LaundryWatcher/settings.py` (lignes 161-163)

**Solution** : Mettre `DEBUG = False` en mode frozen (production). Si le debug temporaire a été activé pour résoudre un problème, le désactiver une fois le problème résolu.

### 6.3 `EMAIL_BACKEND` défini deux fois

**Problème** : `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` est défini à la ligne 224 puis de nouveau à la ligne 295.

**Solution** : Supprimer l'une des deux définitions (conserver celle en bas du fichier, supprimer la première).

---

## 7. Fichiers temporaires à nettoyer

**Problème** : Deux fichiers temporaires sont présents à la racine du projet :
- `temp_forms_content.txt` (copie UTF-16 de `core/forms.py`)
- `temp_forms_supply.txt` (copie UTF-16 de `supply/forms.py`)

Ces fichiers ne devraient pas être versionnés.

**Solution** : Les supprimer et les ajouter au `.gitignore`.

---

## 8. Duplication des routes d'URL

**Problème** : Les routes AJAX du dashboard sont définies en double :
- Dans `src/LaundryWatcher/urls.py` (lignes 31-46)
- Dans `src/core/urls.py` (lignes 21-36)

De plus, `core/urls.py` référence `views.home` (ligne 11) qui n'existe pas dans `core/views.py`.

**Fichiers** : `src/LaundryWatcher/urls.py`, `src/core/urls.py`

**Solution** :
1. Centraliser les routes soit dans `urls.py` principal, soit via `include()` vers `core/urls.py`.
2. Supprimer la référence à `views.home` ou créer cette vue.

---

## 9. Performance du `DashboardService`

**Problème** : La vue `dashboard()` appelle successivement `DashboardService.get_all_dashboard_data()` et `DashboardService.get_alerts_count()`. Or, `get_alerts_count()` rappelle en interne `get_stock_anomalies()`, `get_order_anomalies()` et `get_contract_anomalies()`, qui sont déjà calculées par `get_all_dashboard_data()`. Cela double les requêtes SQL.

De plus, `get_stock_anomalies()` rappelle `get_missing_items()` et `get_excess_items()`, qui sont aussi déjà dans `get_all_dashboard_data()`.

**Fichiers** : `src/core/services.py` et `src/core/views.py` (lignes 201-266)

**Solution** : Calculer `alerts_count` à partir des données déjà récupérées par `get_all_dashboard_data()`.

```python
# Après
dashboard_data = DashboardService.get_all_dashboard_data()
alerts_count = {
    'stock': len(dashboard_data['stock_alerts']),
    'orders': len(dashboard_data['order_alerts']),
    'contracts': len(dashboard_data['contract_alerts']),
    'total': (len(dashboard_data['stock_alerts'])
             + len(dashboard_data['order_alerts'])
             + len(dashboard_data['contract_alerts'])),
}
```

---

## 10. Middleware exécuté à chaque requête

**Problème** : `AccountExpirationMiddleware` exécute une requête SQL (`User.objects.filter(...).update(...)`) à **chaque** requête HTTP, y compris les assets statiques. De plus, il utilise `print()` au lieu du module `logging`.

**Fichiers** : `src/authentication/middleware.py`

**Solution** :
1. Ajouter un mécanisme de cache/throttle pour n'exécuter la vérification qu'une fois par minute (ou par session).
2. Remplacer `print()` par `logging.getLogger(__name__).info()`.

```python
import logging
import time

logger = logging.getLogger(__name__)

class AccountExpirationMiddleware:
    _last_check = 0
    CHECK_INTERVAL = 60  # secondes

    def __call__(self, request):
        now = time.time()
        if now - self._last_check > self.CHECK_INTERVAL:
            self.deactivate_expired_accounts()
            AccountExpirationMiddleware._last_check = now
        response = self.get_response(request)
        return response
```

---

## 11. Opérations destructives acceptant GET

**Problème** : Les vues de suppression acceptent les requêtes GET, ce qui est contraire aux bonnes pratiques REST et peut permettre des suppressions accidentelles (via un lien, un pré-chargement navigateur, etc.).

**Vues concernées** :
- `authentication/views.py` : `delete_user`
- `supply/views.py` : `delete_item`
- `supplier/views.py` : `delete_supplier`, `delete_order`

**Solution** : Ajouter le décorateur `@require_http_methods(["POST"])` ou `@require_POST` à toutes les vues de suppression.

```python
from django.views.decorators.http import require_POST

@require_POST
@role_required(['ADMIN', 'DIRECTOR'])
def delete_user(request, user_id):
    ...
```

---

## 12. Relation M2M dupliquée entre `Supplier` et `Item`

**Problème** : Il existe deux relations ManyToMany distinctes entre `Supplier` et `Item` :
1. `Item.suppliers` (dans `supply/models.py`, ligne 22-26)
2. `Supplier.associated_items` (dans `supplier/models.py`, ligne 17-21)

Ces deux champs créent **deux tables intermédiaires séparées** en base de données, ce qui peut causer des incohérences.

**Fichiers** : `src/supply/models.py`, `src/supplier/models.py`

**Solution** : Supprimer l'une des deux relations et utiliser le reverse accessor de l'autre. Par exemple, garder `Item.suppliers` et accéder aux items d'un fournisseur via `supplier.items.all()` (grâce au `related_name='items'`).

---

## 13. Vue `import_items` trop longue avec `except` trop large

**Problème** : La vue `import_items` dans `supply/views.py` fait ~180 lignes avec une logique complexe (lecture CSV/Excel, parsing, création/mise à jour de modèles). Elle utilise aussi des `except:` (bare except) qui avalent silencieusement toutes les exceptions.

**Fichiers** : `src/supply/views.py` (lignes 100-280)

**Solution** :
1. Extraire la logique d'import dans un service dédié (`supply/services.py` ou `supply/import_service.py`).
2. Remplacer les bare `except:` par des exceptions spécifiques (`except (ValueError, TypeError):`).

---

## 14. Vue `receive_order` trop longue

**Problème** : La vue `receive_order` dans `supplier/views.py` fait ~140 lignes avec de la logique métier complexe (validation, mise à jour des stocks, création de reliquats). La logique métier devrait être dans un service.

**Fichiers** : `src/supplier/views.py` (lignes 132-274)

**Solution** : Extraire la logique de réception dans un service dédié (`supplier/services.py`).

```python
# supplier/services.py
class OrderReceptionService:
    @staticmethod
    def process_reception(order, receptions_data, user):
        """Traite la réception d'une commande et retourne les résultats."""
        ...
```

---

## 15. Absence de `default_auto_field` dans les `AppConfig`

**Problème** : Bien que `DEFAULT_AUTO_FIELD` soit défini dans `settings.py`, certains `AppConfig` ne définissent pas `default_auto_field`, ce qui peut générer des avertissements Django.

**Fichiers** : `src/authentication/apps.py`, `src/core/apps.py`, `src/supply/apps.py`, `src/supplier/apps.py`

**Solution** : Ajouter `default_auto_field = 'django.db.models.BigAutoField'` dans chaque `AppConfig`.

---

## Résumé par priorité

| Priorité | # | Problème | Impact | Effort |
|----------|---|----------|--------|--------|
| 🔴 Haute | 6.2 | `DEBUG = True` en production | Sécurité | Faible |
| 🔴 Haute | 5 | `.get()` sans gestion d'erreur | Stabilité (erreurs 500) | Faible |
| 🔴 Haute | 11 | Suppressions via GET | Sécurité | Faible |
| 🔴 Haute | 2 | `exports_monthly.py` dupliqué/défectueux | Bug potentiel (NameError) | Faible |
| 🟠 Moyenne | 1 | Code dupliqué dans les formulaires | Maintenabilité | Moyen |
| 🟠 Moyenne | 9 | Requêtes SQL dupliquées dashboard | Performance | Faible |
| 🟠 Moyenne | 12 | Relation M2M dupliquée | Incohérence données | Moyen |
| 🟠 Moyenne | 4 | Imports dans les fonctions | Lisibilité / PEP 8 | Faible |
| 🟠 Moyenne | 8 | Routes URL dupliquées | Maintenance | Faible |
| 🟠 Moyenne | 10 | Middleware à chaque requête | Performance | Faible |
| 🟡 Basse | 3 | `views.py` trop volumineux | Maintenabilité | Moyen |
| 🟡 Basse | 13 | `import_items` trop long + bare except | Maintenabilité / Debug | Moyen |
| 🟡 Basse | 14 | `receive_order` trop long | Maintenabilité | Moyen |
| 🟡 Basse | 6.1/6.3 | Settings dupliqués | Clarté | Faible |
| 🟡 Basse | 7 | Fichiers temporaires versionnés | Propreté repo | Faible |
| 🟡 Basse | 15 | `default_auto_field` manquant | Avertissements Django | Faible |

---

## Ordre d'implémentation recommandé

1. **Phase 1 — Corrections critiques** (sécurité et stabilité) :
   - [x] 6.2 — Passer `DEBUG = False` en production
   - [x] 5 — Remplacer `.get()` par `get_object_or_404()`
   - [x] 11 — Ajouter `@require_POST` aux vues de suppression
   - [x] 2 — Supprimer ou corriger `exports_monthly.py`

2. **Phase 2 — Élimination du code dupliqué** :
   - [x] 1.1 — Fusionner `CreateItemForm` / `ChangeItemForm`
   - [x] 1.2 — Fusionner `CreateSupplierForm` / `ChangeSupplierForm`
   - [x] 1.3 — Extraire la validation JSON des items en mixin
   - [x] 1.4 — Extraire la validation des dates de contrat en mixin
   - [x] 1.5 — Factoriser `clean_items_data` des formulaires d'inventaire

3. **Phase 3 — Optimisation et nettoyage** :
   - [x] 9 — Éliminer les requêtes SQL dupliquées du dashboard
   - [x] 10 — Optimiser le middleware (throttle)
   - [x] 4 — Déplacer les imports en haut des fichiers
   - [x] 8 — Centraliser les routes URL
   - [x] 7 — Supprimer les fichiers temporaires

4. **Phase 4 — Restructuration** :
   - [ ] 3 — Découper `core/views.py` en sous-modules
   - [ ] 12 — Résoudre la relation M2M dupliquée
   - [ ] 13 — Extraire `import_items` dans un service
   - [ ] 14 — Extraire `receive_order` dans un service
   - [ ] 15 — Ajouter `default_auto_field` aux `AppConfig`

---

## Notes

- Chaque refactorisation doit être accompagnée de tests unitaires pour garantir la non-régression.
- Les refactorisations de phase 4 (restructuration) peuvent impacter les imports dans d'autres fichiers ; une attention particulière est nécessaire.
- La résolution du point 12 (relation M2M dupliquée) nécessitera une migration de données pour ne pas perdre les associations existantes.
