from django.contrib import admin

from .models import Category, Location, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'location',
        'author',
        'text',
        'is_published',
        'pub_date',
    )
    list_editable = (
        'is_published',
        'category'
    )
    search_fields = ('author',)
    list_filter = ('category',)
    list_display_links = ('title',)


admin.site.register(Category)
admin.site.register(Post, PostAdmin)
admin.site.register(Location)
