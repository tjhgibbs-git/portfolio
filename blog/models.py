# blog/models.py
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Post(models.Model):
    # Post type choices
    ARTICLE = 'article'
    LINK = 'link'
    NOTE = 'note'
    POST_TYPES = [
        (ARTICLE, 'Article'),
        (LINK, 'Link'),
        (NOTE, 'Note'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(help_text="Markdown supported")
    excerpt = models.TextField(blank=True, help_text="Short summary (optional). If left blank, an excerpt will be automatically generated.")
    
    # Fields for link posts
    external_url = models.URLField(blank=True, help_text="For link posts, the URL to link to")
    
    # Common fields
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default=ARTICLE)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    def is_long_post(self):
        """Check if the post is considered 'long' and should be truncated."""
        # Roughly 200 words
        return len(self.content.split()) > 200
    
    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Set published date when post is first published
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
            
        # Generate excerpt if not provided
        if not self.excerpt and self.content:
            # Take approximately the first 100 words
            words = self.content.split()[:100]
            self.excerpt = ' '.join(words) + '...' if len(words) >= 100 else self.content
        
        super().save(*args, **kwargs)

class PostImage(models.Model):
    post = models.ForeignKey(Post, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='blog/images/%Y/%m/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.post.title}"