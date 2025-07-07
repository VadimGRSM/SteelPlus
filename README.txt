Installation

git clone https://github.com/VadimGRSM/SteelPlus.git
cd SteelPlus/SteelPlus
pip install -r requirements.txt


Launching

celery -A SteelPlus worker --pool=solo --loglevel=info

python manage.py runserver

