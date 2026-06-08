from fastapi import FastAPI

fastapi_app = FastAPI(title="FastAPI + Django Demo")

@fastapi_app.get("/books")
def get_books():
    from myapp.models import Book
    from django.forms.models import model_to_dict
    return [model_to_dict(book) for book in Book.objects.all()]
