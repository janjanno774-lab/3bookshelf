# books/urls.py
# ...
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('search/', views.search, name='search'),
    path('add_book_api/', views.add_book_api, name='add_book_api'),
    path('book_detail/<int:pk>/', views.book_detail, name='book_detail'),
    path('delete_book/<int:pk>/', views.delete_book, name='delete_book'),
]