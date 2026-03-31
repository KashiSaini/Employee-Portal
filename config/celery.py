import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  #give all setting  access to celery

app = Celery("config")                                              #create a celery instance with the name of the project name source
app.config_from_object("django.conf:settings", namespace="CELERY")  #tell celery to read all celery related setting with the prefix CELERY_ from django settings
app.autodiscover_tasks()                                            #tell celery to look for tasks.py in all installed apps
