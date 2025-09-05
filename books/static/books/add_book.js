// books/static/books/add_book.js

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.add-book-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            const clickedButton = this;
            const status = clickedButton.getAttribute('data-status');
            const form = this.closest('form');

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const isbn = form.querySelector('input[name="isbn"]').value;
            const title = form.querySelector('input[name="title"]').value;
            const author = form.querySelector('input[name="author"]').value;
            const thumbnail_url = form.querySelector('input[name="thumbnail_url"]').value;

            // リクエストを送信する前にボタンを無効化
            clickedButton.disabled = true;
            clickedButton.innerText = '追加中...';

            fetch('/add_book_api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    isbn: isbn,
                    title: title,
                    author: author,
                    thumbnail_url: thumbnail_url,
                    status: status
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const statusTextMap = {
                        'read': '読んだ本に追加済み',
                        'reading': '積読に追加済み',
                        'wishlist': '読みたいに追加済み'
                    };
                    
                    clickedButton.innerText = statusTextMap[status];

                    // 成功した場合は、同じ本のすべてのボタンを無効化
                    clickedButton.closest('.d-grid').querySelectorAll('.add-book-btn').forEach(btn => {
                        btn.disabled = true;
                    });
                    
                } else {
                    alert(data.message);
                    // 失敗した場合、ボタンを元に戻す
                    clickedButton.disabled = false;
                    clickedButton.innerText = '再試行'; 
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('エラーが発生しました。');
                // 失敗した場合、ボタンを元に戻す
                clickedButton.disabled = false;
                clickedButton.innerText = '再試行';
            });
        });
    });
});