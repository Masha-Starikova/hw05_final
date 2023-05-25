# hw05_final

[![CI](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml)
# Yatube
Социальная сеть блогеров
### Описание 
Этот проект даёт возможность создавать страницы с публикациями личных дневников. Незарегистрированные пользователи могут заходить на чужие страницы, просматривать записи авторов. Реализована система регистрации и восстановления пароля. При регистрации автор может выбрать имя и уникальный адрес своей страницы. Зарегистрированные пользователи могут просматривать чужие записи, комментировать их, подписываться на понравившихся авторов, отписываться от авторов.
### Технологии
Python 3.7 
Django 2.2.19
### Запуск проекта
Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:Masha-Starikova/hw05_final.git
cd hw05_final 
``` 
Создать и активировать виртуальное окружение:
```
python3 -m venv venv 
source venv/scripts/activate
``` 
Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt 
``` 
Выполнить миграции:
```
python3 manage.py migrate
```
В папке с файлом manage.py выполнить команду: 
``` 
python3 manage.py runserver 
```
### Автор
Мария Старикова
