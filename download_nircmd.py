import urllib.request
import os

def download_nircmd():
    """Скачивает nircmd.exe с официального сайта"""
    url = "https://www.nirsoft.net/utils/nircmd.exe"
    filename = "nircmd.exe"
    
    if os.path.exists(filename):
        print(f"Файл {filename} уже существует")
        return
    
    try:
        print(f"Скачиваю {filename}...")
        urllib.request.urlretrieve(url, filename)
        print(f"✅ {filename} успешно скачан!")
    except Exception as e:
        print(f"❌ Ошибка при скачивании: {e}")
        print("Пожалуйста, скачайте nircmd.exe вручную с https://www.nirsoft.net/utils/nircmd.html")

if __name__ == "__main__":
    download_nircmd() 