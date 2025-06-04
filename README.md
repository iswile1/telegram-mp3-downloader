# Téléchargeur de MP3 Telegram

Ce script permet de télécharger automatiquement tous les fichiers MP3 d'un canal Telegram spécifié.

## Installation

Pour installer et utiliser ce script, suivez les étapes suivantes :

1.  **Cloner le dépôt ou télécharger les fichiers :**
    Si vous utilisez Git, clonez le dépôt avec la commande :
    ```bash
    git clone <URL_DU_DEPOT>
    ```
    Si non, téléchargez simplement les fichiers du projet.

2.  **Installer Python :**
    Assurez-vous d'avoir Python 3.7 ou une version supérieure installée sur votre système. Vous pouvez le télécharger depuis le site officiel de [Python](https://www.python.org/downloads/).

3.  **Naviguer dans le dossier du projet :**
    Ouvrez un terminal ou une invite de commandes et naviguez jusqu'au dossier où vous avez cloné ou téléchargé le script :
    ```bash
    cd /chemin/vers/telegram_downloader
    ```

4.  **Installer les dépendances :**
    Le script nécessite quelques bibliothèques Python. Installez-les en utilisant pip (le gestionnaire de paquets de Python) et le fichier `requirements.txt` :
    ```bash
    pip install -r requirements.txt
    ```

## Prérequis

1. Python 3.7 ou supérieur
2. Les bibliothèques Python requises :
   ```
   pip install telethon
   ```

## Configuration

1. Obtenez vos identifiants Telegram :
   - Allez sur [my.telegram.org](https://my.telegram.org/)
   - Connectez-vous avec votre numéro de téléphone
   - Créez une nouvelle application
   - Notez votre `API_ID` et `API_HASH`

2. Configurez le fichier `config.py` :
   - `API_ID` : Votre API ID Telegram
   - `API_HASH` : Votre API Hash Telegram
   - `PHONE_NUMBER` : Votre numéro de téléphone (format: '+33612345678')
   - `CHANNEL_LINK` : Le lien du canal (ex: 'https://t.me/nomducanal')
   - `MESSAGE_LIMIT` : Nombre maximum de messages à télécharger (par défaut: 100)

## Utilisation

1. Assurez-vous que votre fichier `config.py` est correctement configuré
2. Ouvrez un terminal dans le dossier du projet
3. Exécutez :
   ```
   python telegram_mp3_downloader.py
   ```
4. À la première utilisation :
   - Vous recevrez un code de vérification par Telegram
   - Entrez ce code dans le terminal
   - Une session sera créée pour les utilisations futures

## Notes importantes

- Le téléchargement des fichiers peut prendre du temps, en fonction de la quantité de MP3 et des limitations de l'API Telegram.
- Il est recommandé de laisser le script s'exécuter en arrière-plan dans un terminal.

## Structure du projet

```
telegram_downloader/
├── README.md
├── config.py           # Configuration de l'application
├── telegram_mp3_downloader.py  # Script principal
├── session_name.session    # Fichier de session (créé automatiquement)
└── telegram_mp3s/      # Dossier de téléchargement (créé automatiquement)
```

## Fonctionnalités

- Téléchargement automatique des fichiers MP3
- Gestion de session pour éviter de se reconnecter à chaque fois
- Limite configurable du nombre de messages à télécharger
- Création automatique du dossier de téléchargement
- Support des canaux publics et privés

## Sécurité

- Vos identifiants sont stockés localement dans `config.py`
- Le fichier de session est créé localement et ne doit pas être partagé
- Les téléchargements sont effectués de manière sécurisée via l'API Telegram

## Support

Si vous rencontrez des problèmes :
1. Vérifiez que vos identifiants dans `config.py` sont corrects
2. Assurez-vous d'avoir les droits d'accès au canal
3. Vérifiez votre connexion internet 