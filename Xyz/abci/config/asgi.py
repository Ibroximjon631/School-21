import os
import django
from django.core.asgi import get_asgi_application

from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

# Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()  #

django_asgi_app = get_asgi_application()

# FastAPI app
fastapi_app = FastAPI(title="FastAPI")

@fastapi_app.get("/books")
def get_books():
    from myapp.models import Book
    from django.forms.models import model_to_dict
    return [model_to_dict(book) for book in Book.objects.all()]



application = Starlette(routes=[
    Mount("/api", app=fastapi_app),          # FastAPI endpoints
    Mount("/static", app=StaticFiles(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "staticfiles")), name="static"),  # Static fayllar
    Mount("/", app=django_asgi_app),         # Django admin va sayt
])
