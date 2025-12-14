from django.contrib import admin
from .models import Category, Location, Post, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'pub_date', 'is_published', 'category')
    list_filter = ('is_published', 'category', 'pub_date')
    search_fields = ('title', 'text')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'author__username')


admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
