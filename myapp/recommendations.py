import pandas as pd
import logging
from functools import lru_cache
from sklearn.metrics.pairwise import cosine_similarity
from .models import DanhGia, Movie

logger = logging.getLogger(__name__)

@lru_cache(maxsize=128)
def get_recommendations_for_user(user_id, top_n=5):
    # Lấy dữ liệu đánh giá từ database
    ratings = DanhGia.objects.all().values('user_id', 'phim_id', 'diem')
    df = pd.DataFrame(ratings)

    if df.empty:
        # Nếu không có dữ liệu đánh giá, trả về phim mới nhất
        return Movie.objects.order_by('-ngay_phat_hanh')[:top_n]

    # Tạo bảng pivot: hàng là user, cột là phim, giá trị là điểm đánh giá
    pivot_table = df.pivot_table(index='user_id', columns='phim_id', values='diem').fillna(0)

    if user_id not in pivot_table.index:
        # Nếu user chưa có đánh giá, trả về phim mới nhất
        return Movie.objects.order_by('-ngay_phat_hanh')[:top_n]

    # Tính độ tương đồng giữa người dùng
    similarity_matrix = cosine_similarity(pivot_table)
    similarity_df = pd.DataFrame(similarity_matrix, index=pivot_table.index, columns=pivot_table.index)

    # Lấy danh sách người dùng tương tự
    similar_users = similarity_df[user_id].sort_values(ascending=False)[1:top_n+1]

    # Lấy danh sách phim đã xem
    watched_movies = df[df['user_id'] == user_id]['phim_id'].tolist()

    # Gợi ý phim dựa trên đánh giá của người dùng tương tự
    recommendations = {}
    for similar_user_id, similarity_score in similar_users.items():
        similar_user_ratings = df[df['user_id'] == similar_user_id]
        for _, row in similar_user_ratings.iterrows():
            phim_id = row['phim_id']
            if phim_id not in watched_movies:
                recommendations[phim_id] = recommendations.get(phim_id, 0) + row['diem'] * similarity_score

    # Sắp xếp phim theo điểm gợi ý
    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:top_n]
    recommended_movie_ids = [phim_id for phim_id, _ in sorted_recommendations]

    # Trả về danh sách phim
    return Movie.objects.filter(id__in=recommended_movie_ids)

def get_similar_movies(movie_id, top_n=3):
    try:
        logger.info(f"Đang tìm phim tương tự cho movie_id={movie_id}")
        data = DanhGia.objects.all().values('user_id', 'phim_id', 'diem')
        df = pd.DataFrame(data)

        if not df.empty:
            pivot = df.pivot_table(index='phim_id', columns='user_id', values='diem', aggfunc='mean').fillna(0)

            if movie_id in pivot.index:
                similarity_matrix = cosine_similarity(pivot)
                similarity_df = pd.DataFrame(similarity_matrix, index=pivot.index, columns=pivot.index)
                similar_movies = similarity_df[movie_id].sort_values(ascending=False)[1:top_n+1]
                similar_ids = [int(i) for i in similar_movies.index]
                movies = Movie.objects.filter(id__in=similar_ids).prefetch_related('the_loai', 'dien_vien')
                if movies.exists():
                    return movies

        current_movie = Movie.objects.filter(id=movie_id).first()
        if current_movie:
            the_loai_ids = current_movie.the_loai.values_list('id', flat=True)
            similar_movies = Movie.objects.filter(the_loai__id__in=the_loai_ids).exclude(id=movie_id).order_by('-luot_xem')[:top_n]
            if similar_movies.exists():
                return similar_movies

        fallback_movies = Movie.objects.exclude(id=movie_id).order_by('-luot_xem')[:top_n]
        return fallback_movies

    except Exception as e:
        logger.error(f"Lỗi trong get_similar_movies: {e}")
        return Movie.objects.order_by('-luot_xem')[:top_n]

def get_recommended_movies(user, limit=5):
    if not user.is_authenticated:
        return Movie.objects.order_by('-luot_xem')[:limit]

    high_rated_movie_ids = DanhGia.objects.filter(user=user, diem__gte=7).values_list('phim', flat=True)

    if not high_rated_movie_ids:
        return Movie.objects.order_by('-luot_xem')[:limit]

    liked_genres = Movie.objects.filter(id__in=high_rated_movie_ids).values_list('the_loai', flat=True)

    recommended = Movie.objects.filter(
        the_loai__in=liked_genres
    ).exclude(
        reviews__user=user
    ).distinct().order_by('-luot_xem')[:limit]

    return recommended