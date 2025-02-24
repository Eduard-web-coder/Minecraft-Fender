# Minecraft-Fender

## Описание

**Minecraft-Fender** – это утилита для поиска серверов Minecraft. Приложение позволяет сканировать локальную сеть, заданный диапазон IP-адресов, а также использовать IP-адреса из файла `IP.ini` для поиска активных серверов Minecraft. Программа отображает информацию о найденных серверах, включая количество онлайн игроков, максимальное количество игроков и версию сервера. Также список игроков каждого найденного сервера сохраняется в файл `server_players.txt`.

## Функциональные возможности

- **Сканирование сети:** Автоматический поиск серверов в локальной сети.
- **Сканирование по диапазону:** Возможность задать диапазон IP-адресов для поиска серверов в интернете.
- **Использование IP из файла:** Чтение IP-адресов из файла `IP.ini` для сканирования.
- **Информация о сервере:** Получение данных о текущем количестве игроков, максимальном числе игроков и версии сервера.
- **Сохранение данных:** Запись списка игроков на сервере в файл `server_players.txt`.
- **Графический интерфейс:** Удобное управление утилитой через приложение на PyQt5.
- **Получение IP:** Возможность узнать подробную информацию о локальном IP через создание и запуск BAT-файла.

## Установка

1. **Клонируйте репозиторий:**

   ```bash
   git clone https://github.com/Eduard-web-coder/Minecraft-Fender.git
