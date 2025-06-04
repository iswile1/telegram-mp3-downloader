import os
import asyncio
import re
from tqdm import tqdm
import time
import traceback
from datetime import datetime
import sys
from telethon import TelegramClient, events
import random
import json

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

def save_progress(channel_name, downloaded_files):
    try:
        progress_file = f"progress_{channel_name}.json"
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(list(downloaded_files), f)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la progression: {str(e)}")

def load_progress(channel_name):
    try:
        progress_file = f"progress_{channel_name}.json"
        if os.path.exists(progress_file):
            with open(progress_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()
    except Exception as e:
        print(f"Erreur lors du chargement de la progression: {str(e)}")
        return set()

def reset_progress(channel_name):
    try:
        progress_file = f"progress_{channel_name}.json"
        if os.path.exists(progress_file):
            os.remove(progress_file)
            print(f"Fichier de progression {progress_file} supprimé")
    except Exception as e:
        print(f"Erreur lors de la suppression du fichier de progression: {str(e)}")

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

def get_channel_folder_name(channel_username):
    # Nettoyer le nom du canal pour créer un nom de dossier valide
    clean_name = re.sub(r'[<>:"/\\|?*]', '', channel_username)
    clean_name = clean_name.replace('@', '')
    return clean_name

def get_downloaded_files(download_folder):
    try:
        if not os.path.exists(download_folder):
            return set()
        
        # Récupérer tous les fichiers MP3
        files = {f for f in os.listdir(download_folder) if f.endswith('.mp3')}
        base_names = set()
        for file in files:
            # Enlever les numéros de doublons (_1, _2, etc.)
            base_name = re.sub(r'_\d+\.mp3$', '.mp3', file)
            base_names.add(base_name)
        
        return base_names
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

async def download_file(client, message, pbar, downloaded_files, download_folder, channel_name):
    try:
        file_name = get_file_name(message)
        base_name = re.sub(r'_\d+\.mp3$', '.mp3', file_name)
        
        if base_name in downloaded_files:
            pbar.update(1)
            pbar.set_description(f"Déjà téléchargé: {file_name}")
            return True

        # Ajouter un délai aléatoire pour éviter la détection
        await asyncio.sleep(random.uniform(0.5, 2.0))

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
            
            downloaded_files.add(base_name)
            save_progress(channel_name, downloaded_files)
            
            pbar.update(1)
            pbar.set_description(f"Téléchargé: {file_name}")
            return True
        return False

    except Exception as e:
        print(f"\nErreur lors du téléchargement de {file_name}: {str(e)}")
        return False

async def main():
    try:
        print_info()
        print("Démarrage du script...")
        start_time = time.time()
        
        # Charger la configuration
        from config import API_ID, API_HASH, PHONE_NUMBER, CHANNEL_LINK, SESSION_NAME
        
        channel_username = extract_channel_username(CHANNEL_LINK)
        channel_folder = get_channel_folder_name(channel_username)
        download_folder = os.path.join('telegram_mp3s', channel_folder)
        
        # Vérifier si le dossier existe et s'il contient des fichiers
        if os.path.exists(download_folder):
            files = [f for f in os.listdir(download_folder) if f.endswith('.mp3')]
            if not files:
                print(f"Dossier {download_folder} vide, réinitialisation de la progression...")
                reset_progress(channel_folder)
        else:
            print(f"Création du dossier {download_folder}...")
            os.makedirs(download_folder)
            reset_progress(channel_folder)
        
        print(f"Téléchargement des fichiers dans {download_folder}")
        
        # Charger la progression précédente et les fichiers existants
        downloaded_files = load_progress(channel_folder)
        existing_files = get_downloaded_files(download_folder)
        
        # Si aucun fichier n'existe physiquement, réinitialiser la progression
        if not existing_files and downloaded_files:
            print("Aucun fichier trouvé dans le dossier, réinitialisation de la progression...")
            reset_progress(channel_folder)
            downloaded_files = set()
        
        # Fusionner les deux ensembles pour avoir une liste complète
        downloaded_files.update(existing_files)
        
        if downloaded_files:
            print(f"Reprise du téléchargement avec {len(downloaded_files)} fichiers déjà téléchargés")
            print("Fichiers déjà téléchargés:")
            for file in sorted(downloaded_files):
                print(f"- {file}")
        
        # Connexion à Telegram
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH, **CLIENT_SETTINGS)
        await client.start(phone=PHONE_NUMBER)
        
        channel = await client.get_entity(channel_username)
        messages = await client.get_messages(channel, limit=None)
        
        mp3_messages = []
        for message in messages:
            if message.media and hasattr(message.media, 'document'):
                if message.media.document.mime_type == 'audio/mpeg':
                    mp3_messages.append(message)
        
        # Filtrer les messages déjà téléchargés
        remaining_messages = []
        for message in mp3_messages:
            file_name = get_file_name(message)
            base_name = re.sub(r'_\d+\.mp3$', '.mp3', file_name)
            if base_name not in downloaded_files:
                remaining_messages.append(message)
        
        print(f"\n{len(remaining_messages)} nouveaux fichiers à télécharger")
        
        with tqdm(total=len(remaining_messages), desc="Téléchargement", unit="fichier") as pbar:
            for message in remaining_messages:
                await download_file(client, message, pbar, downloaded_files, download_folder, channel_folder)
                # Pause aléatoire entre les téléchargements
                await asyncio.sleep(random.uniform(1, 3))
        
        await client.disconnect()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\nTéléchargement terminé!")
        print(f"- Fichiers déjà téléchargés: {len(downloaded_files) - len(remaining_messages)}")
        print(f"- Nouveaux fichiers téléchargés: {len(remaining_messages)}")
        print(f"- Total des fichiers: {len(downloaded_files)}")
        print(f"- Temps total: {total_time:.1f} secondes")
        
    except Exception as e:
        print("\nUne erreur s'est produite!")
        print("Détails de l'erreur:")
        print(traceback.format_exc())
    
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