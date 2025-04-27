from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.urls import path, include  # 
from .views import search_movies, lich_su_xem, xem_phim, the_loai,movie_review
from myapp.views import login_view
from django.views.generic import TemplateView
from .views import update_fullname
from django.contrib.auth import views as auth_views
from django.urls import path

urlpatterns = [
    
    path('', views.home, name='home'),
    path('accounts/', include('allauth.urls')),
    path("gioithieu/", views.gioithieu, name="gioithieu"),
    # path('phim/onepiece/', views.onepiece, name='onepiece'),
    # path('phim/kime/', views.kime, name='kime'),
    # path('phim/natra/', views.natra, name='natra'),

        # Giới thiệu và điều khoản
    path('gioithieu/', views.gioithieu, name='gioithieu'),
    path("dieukhoan/", views.dieukhoan, name="dieukhoan"),
    path("quyen/", views.quyen, name="quyen"),
    path('update-avatar/', views.update_avatar, name='update_avatar'),
    path('log/login/', login_view, name='login'),
    path('log/profile/', views.profile, name='profile'),
  
    path("search/", search_movies, name="search_movies"),
    path('lich-su-xem/', views.lich_su_xem, name='lich_su_xem'),
    path("update-fullname/", update_fullname, name="update_fullname"),
    path('the-loai/<str:ten>/', the_loai, name='the_loai'),
    path('chitietphim/<str:maphim>/', views.chitietphim, name='chitietphim'),
    path("phim/<int:movie_id>/review/", movie_review, name="movie_review"),
    # path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('recommend/', views.recommend_movies, name='recommend'),
    path('goi-y/', views.recommended_movies_view, name='recommended_movies'),   
    #  # Đăng nhập
    # path("accounts/login/", auth_views.LoginView.as_view(template_name="myapp/log/login.html"), name="login"),
    # # Đăng xuất
    # path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
