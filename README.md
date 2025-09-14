# Calendar Backend

## Overview
Backend for the interview project, built with **Django**, **Django REST Framework (DRF)** and **PostgreSQL**.  
Handles events, recurring rules (rrule), exceptions, and timezone-aware date operations.

## Architecture Decisions
- **views:** All main operations for this project. Seperated in **Event** and **Exceptions two parts**.
- **Time Handling:** All datetimes are stored in **UTC** with a **build zone info**. Occurrences are generated based on both UTC time and Build zone.
- **models** The data strcure
- **Serializers:** Used to validate input data and expose the correct fields to frontend.

## Assumptions, Trade-offs, Known Limitations
- **Single user** Only supports a single user scenario (no login/auth). As it's a interview project I think it's okay. For production line can just add access limit on backend, encybered account and password with generated token will be the first option I would use.
- **Exceptions:** Exceptions logic prioritizes “This time” over other ranges; multiple “future” or “all time” exceptions do not stack. It's the first time I do a calendar project. I tried to accumulate the effects brought by all exceptions at the first place. But found the data structure doesn't supply. If I really want to do in this way then I have to turn over the database. And I'm not sure if people are doing accumulation or in the way I'm doing now. It's not a better one with a poorer one, just options.

## What I’d Do Next With More Time
- Orgnize the code. Sorry for who has to review this. I know it's not very easily readable but not a really complex one too.
- Add access limit.
- More test cases. I didn't spend time on test cases. Just to show I can write it so I still put two cases there.


## Before you run
- Remember to change the DATABASES in my_calendar/settings.py to yours
- I suggest not to change the urls if they don't conflict with anything else you are running.
As it mathces my frontend. But do feel free to change, just don't forget to change it on frontend side then it's gonna be fine.

### run the code
```bash
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows (cmd):
venv\Scripts\activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
