# ⚙️ Настройка Volume Control

## 📝 Конфигурационный файл

Программа использует файл `config.json` для настройки. Вы можете создать этот файл рядом с .exe файлом для изменения настроек.

### Пример config.json:
```json
{
    "hotkey": "f9",
    "low_volume": 0.2,
    "high_volume": 1.0,
    "app_name": "Discord.exe",
    "show_console": false
}
```

### Параметры:

- **hotkey** - Горячая клавиша (по умолчанию: "f9")
  - Примеры: "f9", "f10", "ctrl+f9", "alt+f9"
  
- **low_volume** - Громкость в пониженном состоянии (по умолчанию: 0.2 = 20%)
  - Значения от 0.0 до 1.0 (0% - 100%)
  
- **high_volume** - Громкость в восстановленном состоянии (по умолчанию: 1.0 = 100%)
  - Значения от 0.0 до 1.0 (0% - 100%)
  
- **app_name** - Имя процесса приложения (по умолчанию: "Discord.exe")
  - Примеры: "Discord.exe", "chrome.exe", "spotify.exe"
  
- **show_console** - Показывать ли консоль (по умолчанию: false)

## 🎯 Примеры конфигураций

### Для Discord с F10:
```json
{
    "hotkey": "f10",
    "low_volume": 0.1,
    "high_volume": 1.0,
    "app_name": "Discord.exe"
}
```

### Для Chrome с Ctrl+F9:
```json
{
    "hotkey": "ctrl+f9",
    "low_volume": 0.3,
    "high_volume": 0.8,
    "app_name": "chrome.exe"
}
```

### Для Spotify с Alt+F9:
```json
{
    "hotkey": "alt+f9",
    "low_volume": 0.15,
    "high_volume": 0.9,
    "app_name": "spotify.exe"
}
```

## 📁 Размещение файла

Поместите `config.json` в ту же папку, где находится `volume_keys.exe`.

## 🔄 Изменения в реальном времени

- Изменения в config.json применяются при следующем запуске программы
- Если config.json отсутствует, используются значения по умолчанию
- При ошибке в config.json программа продолжит работу с дефолтными настройками 