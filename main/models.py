from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(help_text="Markdown supported")
    short_description = models.TextField()
    image = models.ImageField(upload_to='projects/')
    technologies = models.CharField(max_length=255, help_text="Comma-separated list of technologies")
    url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    date_created = models.DateField()
    featured = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    def get_technologies_list(self):
        return [tech.strip() for tech in self.technologies.split(',')]


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, related_name='additional_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.project.title}"