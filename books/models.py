from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

# 本の情報モデル
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=40, unique=True)
    published_date = models.DateField(null=True, blank=True)
    thumbnail_url = models.URLField(max_length=500, null=True, blank=True)
    def __str__(self):
        return self.title

# ユーザーの本棚モデル
class UserBook(models.Model):
    LIST_CHOICES = (
        ('read', '読んだ本'),
        ('reading', '積読'),
        ('wishlist', '読みたい'),
        
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=LIST_CHOICES)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book', 'status') # 重複登録を防ぐ

    def __str__(self):
        return f"{self.user.username}'s {self.book.title} ({self.status})"