# blog/admin.py
from django.contrib import admin
from django import forms
from django.utils import timezone
from .models import Post, Tag, PostImage

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1

class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={'rows': 20, 'class': 'markdown-editor'}),
            'excerpt': forms.Textarea(attrs={'rows': 3}),
        }

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ('title', 'post_type', 'is_published', 'published_at')
    list_filter = ('post_type', 'is_published', 'tags')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    inlines = [PostImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'post_type', 'content')
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at', 'tags'),
        }),
        ('Link Post Options', {
            'fields': ('external_url',),
            'classes': ('collapse',),
        }),
        ('Summary/Excerpt', {
            'fields': ('excerpt',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Set published_at timestamp when post is published
        if obj.is_published and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)