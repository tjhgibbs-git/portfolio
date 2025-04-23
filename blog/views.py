# blog/views.py
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
import markdown
from django.utils.safestring import mark_safe
from .models import Post, Tag

def post_list(request, tag_slug=None):
    posts = Post.objects.filter(is_published=True, published_at__lte=timezone.now())
    
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags=tag)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    # Process markdown for display
    for post in posts:
        post.content_html = mark_safe(markdown.markdown(
            post.content,
            extensions=['extra', 'codehilite']
        ))
        if post.excerpt:
            post.excerpt_html = mark_safe(markdown.markdown(
                post.excerpt,
                extensions=['extra']
            ))
    
    # Get all tags for the sidebar
    all_tags = Tag.objects.all()
    
    return render(request, 'blog/post_list.html', {
        'posts': posts,
        'tag': tag,
        'all_tags': all_tags,
        'search_query': search_query
    })

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True, published_at__lte=timezone.now())
    
    # Convert markdown to HTML
    post.content_html = mark_safe(markdown.markdown(
        post.content,
        extensions=['extra', 'codehilite']
    ))
    
    # Get related posts (same tags)
    related_posts = Post.objects.filter(
        is_published=True, 
        published_at__lte=timezone.now(),
        tags__in=post.tags.all()
    ).exclude(id=post.id).distinct()[:3]
    
    # Get all tags for the sidebar
    all_tags = Tag.objects.all()
    
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'related_posts': related_posts,
        'all_tags': all_tags
    })