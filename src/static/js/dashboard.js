/**
 * DASHBOARD JAVASCRIPT - LaundryWatcher
 * Fonctionnalités interactives du dashboard
 */

(function() {
    'use strict';

    // ==================== CONFIGURATION ====================
    const CONFIG = {
        REFRESH_INTERVAL: 300000, // 5 minutes en millisecondes
        STORAGE_KEY: 'dashboard_accordion_state',
        AUTO_REFRESH_ENABLED: false // Désactivé par défaut
    };

    // ==================== GESTION DES ACCORDIONS ====================
    
    /**
     * Sauvegarde l'état des accordions dans localStorage
     */
    function saveAccordionState() {
        const accordions = document.querySelectorAll('.accordion-collapse');
        const state = {};
        
        accordions.forEach((accordion) => {
            state[accordion.id] = accordion.classList.contains('show');
        });
        
        localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(state));
    }

    /**
     * Restaure l'état des accordions depuis localStorage
     */
    function restoreAccordionState() {
        const savedState = localStorage.getItem(CONFIG.STORAGE_KEY);
        
        if (!savedState) return;
        
        try {
            const state = JSON.parse(savedState);
            
            Object.entries(state).forEach(([accordionId, isOpen]) => {
                const accordion = document.getElementById(accordionId);
                const button = document.querySelector(`[data-bs-target="#${accordionId}"]`);
                
                if (accordion && button) {
                    if (isOpen) {
                        accordion.classList.add('show');
                        button.classList.remove('collapsed');
                        button.setAttribute('aria-expanded', 'true');
                    } else {
                        accordion.classList.remove('show');
                        button.classList.add('collapsed');
                        button.setAttribute('aria-expanded', 'false');
                    }
                }
            });
        } catch (error) {
            console.error('Erreur lors de la restauration de l\'état des accordions:', error);
        }
    }

    /**
     * Initialise la sauvegarde automatique de l'état des accordions
     */
    function initAccordionStateSaving() {
        const accordions = document.querySelectorAll('.accordion-collapse');
        
        accordions.forEach((accordion) => {
            accordion.addEventListener('shown.bs.collapse', saveAccordionState);
            accordion.addEventListener('hidden.bs.collapse', saveAccordionState);
        });
    }

    // ==================== RAFRAÎCHISSEMENT AUTO ====================
    
    /**
     * Rafraîchit les données du dashboard via AJAX
     */
    function refreshDashboard() {
        if (!CONFIG.AUTO_REFRESH_ENABLED) return;
        
        const currentUrl = window.location.href;
        
        fetch(currentUrl, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            // Créer un parser DOM
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Mettre à jour uniquement le contenu du dashboard
            const newContent = doc.querySelector('#dashboardAccordion');
            const currentContent = document.querySelector('#dashboardAccordion');
            
            if (newContent && currentContent) {
                currentContent.innerHTML = newContent.innerHTML;
                
                // Réinitialiser les événements
                initAccordionStateSaving();
                initTableFeatures();
                addAnimations();
                
                // Afficher notification
                showNotification('Dashboard actualisé', 'success');
            }
        })
        .catch(error => {
            console.error('Erreur lors du rafraîchissement:', error);
            showNotification('Erreur de rafraîchissement', 'danger');
        });
    }

    /**
     * Démarre le rafraîchissement automatique
     */
    function startAutoRefresh() {
        if (CONFIG.AUTO_REFRESH_ENABLED) {
            setInterval(refreshDashboard, CONFIG.REFRESH_INTERVAL);
            console.log(`Auto-refresh activé (${CONFIG.REFRESH_INTERVAL / 1000}s)`);
        }
    }

    // ==================== FILTRES ET RECHERCHE ====================
    
    /**
     * Ajoute une fonction de recherche à un tableau
     */
    function addTableSearch(tableId, searchInputId) {
        const searchInput = document.getElementById(searchInputId);
        const table = document.getElementById(tableId);
        
        if (!searchInput || !table) return;
        
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const text = row.textContent.toLowerCase();
                
                if (text.includes(filter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        });
    }

    /**
     * Initialise les fonctionnalités de table
     */
    function initTableFeatures() {
        // Tri des colonnes
        const headers = document.querySelectorAll('th[data-sortable]');
        
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(this);
            });
        });
    }

    /**
     * Trie un tableau par colonne
     */
    function sortTable(header) {
        const table = header.closest('table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const columnIndex = Array.from(header.parentElement.children).indexOf(header);
        const currentDirection = header.dataset.sortDirection || 'asc';
        const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
        
        rows.sort((a, b) => {
            const aText = a.children[columnIndex].textContent.trim();
            const bText = b.children[columnIndex].textContent.trim();
            
            if (newDirection === 'asc') {
                return aText.localeCompare(bText, 'fr', { numeric: true });
            } else {
                return bText.localeCompare(aText, 'fr', { numeric: true });
            }
        });
        
        rows.forEach(row => tbody.appendChild(row));
        header.dataset.sortDirection = newDirection;
    }

    // ==================== NOTIFICATIONS ====================
    
    /**
     * Affiche une notification toast
     */
    function showNotification(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        
        if (!toastContainer) {
            // Créer le conteneur s'il n'existe pas
            const container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '11';
            document.body.appendChild(container);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        document.getElementById('toastContainer').appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 3000
        });
        
        bsToast.show();
        
        // Supprimer après disparition
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // ==================== ANIMATIONS ====================
    
    /**
     * Ajoute des animations aux éléments
     */
    function addAnimations() {
        // Animation au chargement
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
        
        // Pulsation pour les alertes critiques
        const criticalAlerts = document.querySelectorAll('[data-severity="danger"]');
        criticalAlerts.forEach(alert => {
            alert.classList.add('alert-critical');
        });
    }

    // ==================== UTILITAIRES ====================
    
    /**
     * Formate un nombre avec séparateurs de milliers
     */
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    }

    /**
     * Copie du texte dans le presse-papiers
     */
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copié dans le presse-papiers', 'success');
        }).catch(err => {
            console.error('Erreur de copie:', err);
            showNotification('Erreur de copie', 'danger');
        });
    }

    /**
     * Exporte les données du tableau en CSV
     */
    function exportTableToCSV(tableId, filename = 'export.csv') {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        const rows = table.querySelectorAll('tr');
        const csv = [];
        
        rows.forEach(row => {
            const cols = row.querySelectorAll('td, th');
            const rowData = Array.from(cols).map(col => {
                return '"' + col.textContent.trim().replace(/"/g, '""') + '"';
            });
            csv.push(rowData.join(','));
        });
        
        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    /**
     * Imprime le dashboard
     */
    function printDashboard() {
        // Ouvrir tous les accordions avant impression
        const accordions = document.querySelectorAll('.accordion-collapse');
        accordions.forEach(accordion => {
            accordion.classList.add('show');
        });
        
        window.print();
    }

    // ==================== COMPTEURS ANIMÉS ====================
    
    /**
     * Anime un compteur
     */
    function animateCounter(element, target, duration = 1000) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 16);
    }

    /**
     * Initialise les compteurs animés
     */
    function initAnimatedCounters() {
        const counters = document.querySelectorAll('[data-counter]');
        counters.forEach(counter => {
            const target = parseInt(counter.dataset.counter);
            animateCounter(counter, target);
        });
    }

    // ==================== ACTIONS RAPIDES (MODALS) ====================
    
    /**
     * Initialise les modals et leurs formulaires
     */
    function initModals() {
        initInventoryModal();
        initContractModal();
        initOrderModal();
    }

    /**
     * Initialise le modal d'inventaire
     */
    function initInventoryModal() {
        // Ajouter un bouton "Enregistrer inventaire" sur chaque ligne d'article
        document.querySelectorAll('[data-item-id]').forEach(row => {
            const itemId = row.dataset.itemId;
            const itemName = row.dataset.itemName;
            
            // Créer un bouton d'action si pas déjà présent
            if (!row.querySelector('.btn-inventory')) {
                const actionCell = row.querySelector('.action-cell');
                if (actionCell) {
                    const btn = document.createElement('button');
                    btn.className = 'btn btn-sm btn-info btn-inventory';
                    btn.innerHTML = '<i class="bi bi-clipboard-check"></i>';
                    btn.title = 'Enregistrer inventaire';
                    btn.onclick = () => openInventoryModal(itemId, itemName);
                    actionCell.appendChild(btn);
                }
            }
        });
    }

    /**
     * Ouvre le modal d'inventaire
     */
    function openInventoryModal(itemId, itemName) {
        document.getElementById('inventoryItemId').value = itemId;
        document.getElementById('inventoryItemName').textContent = itemName;
        document.getElementById('inventoryQuantity').value = '';
        document.getElementById('inventoryFormErrors').classList.add('d-none');
        
        const modal = new bootstrap.Modal(document.getElementById('inventoryModal'));
        modal.show();
    }

    /**
     * Initialise le modal de prolongation de contrat
     */
    function initContractModal() {
        // Ajouter des boutons sur les alertes de contrat
        document.querySelectorAll('[data-user-id]').forEach(row => {
            const userId = row.dataset.userId;
            const username = row.dataset.username;
            const currentDate = row.dataset.endDate;
            
            if (!row.querySelector('.btn-contract')) {
                const actionCell = row.querySelector('.action-cell');
                if (actionCell) {
                    const btn = document.createElement('button');
                    btn.className = 'btn btn-sm btn-warning btn-contract';
                    btn.innerHTML = '<i class="bi bi-calendar-plus"></i>';
                    btn.title = 'Prolonger contrat';
                    btn.onclick = () => openContractModal(userId, username, currentDate);
                    actionCell.appendChild(btn);
                }
            }
        });
    }

    /**
     * Ouvre le modal de prolongation de contrat
     */
    function openContractModal(userId, username, currentDate) {
        document.getElementById('contractUserId').value = userId;
        document.getElementById('contractUsername').textContent = username;
        document.getElementById('contractCurrentDate').textContent = currentDate;
        document.getElementById('contractNewDate').value = '';
        document.getElementById('contractFormErrors').classList.add('d-none');
        
        const modal = new bootstrap.Modal(document.getElementById('contractModal'));
        modal.show();
    }

    /**
     * Initialise le formulaire de création de commande
     */
    function initOrderModal() {
        const form = document.getElementById('createOrderForm');
        if (!form) return;

        // Définir la date par défaut (7 jours)
        const expectedDateInput = document.getElementById('orderExpectedDate');
        const today = new Date();
        today.setDate(today.getDate() + 7);
        expectedDateInput.value = today.toISOString().split('T')[0];
        expectedDateInput.min = new Date().toISOString().split('T')[0];

        form.addEventListener('submit', handleOrderSubmit);
    }

    /**
     * Gère la soumission du formulaire de commande
     */
    async function handleOrderSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const errorDiv = document.getElementById('orderFormErrors');
        
        try {
            const response = await fetch('/dashboard/create-order/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showNotification(data.message, 'success');
                bootstrap.Modal.getInstance(document.getElementById('createOrderModal')).hide();
                form.reset();
                errorDiv.classList.add('d-none');
                
                // Rafraîchir la page après 1 seconde
                setTimeout(() => window.location.reload(), 1000);
            } else {
                errorDiv.textContent = formatErrors(data.errors);
                errorDiv.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Erreur:', error);
            showNotification('Erreur lors de la création de la commande', 'danger');
        }
    }

    /**
     * Initialise les formulaires d'inventaire et de contrat
     */
    function initActionForms() {
        // Formulaire d'inventaire
        const inventoryForm = document.getElementById('inventoryForm');
        if (inventoryForm) {
            inventoryForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const errorDiv = document.getElementById('inventoryFormErrors');
                
                try {
                    const response = await fetch('/dashboard/update-inventory/', {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                        }
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        showNotification(data.message, 'success');
                        bootstrap.Modal.getInstance(document.getElementById('inventoryModal')).hide();
                        errorDiv.classList.add('d-none');
                        
                        setTimeout(() => window.location.reload(), 1000);
                    } else {
                        errorDiv.textContent = formatErrors(data.errors);
                        errorDiv.classList.remove('d-none');
                    }
                } catch (error) {
                    console.error('Erreur:', error);
                    showNotification('Erreur lors de l\'enregistrement', 'danger');
                }
            });
        }

        // Formulaire de prolongation de contrat
        const contractForm = document.getElementById('contractForm');
        if (contractForm) {
            contractForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const errorDiv = document.getElementById('contractFormErrors');
                
                try {
                    const response = await fetch('/dashboard/extend-contract/', {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                        }
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        showNotification(data.message, 'success');
                        bootstrap.Modal.getInstance(document.getElementById('contractModal')).hide();
                        errorDiv.classList.add('d-none');
                        
                        setTimeout(() => window.location.reload(), 1000);
                    } else {
                        errorDiv.textContent = formatErrors(data.errors);
                        errorDiv.classList.remove('d-none');
                    }
                } catch (error) {
                    console.error('Erreur:', error);
                    showNotification('Erreur lors de la prolongation', 'danger');
                }
            });
        }
    }

    /**
     * Formate les erreurs de formulaire pour l'affichage
     */
    function formatErrors(errors) {
        if (typeof errors === 'string') return errors;
        
        const errorList = [];
        for (const [field, messages] of Object.entries(errors)) {
            if (Array.isArray(messages)) {
                errorList.push(...messages);
            } else {
                errorList.push(messages);
            }
        }
        
        return errorList.join('. ');
    }

    // ==================== INITIALISATION ====================
    
    /**
     * Initialise toutes les fonctionnalités du dashboard
     */
    function init() {
        console.log('Dashboard JS initialisé');
        
        // Restaurer l'état des accordions
        restoreAccordionState();
        
        // Initialiser la sauvegarde automatique
        initAccordionStateSaving();
        
        // Initialiser les fonctionnalités de table
        initTableFeatures();
        
        // Ajouter les animations
        addAnimations();
        
        // Initialiser les compteurs animés
        initAnimatedCounters();
        
        // Initialiser les modals et formulaires d'actions rapides
        initModals();
        initActionForms();
        
        // Démarrer le rafraîchissement auto (si activé)
        startAutoRefresh();
        
        // Exposer certaines fonctions globalement
        window.dashboardUtils = {
            exportTableToCSV,
            printDashboard,
            copyToClipboard,
            showNotification,
            refreshDashboard,
            openInventoryModal,
            openContractModal
        };
    }

    // Exécuter au chargement du DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
