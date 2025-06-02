from django.db import models
from django.utils.text import slugify
from django.urls import reverse
import re

class Tool(models.Model):
    name = models.CharField(max_length=200, help_text="Name of the tool")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL slug (auto-generated from name)")
    description = models.TextField(blank=True, help_text="Brief description of what this tool does")
    
    # Store the artifact code
    html_content = models.TextField(help_text="Paste the complete HTML artifact code here")
    
    # Metadata
    is_active = models.BooleanField(default=True, help_text="Whether the tool is publicly accessible")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_exported = models.DateTimeField(null=True, blank=True, help_text="When this tool was last exported to git")
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0, help_text="Number of times this tool has been accessed")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tool"
        verbose_name_plural = "Tools"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)
    
    def generate_unique_slug(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        while Tool.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def get_absolute_url(self):
        return reverse('tools:detail', kwargs={'slug': self.slug})
    
    def extract_title_from_html(self):
        """Extract title from HTML content for better admin display"""
        if self.html_content:
            title_match = re.search(r'<title>(.*?)</title>', self.html_content, re.IGNORECASE)
            if title_match:
                return title_match.group(1)
        return "Untitled Tool"
    
    def increment_view_count(self):
        """Increment view count atomically"""
        Tool.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)
        self.refresh_from_db(fields=['view_count'])
    
    @property
    def needs_export(self):
        """Check if this tool needs to be exported (updated since last export)"""
        if not self.last_exported:
            return True
        return self.updated_at > self.last_exported