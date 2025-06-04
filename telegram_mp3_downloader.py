from telethon import TelegramClient, events
import os
import asyncio
import re
from tqdm import tqdm
import time
import traceback
from datetime import datetime
import sys


# Chargement de la configuration
def load_config():
    try:
        if not os.path.exists('config.py'):
            print("Création du fichier de configuration...")
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write("""# Configuration Telegram
API_ID = ''  # Votre API ID
API_HASH = ''  # Votre API Hash
PHONE_NUMBER = ''  # Format: '+33612345678'
CHANNEL_LINK = ''  # Lien du canal Telegram
""")
            print("Veuillez remplir le fichier config.py avec vos informations.")
            sys.exit(1)
            
        from config import API_ID, API_HASH, PHONE_NUMBER, CHANNEL_LINK, DOWNLOAD_PATH, SESSION_NAME, MESSAGE_LIMIT
        
        if not all([API_ID, API_HASH, PHONE_NUMBER, CHANNEL_LINK]):
            print("Erreur: Veuillez remplir tous les champs obligatoires (API_ID, API_HASH, PHONE_NUMBER, CHANNEL_LINK) dans config.py")
            sys.exit(1)
            
        # Utiliser les valeurs par défaut si non spécifiées dans config.py
        DOWNLOAD_FOLDER = DOWNLOAD_PATH if 'DOWNLOAD_PATH' in locals() else 'telegram_mp3s'
        SESSION_NAME = SESSION_NAME if 'SESSION_NAME' in locals() else 'session_name'
        MESSAGE_LIMIT = MESSAGE_LIMIT if 'MESSAGE_LIMIT' in locals() else None # Utiliser None pour telecharger tous les messages si pas de limite

        return API_ID, API_HASH, PHONE_NUMBER, CHANNEL_LINK, DOWNLOAD_FOLDER, SESSION_NAME, MESSAGE_LIMIT
        
    except ImportError:
        print("Erreur: Fichier de configuration manquant ou invalide.")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration : {e}")
        sys.exit(1)


# Configuration du client pour optimiser la vitesse
CLIENT_SETTINGS = {
    'connection_retries': 5,
    'retry_delay': 0.1,
    'timeout': 30,
    'use_ipv6': False,
    'auto_reconnect': True,
    'device_model': 'Desktop',
    'system_version': 'Windows 10',
    'app_version': '1.0',
    'lang_code': 'fr',
    'system_lang_code': 'fr'
}

def print_info():
    current_year = datetime.now().year
    print("\n" + "="*50)
    print("""
    ╔══════════════════════════════════════════╗
    ║                                          ║
    ║     TELEGRAM MP3 DOWNLOADER              ║
    ║                                          ║
    ║     Script simple pour télécharger des   ║
    ║     MP3 depuis un canal Telegram.        ║
    ║                                          ║
    ║     Utilisation libre                    ║
    ║     Copyright © 2024-{}                  ║
    ║                                          ║
    ╚══════════════════════════════════════════╝
    """.format(current_year))
    print("="*50 + "\n")

def extract_channel_username(link):
    try:
        if link.startswith('@'):
            return link
        if 't.me/' in link:
            username = link.split('t.me/')[-1]
            return f'@{username}'
        if 'telegram.me/' in link:
            username = link.split('telegram.me/')[-1]
            return f'@{username}'
        return link
    except Exception as e:
        print(f"Erreur lors de l'extraction du nom d'utilisateur: {str(e)}")
        return link

def get_downloaded_files(download_folder):
    try:
        if not os.path.exists(download_folder):
            return set()
        return {f for f in os.listdir(download_folder) if f.endswith('.mp3')}
    except Exception as e:
        print(f"Erreur lors de la récupération des fichiers: {str(e)}")
        return set()

def get_file_name(message):
    try:
        if hasattr(message.media.document, 'attributes'):
            for attr in message.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    return attr.file_name
        
        if message.text:
            clean_name = re.sub(r'[<>:"/\\|?*]', '', message.text)
            clean_name = clean_name.strip()
            if clean_name:
                return f"{clean_name}.mp3"
        
        return f"audio_{message.id}.mp3"
    except Exception as e:
        print(f"Erreur lors de la récupération du nom du fichier: {str(e)}")
        return f"audio_{message.id}.mp3"

async def download_file(client, message, pbar, downloaded_files, download_folder):
    try:
        file_name = get_file_name(message)
        if file_name in downloaded_files:
            pbar.update(1)
            pbar.set_description(f"Déjà téléchargé: {file_name}")
            return True

        path = await message.download_media(
            download_folder,
            progress_callback=lambda d, t: pbar.set_description(
                f"Téléchargement: {file_name} ({d/1024/1024:.1f}MB/{t/1024/1024:.1f}MB) - {d/t*100:.1f}%"
            )
        )

        if path:
            new_path = os.path.join(download_folder, file_name)
            if path != new_path:
                os.rename(path, new_path)
            
            pbar.update(1)
            pbar.set_description(f"Téléchargé: {file_name}")
            return True
        return False

    except Exception as e:
        print(f"\nErreur lors du téléchargement de {file_name}: {str(e)}")
        return False

async def main():
    try:
        # Chargement de la configuration
        API_ID, API_HASH, PHONE_NUMBER, CHANNEL_LINK, DOWNLOAD_FOLDER, SESSION_NAME, MESSAGE_LIMIT = load_config()
        
        print_info()
        print("Démarrage du script...")
        start_time = time.time()
        
        if not os.path.exists(DOWNLOAD_FOLDER):
            print(f"Création du dossier {DOWNLOAD_FOLDER}...")
            os.makedirs(DOWNLOAD_FOLDER)

        downloaded_files = get_downloaded_files(DOWNLOAD_FOLDER)
        print(f"Fichiers déjà téléchargés: {len(downloaded_files)}")

        print("Connexion à Telegram...")
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH, **CLIENT_SETTINGS)
        await client.start(phone=PHONE_NUMBER)

        channel_username = extract_channel_username(CHANNEL_LINK)
        print(f"Connexion établie. Recherche des fichiers MP3 dans {channel_username}...")

        print("Récupération des messages...")
        channel = await client.get_entity(channel_username)
        messages = await client.get_messages(channel, limit=MESSAGE_LIMIT)

        print("Filtrage des fichiers MP3...")
        mp3_messages = []
        for message in messages:
            if message.media and hasattr(message.media, 'document'):
                if message.media.document.mime_type == 'audio/mpeg':
                    mp3_messages.append(message)

        total_files = len(mp3_messages)
        print(f"\n{total_files} fichiers MP3 trouvés dans le canal")
        print("Téléchargement des fichiers un par un...")

        with tqdm(total=total_files, desc="Téléchargement", unit="fichier") as pbar:
            for message in mp3_messages:
                await download_file(client, message, pbar, downloaded_files, DOWNLOAD_FOLDER)

        new_downloaded_files = get_downloaded_files(DOWNLOAD_FOLDER)
        new_files_count = len(new_downloaded_files) - len(downloaded_files)

        end_time = time.time()
        total_time = end_time - start_time

        print(f"\nTéléchargement terminé!")
        print(f"- Fichiers déjà présents: {len(downloaded_files)}")
        print(f"- Nouveaux fichiers téléchargés: {new_files_count}")
        print(f"- Total des fichiers: {len(new_downloaded_files)}")
        print(f"- Temps total: {total_time:.1f} secondes")
        if new_files_count > 0:
            print(f"- Vitesse moyenne: {new_files_count/total_time:.1f} fichiers/seconde")

        await client.disconnect()

    except Exception as e:
        print("\nUne erreur s'est produite!")
        print("Détails de l'erreur:")
        print(traceback.format_exc())
        print("\nVérifiez que vous avez bien rempli le fichier config.py et que les dépendances sont installées (pip install -r requirements.txt)")
    
    print("\nAppuyez sur Entrée pour fermer...")
    input()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print("\nUne erreur critique s'est produite!")
        print("Détails de l'erreur:")
        print(traceback.format_exc())
        print("\nAppuyez sur Entrée pour fermer...")
        input() 