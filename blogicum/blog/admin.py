from django.contrib import admin

from .models import Category, Location, Post


class BlogAdmin(admin.ModelAdmin):
    """Административная модель для управления постами."""
    list_display = (
        'title',
        'author',
        'pub_date',
        'category',
        'is_published',
        'text',
    )


admin.site.register(Post, BlogAdmin)
admin.site.register(Category)
admin.site.register(Location)
