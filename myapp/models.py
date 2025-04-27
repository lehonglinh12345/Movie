from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import TextChoices
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.templatetags.static import static
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
)
import re
import requests
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Tạo user bình thường"""
        if not email:
            raise ValueError("Người dùng phải có địa chỉ email")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Tạo superuser"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Email")
    fullname = models.CharField(max_length=255, verbose_name="Họ và tên", blank=True, null=True)  
    avatar = models.ImageField(upload_to="users/avatars/",default='img/logo.jpg', null=True, blank=True, verbose_name="Ảnh đại diện")
    ngay_sinh = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    is_staff = models.BooleanField(default=False, verbose_name="Nhân viên")

    groups = models.ManyToManyField(Group, related_name="user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="user_permissions", blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'  # Đặt email làm username
    REQUIRED_FIELDS = []  # Không cần username

    def __str__(self):
        return self.email


class TheLoai(models.Model):
    ten = models.CharField(max_length=100, unique=True, verbose_name="Tên thể loại")

    class Meta:
        verbose_name_plural = "Thể loại"

    def __str__(self):
        return self.ten


class DienVien(models.Model):
    ten = models.CharField(max_length=200, verbose_name="Tên diễn viên")

    def __str__(self):
        return self.ten

class TrangThaiPhim(TextChoices):
    SAP_CHIEU = "sap_chieu", "Sắp Chiếu"
    DANG_CHIEU = "dang_chieu", "Đang Chiếu"
    DA_KET_THUC = "da_ket_thuc", "Đã Kết Thúc"

class Movie(models.Model):
    maphim = models.CharField(max_length=20, unique=True, verbose_name="Mã phim", null=True, blank=True)
    ten_phim = models.CharField(max_length=200, verbose_name="Tên phim")
    tmdb_id = models.PositiveIntegerField(unique=True, null=True, blank=True, verbose_name="TMDb ID")
    video_url = models.URLField(null=True, blank=True, verbose_name="Link video") 
    the_loai = models.ManyToManyField(TheLoai, related_name="movies", verbose_name="Thể loại")
    mo_ta = models.TextField(verbose_name="Mô tả phim")
    dao_dien = models.CharField(max_length=200, verbose_name="Đạo diễn")
    dien_vien = models.ManyToManyField(DienVien, related_name="movies", verbose_name="Diễn viên")
    ngay_phat_hanh = models.DateField(null=True, blank=True, verbose_name="Ngày phát hành")
    thoi_luong = models.PositiveIntegerField(help_text="Thời lượng phim tính bằng phút", verbose_name="Thời lượng")
    anh_bia = models.ImageField(upload_to="phim/anhbia/", null=True, blank=True, verbose_name="Ảnh bìa")
    trang_thai = models.CharField(
        max_length=20,
        choices=TrangThaiPhim.choices,
        default=TrangThaiPhim.SAP_CHIEU,
        verbose_name="Trạng thái"
    )
    luot_xem = models.PositiveIntegerField(default=0, verbose_name="Lượt xem")

    
    class Meta:
        ordering = ['-ngay_phat_hanh']

    def __str__(self):
        return f"{self.maphim} - {self.ten_phim}"
    

    def update_luot_xem(self):
        self.luot_xem = self.watch_history.count()  # Dựa vào related_name của LichSuXem
        self.save(update_fields=['luot_xem'])


    def anh_bia_url(self):
        if self.anh_bia and hasattr(self.anh_bia, 'url'):
            return self.anh_bia.url
        return static('myapp/img/logo.jpg') 


import re   

def get_embed_url(self):
    """Chuyển đổi link YouTube thành dạng nhúng."""
    if self.video_url:
        youtube_patterns = [
            (r"watch\?v=([\w-]+)", r"embed/\1"),   # Dạng: youtube.com/watch?v=abc123
            (r"youtu\.be/([\w-]+)", r"youtube.com/embed/\1")  # Dạng: youtu.be/abc123
        ]
        for pattern, replacement in youtube_patterns:
            self.video_url = re.sub(pattern, replacement, self.video_url)
    return self.video_url




class DanhGia(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews", verbose_name="Người dùng")
    phim = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews", verbose_name="Phim")
    diem = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)], verbose_name="Điểm đánh giá")
    binh_luan = models.TextField(verbose_name="Bình luận")
    ngay_danh_gia = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đánh giá")
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'phim'], name="unique_review_per_user")
        ]
        ordering = ['-ngay_danh_gia']

    def __str__(self):
        return f"{self.user.email} - {self.phim.ten_phim} ({self.diem})"

class LichSuXem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watch_history", verbose_name="Người dùng")
    phim = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="watch_history", verbose_name="Phim")
    thoi_gian_bat_dau = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian bắt đầu")
    thoi_gian_ket_thuc = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian kết thúc")

    def __str__(self):
        return f"{self.user.email} đã xem {self.phim.ten_phim}"
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.phim.update_luot_xem()


