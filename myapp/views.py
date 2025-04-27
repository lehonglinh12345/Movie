from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Movie, User, TheLoai, LichSuXem

# Trang chủ và giới thiệu
from django.db.models import Count
from django.shortcuts import render
from .models import Movie
import requests

def lay_trailer_tmdb(movie_id):
    API_KEY = 'c53ff05a507beb95ce9c55f89908d88d'
    url = f'https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}&language=vi-VN'
    response = requests.get(url)
    data = response.json()

    for video in data.get('results', []):
        if video['site'] == 'YouTube' and video['type'] == 'Trailer':
            return f"https://www.youtube.com/embed/{video['key']}"
    return None

def home(request):
    # Lấy phim mới nhất
    danh_sach_phim = Movie.objects.order_by('-ngay_phat_hanh')[:10]  # Lấy 10 phim mới nhất

    # Lấy phim yêu thích (theo số lượng bình luận, nếu bạn có model bình luận)
    phim_yeu_thich = Movie.objects.annotate(num_reviews=Count('reviews')).order_by('-num_reviews')[:4]

    phim_hay_nhat = phim_yeu_thich.all()[:3]  # Trả về QuerySet thay vì list
    phim_dang_chieu = Movie.objects.filter(trang_thai='dang_chieu')[:10]
    phim_sap_chieu = Movie.objects.filter(trang_thai='sap_chieu')[:10]

    for phim in phim_sap_chieu:
        phim.video_url = lay_trailer_tmdb(phim.tmdb_id)  # đảm bảo model Movie có trường tmdb_id

    recommended = get_recommendations_for_user(request.user)
    context = {
        'danh_sach_phim': danh_sach_phim,
        'phim_noi_bat': danh_sach_phim,
        'phim_yeu_thich': phim_yeu_thich,
        'phim_hay_nhat': phim_hay_nhat,
        'phim_dang_chieu': phim_dang_chieu,
        'phim_sap_chieu': phim_sap_chieu,
        

        'recommended_movies': recommended
    }

    return render(request, 'myapp/pages/home.html', context)




def dieukhoan(request):
    return render(request, "myapp/quydinh/dieukhoan.html")
def quyen(request):
    return render(request, "myapp/quydinh/quyen.html")
def gioithieu(request):
    return render(request, 'myapp/quydinh/gioithieu.html')

def home1(request):
    return render(request, "myapp/pages/home1.html")

# Chi tiết phim
def onepiece(request):
    movie = get_object_or_404(Movie, ten_phim="One Piece") 
    return render(request, 'myapp/pages/phim/onepiece.html', {'movie': movie})

def kime(request):
    movie = get_object_or_404(Movie, ten_phim="Kimetsu no Yaiba") 
    return render(request, 'myapp/pages/phim/kime.html', {'movie': movie})

def natra(request):
    movie = get_object_or_404(Movie, ten_phim="NaTra2") 
    return render(request, 'myapp/pages/phim/natra.html', {'movie': movie})


from django.shortcuts import render, get_object_or_404
from .models import Movie


@login_required
def chitietphim(request, maphim):
    movie = get_object_or_404(Movie, maphim=maphim)
    # Lấy gợi ý phim (vd: cùng thể loại, cùng đạo diễn,...)
    recommended_movies = Movie.objects.filter(the_loai__in=movie.the_loai.all()).exclude(id=movie.id).distinct()[:4]


    # Lưu lịch sử xem
    lich_su, created = LichSuXem.objects.get_or_create(
        user=request.user,
        phim=movie,  # 👉 Lưu ý: trường trong model là `phim`, không phải `movie`
        defaults={'thoi_gian_bat_dau': now()}
    )
    if not created:
        lich_su.thoi_gian_bat_dau = now()
        lich_su.save()
    # Cập nhật lượt xem
    movie.update_luot_xem()
    video_embed = get_video_embed_url(movie.video_url)

    return render(request, 'myapp/pages/chitietphim.html', {
        'movie': movie,
        "recommended_movies": recommended_movies,
        'video_embed': video_embed
    })


# Chức năng đăng nhập
def login_view(request):   
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Email hoặc mật khẩu không đúng!')
            return render(request, 'myapp/log/login.html', {'email': email})

    return render(request, 'myapp/log/login.html')

@login_required
def profile(request):
    return render(request, "myapp/log/profile.html")

# Chức năng tìm kiếm phim
def search_movies(request):
    query = request.GET.get("q", "").strip()
    genre = request.GET.get("genre", "").strip()
    movies = Movie.objects.all()

    if query:
        movies = movies.filter(ten_phim__icontains=query)
    if genre:
        movies = movies.filter(the_loai__ten__icontains=genre)

    return render(request, "myapp/search/search_results.html", {"movies": movies.distinct(), "query": query, "genre": genre})

# Chức năng xem phim
@login_required
def xem_phim(request, id):
    movie = get_object_or_404(Movie, id=id)
    return render(request, 'myapp/xem_phim.html', {'movie': movie})


@login_required
def lich_su_xem(request):
    lich_su = LichSuXem.objects.filter(user=request.user).select_related('phim').order_by('-thoi_gian_bat_dau')
    return render(request, 'myapp/pages/lich_su_xem.html', {'lich_su': lich_su})
# Cập nhật thông tin cá nhân
@csrf_exempt
@login_required
def update_fullname(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_fullname = data.get("fullname")
            user = request.user
            user.fullname = new_fullname
            user.save()
            return JsonResponse({"success": True, "fullname": new_fullname})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})





from django.shortcuts import render, get_object_or_404
from .models import TheLoai, Movie

def the_loai(request, ten):
    the_loai = get_object_or_404(TheLoai, ten=ten)
    movies = Movie.objects.filter(the_loai=the_loai)
    return render(request, 'myapp/pages/the_loai.html', {'the_loai': the_loai, 'movies': movies})







import re

def get_video_embed_url(url):
    if not url:
        return None
    
    # Kiểm tra nếu URL là YouTube URL chuẩn (watch?v=)
    if "watch?v=" in url:
        video_id = url.split("watch?v=")[-1].split("&")[0]  # Lấy phần ID và loại bỏ các tham số phụ
        return f"https://www.youtube.com/embed/{video_id}"
    
    # Kiểm tra nếu URL là YouTube URL dạng rút gọn (youtu.be/)
    elif "youtu.be/" in url:
        video_id = url.split("/")[-1].split("?")[0]  # Tách ID video và loại bỏ các tham số
        # Kiểm tra nếu video ID hợp lệ (chỉ chứa ký tự hợp lệ của YouTube)
        if re.match(r'^[A-Za-z0-9_-]+$', video_id):
            return f"https://www.youtube.com/embed/{video_id}"
        else:
            return None  # Nếu ID không hợp lệ thì trả về None
    
    # Nếu không phải URL YouTube hợp lệ
    return None


from .models import TheLoai

def danh_sach_the_loai(request):
    return {'categories': TheLoai.objects.all()}


# myapp/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import User

@login_required
def profile(request):
    user = request.user
    if request.method == 'POST' and 'avatar' in request.FILES:
        user.avatar = request.FILES['avatar']
        user.save()
        return JsonResponse({'success': True, 'avatar_url': user.avatar.url})
    return render(request, 'myapp/log/profile.html', {'user': user})

@login_required
def update_avatar(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        new_fullname = data.get('fullname')
        user = request.user
        user.fullname = new_fullname
        user.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def phim_sap_chieu(request):
    upcoming_movies = Movie.objects.filter(trang_thai='Sắp Chiếu')  

    # 🛠 In log để kiểm tra dữ liệu
    print("🔥 DEBUG: Số lượng phim sắp chiếu:", upcoming_movies.count())
    for movie in upcoming_movies:
        print(f"🎬 {movie.ten_phim} - {movie.trang_thai}")

    context = {'upcoming_movies': upcoming_movies}
    return render(request, 'myapp/pages/home1.html', context)


from django.shortcuts import render
from .models import Movie

def upcoming_movies(request):
    # Lọc phim có trạng thái "Sắp Chiếu"
    movies = Movie.objects.filter(trang_thai="sap_chieu").order_by('ngay_phat_hanh')
    
    return render(request, 'phim/home1.html', {'movies': movies})


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    the_loai_list = movie.the_loai.all()  # Lấy tất cả thể loại của phim này
    similar_movies = Movie.objects.filter(the_loai__in=the_loai_list).exclude(id=movie.id).distinct()[:5]
    
    return render(request, 'myapp/pages/phim/movie_detail.html', {
        'movie': movie,
        'similar_movies': similar_movies,
    })
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Movie, DanhGia
from django.http import HttpResponseForbidden
from django.utils import timezone 


@login_required
def movie_review(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == "POST":
        diem = request.POST.get('diem')
        binh_luan = request.POST.get('binh_luan')

        try:
            diem = float(diem)
            if not (0 <= diem <= 10):
                messages.error(request, "Điểm đánh giá phải từ 0 đến 10.")
                return redirect(request.META.get('HTTP_REFERER', '/'))
        except (ValueError, TypeError):
            messages.error(request, "Điểm đánh giá không hợp lệ.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        if not binh_luan:
            messages.error(request, "Bình luận không được để trống.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Tìm đánh giá cũ nếu có
        danh_gia = DanhGia.objects.filter(user=request.user, phim=movie).first()

        if danh_gia:
            # Cập nhật nếu đã tồn tại
            danh_gia.diem = diem
            danh_gia.binh_luan = binh_luan
            danh_gia.ngay_danh_gia = timezone.now()
            danh_gia.save()
        else:
            # Tạo mới nếu chưa có
            DanhGia.objects.create(
                user=request.user,
                phim=movie,
                diem=diem,
                binh_luan=binh_luan,
                ngay_danh_gia=timezone.now()
            )

        messages.success(request, "Đánh giá của bạn đã được lưu!")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return render(request, 'myapp/home.html', {'movie': movie})



from django.shortcuts import render, get_object_or_404
from .models import Movie, TrangThaiPhim
from .recommendations import get_recommendations_for_user, get_similar_movies

def recommended_movies_view(request):
    user = request.user
    if user.is_authenticated:
        recommended_movies = get_recommendations_for_user(user.id, top_n=5)
    else:
        recommended_movies = Movie.objects.order_by('-ngay_phat_hanh')[:5]

    return render(request, 'myapp/pages/recommended.html', {
        'recommended_movies': recommended_movies
    })

def movie_detail_view(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    similar_movies = get_similar_movies(movie_id, top_n=5)

    return render(request, 'myapp/pages/movie_detail.html', {
        'movie': movie,
        'similar_movies': similar_movies
    })

def recommend_movies(request):
    recommended_movies = []
    message = ""

    if request.user.is_authenticated:

        recommended_movies = get_recommendations_for_user(request.user.id, top_n=3)
        message = "Phim gợi ý cho bạn:" if recommended_movies.exists() else "Chưa có gợi ý, xem phim phổ biến:"
    else:
        recommended_movies = Movie.objects.order_by('-ngay_phat_hanh')[:5]
        message = "Đăng nhập để nhận gợi ý cá nhân hóa:"

    return render(request, 'myapp/recommended.html', {
        'recommended_movies': recommended_movies,
        'message': message,
    })

from .recommendations import get_recommendations_for_user
from .recommendations import get_recommended_movies
from django.shortcuts import render
from .models import Movie, DanhGia

def get_recommendations_for_user(user, limit=5):
    if not user.is_authenticated:
        return Movie.objects.order_by('?')[:limit]

    # Lấy danh sách ID các phim người dùng đã đánh giá cao
    high_rated_movie_ids = DanhGia.objects.filter(user=user, diem__gte=7).values_list('phim', flat=True)

    if not high_rated_movie_ids:
        return Movie.objects.order_by('?')[:limit]

    # Lấy thể loại phim người dùng đánh giá cao
    liked_genres = Movie.objects.filter(id__in=high_rated_movie_ids).values_list('the_loai', flat=True)

    # Gợi ý phim cùng thể loại, chưa được người dùng đánh giá
    return Movie.objects.filter(
        the_loai__in=liked_genres
    ).exclude(
        reviews__user=user
    ).distinct()[:limit]




from django.http import JsonResponse
from django.core import serializers

def load_reviews(request, movie_id):
    page = int(request.GET.get('page', 1))
    per_page = 5
    start = (page - 1) * per_page
    end = start + per_page

    reviews = DanhGia.objects.filter(phim_id=movie_id).order_by('-ngay_danh_gia')[start:end]

    data = []
    for review in reviews:
        data.append({
            'username': review.user.get_full_name() or review.user.email,
            'is_owner': review.user == request.user,
            'avatar': review.user.avatar.url if review.user.avatar else '/static/myapp/img/default_avatar.jpg',
            'ngay_danh_gia': review.ngay_danh_gia.strftime("%d/%m/%Y %H:%M"),
            'diem': review.diem,
            'binh_luan': review.binh_luan,
        })

    return JsonResponse({'reviews': data, 'has_more': DanhGia.objects.filter(phim_id=movie_id).count() > end})
