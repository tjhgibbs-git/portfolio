# blog/views.py
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
import markdown
from django.utils.safestring import mark_safe
from .models import Post, Tag
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import base64
import uuid
from django.core.files.base import ContentFile
import re
from PIL import Image
import io

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

@csrf_exempt
def upload_image(request):
    """Handle image uploads from the paste event in the admin editor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is supported'}, status=405)
    
    # Check if we have a post_id or if this is a new post
    post_id = request.POST.get('post_id')
    
    # Get the image data from the request
    if 'image' not in request.FILES and 'image_data' not in request.POST:
        return JsonResponse({'error': 'No image found in request'}, status=400)
    
    try:
        # Handle base64 encoded image data (from paste)
        if 'image_data' in request.POST:
            # Parse the base64 string
            img_data = request.POST.get('image_data')
            if ';base64,' in img_data:
                # Remove the data URL prefix (e.g. data:image/png;base64,)
                format, imgstr = img_data.split(';base64,')
                # Get the file extension
                ext = format.split('/')[-1]
                # Generate a unique filename
                filename = f"{uuid.uuid4()}.{ext}"
                # Convert to Django file
                data = ContentFile(base64.b64decode(imgstr), name=filename)
            else:
                return JsonResponse({'error': 'Invalid image data format'}, status=400)
        else:
            # Handle regular file upload
            data = request.FILES['image']
            filename = data.name
        
        # Optionally resize the image if needed
        # This is commented out but you can uncomment if you want to resize
        """
        img = Image.open(data)
        # Resize while maintaining aspect ratio
        max_size = (1200, 1200)
        img.thumbnail(max_size, Image.LANCZOS)
        # Save to an in-memory file
        buffer = io.BytesIO()
        img.save(buffer, format=img.format)
        # Create a Django file from the buffer
        data = ContentFile(buffer.getvalue(), name=filename)
        """
        
        # If we have a post_id, associate the image with that post
        if post_id and post_id != 'new':
            try:
                post = Post.objects.get(id=post_id)
                post_image = post.images.create(
                    image=data,
                    caption='',  # Default empty caption
                    order=post.images.count()  # Add to the end
                )
                image_url = post_image.image.url
                
                # Return the URL to be inserted into the markdown
                return JsonResponse({
                    'success': True, 
                    'url': image_url,
                    'id': post_image.id
                })
            except Post.DoesNotExist:
                pass  # Continue to temporary upload
        
        # If no post_id or post not found, create a temporary image
        # This will be linked to the post when it's saved
        from django.core.files.storage import default_storage
        
        # Store in a temporary location
        temp_path = f"blog/images/temp/{filename}"
        saved_path = default_storage.save(temp_path, data)
        image_url = default_storage.url(saved_path)
        
        # Return the URL and temp path to be processed later
        return JsonResponse({
            'success': True, 
            'url': image_url,
            'temp_path': saved_path,
            'is_temp': True
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)