from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Book, UserBook
import requests
import json
from django.db import IntegrityError
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q

@login_required
def home(request):
    """
    ホーム画面ビュー。
    ログインユーザーの本棚にある「読んだ本」と「積読」を表示する。
    """
    sort_by = request.GET.get('sort', 'added_date')  # 'added_at'を'added_date'に修正
    
    user_books = UserBook.objects.filter(user=request.user)
    
    if sort_by == 'title':
        read_books = user_books.filter(status='read').order_by('book__title')
        reading_books = user_books.filter(status='reading').order_by('book__title')
    elif sort_by == 'author':
        read_books = user_books.filter(status='read').order_by('book__author')
        reading_books = user_books.filter(status='reading').order_by('book__author')
    else:
        read_books = user_books.filter(status='read').order_by('-added_date')
        reading_books = user_books.filter(status='reading').order_by('-added_date')

    return render(request, 'books/home.html', {
        'read_books': read_books,
        'reading_books': reading_books,
        'current_sort': sort_by,
    })

@login_required
def wishlist(request):
    """
    読みたいリストビュー。
    ログインユーザーの本棚にある「読みたい」本を表示する。
    """
    sort_by = request.GET.get('sort', 'added_date') # 'added_at'を'added_date'に修正

    wishlist_books_query = UserBook.objects.filter(user=request.user, status='wishlist')

    if sort_by == 'title':
        wishlist_books = wishlist_books_query.order_by('book__title')
    elif sort_by == 'author':
        wishlist_books = wishlist_books_query.order_by('book__author')
    else:
        wishlist_books = wishlist_books_query.order_by('-added_date')

    return render(request, 'books/wishlist.html', {
        'wishlist_books': wishlist_books,
        'current_sort': sort_by,
    })

def search(request):
    query = request.GET.get('q', '')
    books = []
    
    registered_books_status = {}
    if request.user.is_authenticated:
        registered_books = UserBook.objects.filter(user=request.user).select_related('book')
        for user_book in registered_books:
            if user_book.book.isbn:
                registered_books_status[user_book.book.isbn] = user_book.status

    if query:
        api_url = f"https://www.googleapis.com/books/v1/volumes?q=inauthor:{query}&maxResults=40&orderBy=relevance"
        response = requests.get(api_url, timeout=5)
        data = response.json()
        
        if not data.get('items', []):
            api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=40&orderBy=relevance"
            response = requests.get(api_url, timeout=5)
            data = response.json()
            
        try:
            response.raise_for_status()

            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                industry_identifiers = volume_info.get('industryIdentifiers', [])
                
                isbn = 'N/A'
                if industry_identifiers:
                    for identifier in industry_identifiers:
                        if identifier.get('type') == 'ISBN_13' or identifier.get('type') == 'ISBN_10':
                            isbn = identifier.get('identifier')
                            break
                
                book_data = {
                    'title': volume_info.get('title', 'N/A'),
                    'author': ', '.join(volume_info.get('authors', ['著者不明'])),
                    'isbn': isbn,
                    'thumbnail_url': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                    'registered_status': registered_books_status.get(isbn, None)
                }
                if book_data['isbn'] != 'N/A':
                    books.append(book_data)

        except requests.exceptions.RequestException as e:
            print(f"APIリクエストに失敗しました: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"APIレスポンスの解析に失敗しました: {e}")
            
    return render(request, 'books/search.html', {'books': books, 'query': query})

@require_POST
@login_required
def add_book_api(request):
    try:
        data = json.loads(request.body)
        isbn = data.get('isbn')
        title = data.get('title')
        author = data.get('author')
        thumbnail_url = data.get('thumbnail_url')
        status = data.get('status')

        if not isbn or isbn == 'N/A':
            return JsonResponse({'success': False, 'message': 'Invalid ISBN'}, status=400)

        book, created = Book.objects.get_or_create(
            isbn=isbn,
            defaults={
                'title': title,
                'author': author,
                'thumbnail_url': thumbnail_url,
            }
        )
        
        user_book, user_book_created = UserBook.objects.get_or_create(
            user=request.user,
            book=book,
            status=status
        )

        if not user_book_created:
            return JsonResponse({'success': True, 'message': 'Already added'}, status=200)

        return JsonResponse({'success': True, 'message': 'Book added successfully'}, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def book_detail(request, pk):
    """
    本棚に登録された本の詳細ページを表示するビュー。
    """
    user_book = get_object_or_404(UserBook, pk=pk, user=request.user)
    book = user_book.book

    related_books = []
    query = book.author
    if query:
        api_url = f"https://www.googleapis.com/books/v1/volumes?q=inauthor:{query}&maxResults=20"
        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            data = response.json()

            registered_books_status = {}
            if request.user.is_authenticated:
                registered_books_for_user = UserBook.objects.filter(user=request.user).select_related('book')
                for ub in registered_books_for_user:
                    if ub.book.isbn:
                        registered_books_status[ub.book.isbn] = ub.status

            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                industry_identifiers = volume_info.get('industryIdentifiers', [])
                
                isbn = 'N/A'
                if industry_identifiers:
                    for identifier in industry_identifiers:
                        if identifier.get('type') == 'ISBN_13' or identifier.get('type') == 'ISBN_10':
                            isbn = identifier.get('identifier')
                            break
                
                related_book_data = {
                    'title': volume_info.get('title', 'N/A'),
                    'author': ', '.join(volume_info.get('authors', ['著者不明'])),
                    'isbn': isbn,
                    'thumbnail_url': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                    'registered_status': registered_books_status.get(isbn, None)
                }
                if isbn != book.isbn and related_book_data['registered_status'] is None and isbn != 'N/A':
                    related_books.append(related_book_data)

        except requests.exceptions.RequestException as e:
            print(f"APIリクエストに失敗しました: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"APIレスポンスの解析に失敗しました: {e}")

    return render(request, 'books/book_detail.html', {
        'user_book': user_book,
        'book': book,
        'related_books': related_books,
    })

@login_required
def delete_book(request, pk):
    user_book = get_object_or_404(UserBook, pk=pk, user=request.user)
    user_book.delete()
    return redirect('home')