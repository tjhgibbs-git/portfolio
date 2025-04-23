from django.contrib import admin
from django import forms
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from .models import Post, Tag, PostImage


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    fields = ('image', 'caption', 'order', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, instance):
        if instance.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 300px;" />', instance.image.url)
        return "No image"


class PostAdminForm(forms.ModelForm):
    """Custom form for Post admin with better mobile support"""
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'vLargeTextField', 'style': 'width: 95%; font-size: 18px;'}),
            'content': forms.Textarea(attrs={
                'rows': 20, 
                'class': 'vLargeTextField markdown-editor',
                'style': 'width: 95%; font-family: monospace; font-size: 14px;',
            }),
            'excerpt': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'vLargeTextField', 
                'style': 'width: 95%;',
                'placeholder': 'Optional short summary. If left empty, it will be generated automatically.'
            }),
            'external_url': forms.URLInput(attrs={
                'style': 'width: 95%;',
                'placeholder': 'https://example.com/article-to-link-to'
            }),
        }


class PostTypeFilter(admin.SimpleListFilter):
    """Filter posts by type with nice icons"""
    title = 'Post Type'
    parameter_name = 'post_type'
    
    def lookups(self, request, model_admin):
        return (
            ('article', '📄 Article'),
            ('link', '🔗 Link'),
            ('note', '📝 Note'),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(post_type=self.value())
        return queryset


class PublishStatusFilter(admin.SimpleListFilter):
    """Filter posts by publish status"""
    title = 'Status'
    parameter_name = 'publish_status'
    
    def lookups(self, request, model_admin):
        return (
            ('published', '✅ Published'),
            ('draft', '📋 Draft'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'published':
            return queryset.filter(is_published=True)
        if self.value() == 'draft':
            return queryset.filter(is_published=False)
        return queryset


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ('colored_title', 'post_type_display', 'status_display', 'formatted_date', 'tag_list')
    list_filter = (PublishStatusFilter, PostTypeFilter, 'tags')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    inlines = [PostImageInline]
    filter_horizontal = ('tags',)
    save_on_top = True  # Add save buttons at the top (helpful on mobile)
    actions_on_top = True
    actions_on_bottom = True
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug'),
            'classes': ('wide',),
        }),
        ('Content', {
            'fields': ('post_type', 'content'),
            'classes': ('wide',),
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at', 'tags'),
            'classes': ('wide',),
        }),
        ('Link Post Options', {
            'fields': ('external_url',),
            'classes': ('wide', 'collapse'),
            'description': 'Only needed for link-type posts',
        }),
        ('Summary/Excerpt', {
            'fields': ('excerpt',),
            'classes': ('wide', 'collapse'),
            'description': 'Optional custom excerpt. If left empty, one will be generated automatically.',
        }),
    )
    
    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/easymde/dist/easymde.min.css', 'css/blog_admin.css')
        }
        js = ('https://cdn.jsdelivr.net/npm/easymde/dist/easymde.min.js', 'js/blog_post_admin.js')
    
    def save_model(self, request, obj, form, change):
        # Set published_at timestamp when post is published
        if obj.is_published and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    def colored_title(self, obj):
        """Display title with a color indicator of post type"""
        colors = {
            'article': '#0e9aa7',  # Blue
            'link': '#f46036',     # Orange
            'note': '#ffde22',     # Yellow
        }
        color = colors.get(obj.post_type, '#2f2d2e')
        title = obj.title
        if len(title) > 60:
            title = title[:57] + '...'
        return format_html(
            '<span style="border-left: 4px solid {}; padding-left: 8px;">{}</span>',
            color, title
        )
    colored_title.short_description = 'Title'

    def post_type_display(self, obj):
        """Display post type with an icon"""
        icons = {
            'article': '📄',
            'link': '🔗',
            'note': '📝',
        }
        icon = icons.get(obj.post_type, '❓')
        return format_html('{} {}', icon, obj.get_post_type_display())
    post_type_display.short_description = 'Type'

    def status_display(self, obj):
        """Display published status with an icon and color"""
        if obj.is_published:
            return format_html('<span style="color:#4CAF50;">✅ Published</span>')
        return format_html('<span style="color:#FF5722;">📋 Draft</span>')
    status_display.short_description = 'Status'
    
    def formatted_date(self, obj):
        """Format the published date nicely"""
        if obj.published_at:
            return obj.published_at.strftime('%b %d, %Y')
        return 'Not published'
    formatted_date.short_description = 'Date'
    
    def tag_list(self, obj):
        """Display a comma-separated list of tags with links"""
        tags = []
        for tag in obj.tags.all():
            url = reverse('admin:blog_tag_change', args=[tag.id])
            tags.append(format_html('<a href="{}">{}</a>', url, tag.name))
        return format_html(', '.join(tags)) if tags else 'No tags'
    tag_list.short_description = 'Tags'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    
    def post_count(self, obj):
        """Display the number of posts with this tag"""
        count = obj.posts.count()
        url = reverse('admin:blog_post_changelist') + f'?tags__id__exact={obj.id}'
        return format_html('<a href="{}">{} post{}</a>', url, count, 's' if count != 1 else '')
    post_count.short_description = 'Posts'