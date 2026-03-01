# PLAN D'IMPLÉMENTATION - DASHBOARD

## Vue d'ensemble

Implémentation d'un dashboard centralisé pour la gestion des stocks, alertes et commandes du LaundryWatcher en utilisant Django + Bootstrap 5.

---

## Phase 1 : Modèles et Structure de Données

### 1.1 Mise à jour des modèles existants

**Fichier**: `src/supply/models.py`

- [x] Ajouter les champs nécessaires au modèle `Item` :
  - `last_inventory_quantity` (IntegerField) : quantité du dernier inventaire
  - `last_inventory_date` (DateTimeField) : date du dernier inventaire
  - `excess_quantity` (IntegerField, calculé) : quantité excédentaire
  - `loss_quantity` (IntegerField, calculé) : quantité perdue

- [x] Ajouter des propriétés calculées (@property) :
  - `missing_quantity` : total_quantity - (available_quantity + outside_quantity)
  - `actual_loss_quantity` : total_quantity - last_inventory_quantity

**Fichier**: `src/supplier/models.py`

- [x] Créer un nouveau modèle `Order` (Commande) :
  - `supplier` (ForeignKey vers Supplier)
  - `items` (ManyToManyField vers Item avec through pour quantités)
  - `order_date` (DateTimeField) : date de commande
  - `expected_return_date` (DateField) : date de retour attendue
  - `actual_return_date` (DateField, null=True) : date de retour réelle
  - `status` (CharField) : choices=['pending', 'delayed', 'completed']
  - `created_by` (ForeignKey vers User)

- [x] Créer un modèle `OrderItem` (through model) :
  - `order` (ForeignKey vers Order)
  - `item` (ForeignKey vers Item)
  - `quantity` (IntegerField)

### 1.2 Migrations

- [x] Créer et appliquer les migrations :
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

---

## Phase 2 : Logique Backend (Views & Services)

### 2.1 Création d'un service de calcul

**Fichier**: `src/core/services.py` (nouveau fichier)

- [x] Créer une classe `DashboardService` avec les méthodes :
  - `get_missing_items()` : retourne les items avec missing_quantity > 0
  - `get_excess_items()` : retourne les items avec excess_quantity > 0
  - `get_items_at_supplier()` : retourne les items avec outside_quantity > 0
  - `get_stock_anomalies()` : retourne toutes les anomalies de stock
  - `get_order_anomalies()` : retourne les commandes en retard
  - `get_contract_anomalies()` : retourne les Crew avec contrat expirant dans 2 semaines
  - `get_outdated_orders()` : commandes dont expected_return_date est dépassée
  - `get_waited_orders()` : commandes en attente dans les délais

### 2.2 Vue Dashboard

**Fichier**: `src/core/views.py`

- [x] Créer une vue `DashboardView` (TemplateView ou Vue basée sur fonction) :
  - Récupérer toutes les données via `DashboardService`
  - Passer les contextes suivants au template :
    - `missing_items` : articles manquants
    - `excess_items` : articles excédentaires
    - `items_at_supplier` : articles chez fournisseur
    - `stock_alerts` : anomalies de stock
    - `order_alerts` : anomalies de commandes
    - `contract_alerts` : alertes fin de contrat
    - `outdated_orders` : commandes en retard
    - `waited_orders` : commandes attendues

- [x] Ajouter des permissions (decorators) :
  - `@login_required`
  - Vérifier le rôle (Director et Admin uniquement)

---

## Phase 3 : Interface Utilisateur (Templates)

### 3.1 Template principal du Dashboard

**Fichier**: `src/core/templates/dashboard.html`

Structure HTML avec Bootstrap 5 :

- [x] Créer le layout de base :
  ```html
  {% extends "base.html" %}
  ```

- [x] Section Header avec titre et actions rapides

- [x] Conteneur principal avec 3 sections rétractables (Accordion Bootstrap 5) :
  1. **Section Stocks**
  2. **Section Alertes**
  3. **Section Statut Commandes**

### 3.2 Section 1 : Stocks (Accordion Item 1)

- [x] Créer des cards Bootstrap pour :
  - **Articles manquants** :
    - Tableau avec colonnes : Nom, Catégorie, Quantité manquante, Action
    - Badge rouge si critique
  - **Articles chez fournisseur** :
    - Tableau avec colonnes : Nom, Fournisseur, Quantité outside, Date envoi
  - **Articles excédentaires** :
    - Tableau avec colonnes : Nom, Quantité excès, Suggestion

- [x] Ajouter des graphiques (optionnel, Phase bonus) :
  - Chart.js pour visualisation des stocks

### 3.3 Section 2 : Alertes (Accordion Item 2)

- [x] Créer un système d'alertes avec badges colorés :
  - **Anomalies Stock** :
    - Liste avec icônes (Bootstrap Icons)
    - Couleur : rouge (défaut), orange (excès)
  - **Anomalies Commande** :
    - Liste des commandes en retard
    - Indication du nombre de jours de retard
    - Couleur : rouge si > 7 jours, orange si 3-7 jours
  - **Anomalies Contrat** :
    - Liste des Crew avec fin de contrat proche
    - Boutons d'action : "Prolonger" / "Confirmer fin"

### 3.4 Section 3 : Statut Commandes (Accordion Item 3)

- [x] Créer deux sous-sections avec tabs Bootstrap :
  - **Tab "Commandes en retard"** (`outdated_orders`) :
    - Liste rouge avec détails : fournisseur, items, date attendue, retard
  - **Tab "Commandes attendues"** (`waited_orders`) :
    - Liste verte avec détails : fournisseur, items, date attendue

### 3.5 Partials réutilisables

**Fichier**: `src/core/templates/partials/`

- [x] `dashboard_stock_card.html` : card pour un item de stock
- [x] `dashboard_alert_item.html` : item d'alerte
- [x] `dashboard_order_row.html` : ligne de commande

---

## Phase 4 : Styles et Interactivité

### 4.1 CSS personnalisé

**Fichier**: `src/static/css/dashboard.css` (nouveau fichier)

- [ ] Styles pour les cards de dashboard :
  - Ombres et espacements
  - Couleurs des badges (success, warning, danger)
  - Animations de hover

- [ ] Styles pour les alertes :
  - Icônes et couleurs cohérentes
  - Animation de pulsation pour alertes critiques

- [ ] Responsive design :
  - Adaptation mobile (cards en colonne)
  - Tables scrollables sur mobile

### 4.2 JavaScript / HTMX (optionnel)

**Fichier**: `src/static/js/dashboard.js` (nouveau fichier)

- [ ] Fonctions pour :
  - Rafraîchissement automatique des données (AJAX)
  - Gestion des accordions (état ouvert/fermé dans localStorage)
  - Filtres et recherche dans les tableaux
  - Actions rapides (boutons d'action)

---

## Phase 5 : URLs et Navigation

### 5.1 Configuration des URLs

**Fichier**: `src/core/urls.py` (ou créer si n'existe pas)

- [ ] Ajouter la route :
  ```python
  path('dashboard/', views.DashboardView.as_view(), name='dashboard')
  ```

**Fichier**: `src/LaundryWatcher/urls.py`

- [ ] Inclure les URLs de core :
  ```python
  path('', include('core.urls'))
  ```

### 5.2 Navigation

**Fichier**: `src/LaundryWatcher/templates/base.html`

- [ ] Ajouter le lien Dashboard dans la navbar :
  - Visible uniquement pour Director et Admin
  - Badge de notification pour alertes

---

## Phase 6 : Tests et Optimisation

### 6.1 Tests unitaires

**Fichier**: `src/core/tests.py`

- [ ] Tests pour `DashboardService` :
  - Test calcul des quantités manquantes
  - Test détection des anomalies
  - Test filtrage des commandes en retard

- [ ] Tests pour les vues :
  - Test accès autorisé/refusé selon rôles
  - Test contexte passé au template

### 6.2 Optimisation des requêtes

- [ ] Utiliser `select_related()` et `prefetch_related()` :
  - Pour les relations Item-Supplier
  - Pour les relations Order-Item

- [ ] Ajouter des index sur les champs de recherche fréquents :
  - `Item.available_quantity`
  - `Order.expected_return_date`
  - `User.date_end_contract`

### 6.3 Cache (optionnel)

- [ ] Mettre en cache les données du dashboard :
  - Cache de 5 minutes pour les statistiques
  - Invalidation lors de modifications

---

## Phase 7 : Actions Rapides (Bonus)

### 7.1 Boutons d'action sur le dashboard

- [ ] **Action : Créer une commande** :
  - Modal Bootstrap pour création rapide
  - Formulaire simplifié

- [ ] **Action : Enregistrer un inventaire** :
  - Modal pour mise à jour des quantités
  - Sauvegarde de `last_inventory_quantity`

- [ ] **Action : Prolonger un contrat** :
  - Modal avec sélection de nouvelle date
  - Mise à jour de `date_end_contract`

---

## Phase 8 : Documentation et Déploiement

### 8.1 Documentation

- [ ] Documenter le code (docstrings Python)
- [ ] Créer un guide utilisateur pour le dashboard
- [ ] Ajouter des commentaires dans les templates

### 8.2 Fixtures de test

- [ ] Créer des données de test pour le dashboard :
  - Items avec différents états (manquant, excès, normal)
  - Commandes en retard et en attente
  - Users Crew avec contrats expirant bientôt

### 8.3 Déploiement

- [ ] Vérifier les settings de production
- [ ] Collectstatic pour les nouveaux fichiers CSS/JS
- [ ] Tester en environnement de staging

---

## Checklist de Validation

Avant de considérer le dashboard comme terminé :

- [ ] Toutes les vues (Stocks, Alertes, Commandes) sont rétractables
- [ ] Les calculs de quantités sont corrects et testés
- [ ] L'interface est responsive (mobile & desktop)
- [ ] Les permissions sont correctement appliquées
- [ ] Les alertes sont clairement visibles et informatives
- [ ] Les performances sont optimisées (< 1s de chargement)
- [ ] Le code est documenté et testé

---

## Technologies et Bibliothèques

### Backend
- Django (views, models, ORM)
- Python datetime pour calculs de dates

### Frontend
- Bootstrap 5.3+ (Accordion, Cards, Badges, Tables, Modals)
- Bootstrap Icons pour les icônes
- Chart.js (optionnel pour graphiques)
- HTMX (optionnel pour interactivité)

### CSS/JS
- CSS personnalisé dans `static/css/dashboard.css`
- JavaScript vanilla ou jQuery pour interactivité

---

## Ordre d'implémentation recommandé

1. ✅ **Phase 1** : Modèles et migrations (base de données)
2. ✅ **Phase 2** : Service et logique métier
3. ✅ **Phase 3** : Template HTML de base avec Accordion
4. ✅ **Phase 5** : URLs et navigation
5. ✅ **Phase 4** : Styles CSS et interactivité
6. ✅ **Phase 6** : Tests et optimisation
7. ✅ **Phase 7** : Actions rapides (bonus)
8. ✅ **Phase 8** : Documentation et déploiement

---

## Notes Importantes

- **Sécurité** : S'assurer que seuls Admin et Director peuvent accéder au dashboard
- **Performance** : Optimiser les requêtes pour éviter le N+1 problem
- **UX** : Les accordions doivent mémoriser leur état (ouvert/fermé)
- **Responsive** : Tester sur mobile, tablette et desktop
- **Accessibilité** : Utiliser les attributs ARIA de Bootstrap correctement

---

## Temps estimé

- Phase 1 : 2-3 heures
- Phase 2 : 3-4 heures
- Phase 3 : 4-6 heures
- Phase 4 : 2-3 heures
- Phase 5 : 1 heure
- Phase 6 : 3-4 heures
- Phase 7 : 2-3 heures (optionnel)
- Phase 8 : 1-2 heures

**Total estimé** : 18-26 heures de développement
