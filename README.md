# SupplyManager (LaundryWatcher)

Application de gestion locale pour blanchisserie, conçue pour gérer les stocks, les inventaires et le personnel.

## 📋 Fonctionnalités

*   **Gestion des stocks** : Suivi des entrées et sorties de matériel.
*   **Inventaires** : Saisie et historique des inventaires mensuels.
*   **Personnel** : Gestion des employés et des plannings (si applicable).
*   **Tableau de bord** : Vue synthétique de l'activité.
*   **Exports** : Génération de rapports Excel.
*   **Mise à jour automatique** : Notification lorsqu'une nouvelle version est disponible sur GitHub.

## 🚀 Installation (Utilisateur)

1.  Téléchargez la dernière version (`SupplyManager_Setup.exe`) depuis la section [Releases](https://github.com/Clement-Scipion/SupplyManager/releases) du dépôt GitHub.
2.  Lancez l'installateur et suivez les instructions.
3.  Une icône **SupplyManager** sera créée sur le bureau.

> **Note :** Vos données (base de données `db.sqlite3`) sont stockées de manière sécurisée dans votre dossier utilisateur (`%APPDATA%\SupplyManager`) et **ne sont pas effacées** lors des mises à jour.

---

## 🛠️ Développement

Ce projet est une application **Django** (Python) empaquetée comme une application de bureau Windows autonome.

### Prérequis
*   Python 3.12+
*   Poetry (Gestionnaire de dépendances)
*   Inno Setup (Pour créer l'installateur Windows)

### Installation de l'environnement
```bash
# Installer les dépendances
poetry install

# Activer l'environnement virtuel
poetry shell

# Appliquer les migrations
python src/manage.py migrate

# Lancer le serveur de développement
python src/manage.py runserver
```

---

## 📦 Compilation & Déploiement

Cette procédure permet de créer le fichier `.exe` et l'installateur distribuable.

### 1. Incrémenter la version
Avant de compiler, modifiez toujours le numéro de version dans ces **deux fichiers** :
1.  `src/LaundryWatcher/version.py` : `__version__ = "0.X.Y"`
2.  `setup_script.iss` : `#define MyAppVersion "0.X.Y"`

### 2. Générer l'exécutable (PyInstaller)
Cette étape transforme le code Python en un dossier contenant `SupplyManager.exe`.

```powershell
# Depuis la racine du projet
pyinstaller --clean --noconfirm supplymanager.spec
```
*Le résultat se trouve dans le dossier `dist/`.*

### 3. Créer l'installateur (Inno Setup)
Cette étape crée le fichier d'installation final pour l'utilisateur.

1.  Ouvrez le fichier `setup_script.iss` avec **Inno Setup Compiler**.
2.  Cliquez sur le bouton **Build > Compile** (ou `Ctrl+F9`).
3.  Le fichier `SupplyManager_Setup.exe` sera généré dans le dossier `Output/`.

### 4. Publier la mise à jour
Pour que l'application détecte la mise à jour chez l'utilisateur :

1.  Allez sur GitHub > **Releases** > **Draft a new release**.
2.  **Tag version** : `v0.X.Y` (Attention : le `v` est important, le reste doit correspondre à `version.py`).
3.  **Titre** : Version 0.X.Y.
4.  Attachez le fichier `Output/SupplyManager_Setup.exe`.
5.  Cliquez sur **Publish release**.

---

## 📂 Structure des données

*   **Code source** : Dans le dossier `src/`.
*   **Base de données (Prod)** : `%APPDATA%\SupplyManager\db.sqlite3`.
*   **Logs d'erreurs** : `%APPDATA%\SupplyManager\startup_errors.log`.

## 🛡️ Sécurité

Les dépendances critiques (Django, Pillow, etc.) sont gérées via Poetry et surveillées par Dependabot.
Lors d'une mise à jour de sécurité :
1.  `poetry update <package>`
2.  Tester l'application.
3.  Recompiler et redéployer.
