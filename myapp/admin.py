from django.contrib import admin
from .models import User, TheLoai, DienVien, Movie, DanhGia, LichSuXem
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User



# 🟢 Quản lý User
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'avatar', 'ngay_sinh', 'is_active', 'is_staff')  # Không có 'username'
    search_fields = ('email', 'ngay_sinh')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Thông tin cá nhân', {'fields': ('avatar', 'ngay_sinh')}),
        ('Quyền hạn', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_active', 'is_staff')}
        ),
    )


# 🟢 Quản lý Thể Loại
@admin.register(TheLoai)
class TheLoaiAdmin(admin.ModelAdmin):
    list_display = ('id', 'ten')
    search_fields = ('ten',)

# 🟢 Quản lý Diễn Viên
@admin.register(DienVien)
class DienVienAdmin(admin.ModelAdmin):
    list_display = ('id', 'ten')
    search_fields = ('ten',)

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('maphim', 'id', 'ten_phim', 'danh_sach_the_loai', 'dao_dien', 'ngay_phat_hanh', 'thoi_luong', 'trang_thai')
    search_fields = ('ten_phim', 'dao_dien', 'dien_vien__ten')
    list_filter = ('ngay_phat_hanh', 'trang_thai')
    ordering = ['-ngay_phat_hanh']

    def danh_sach_the_loai(self, obj):
        return ", ".join([tl.ten for tl in obj.the_loai.all()])
    danh_sach_the_loai.short_description = "Thể Loại"


# 🟢 Quản lý Đánh Giá
@admin.register(DanhGia)
class DanhGiaAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phim', 'diem', 'ngay_danh_gia')
    search_fields = ('user__username', 'phim__ten_phim')
    list_filter = ('diem', 'ngay_danh_gia')

# 🟢 Quản lý Lịch Sử Xem
@admin.register(LichSuXem)
class LichSuXemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phim', 'thoi_gian_bat_dau', 'thoi_gian_ket_thuc')
    search_fields = ('user__username', 'phim__ten_phim')
    list_filter = ('thoi_gian_bat_dau', 'thoi_gian_ket_thuc')
