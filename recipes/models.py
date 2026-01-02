# recipes/models.py
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone


class Recipe(models.Model):
    # Difficulty choices
    EASY = 'Easy'
    MEDIUM = 'Medium'
    HARD = 'Hard'
    DIFFICULTY_CHOICES = [
        (EASY, 'Easy'),
        (MEDIUM, 'Medium'),
        (HARD, 'Hard'),
    ]

    # Basic fields
    name = models.CharField(max_length=200, help_text="Recipe name (from JSON)")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Brief description")

    # Recipe metadata
    prep_time = models.CharField(max_length=50, blank=True)
    cook_time = models.CharField(max_length=50, blank=True)
    total_time = models.CharField(max_length=50, blank=True)
    servings = models.CharField(max_length=100, blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=EASY)

    # Store full recipe data as JSON
    recipe_data = models.JSONField(help_text="Full recipe JSON data")

    # Publishing
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('recipes:recipe_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        # Extract data from recipe_data JSON if available
        if self.recipe_data:
            if not self.name:
                self.name = self.recipe_data.get('name', '')
            if not self.description:
                self.description = self.recipe_data.get('description', '')
            if not self.prep_time:
                self.prep_time = self.recipe_data.get('prepTime', '')
            if not self.cook_time:
                self.cook_time = self.recipe_data.get('cookTime', '')
            if not self.total_time:
                self.total_time = self.recipe_data.get('totalTime', '')
            if not self.servings:
                self.servings = self.recipe_data.get('servings', '')
            if not self.difficulty or self.difficulty == self.EASY:
                recipe_difficulty = self.recipe_data.get('difficulty', 'Easy')
                self.difficulty = recipe_difficulty

        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.name)

        # Set published date when recipe is first published
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def ingredients(self):
        """Return ingredients list from JSON data"""
        return self.recipe_data.get('ingredients', [])

    @property
    def instructions(self):
        """Return instructions list from JSON data"""
        return self.recipe_data.get('instructions', [])

    @property
    def notes(self):
        """Return notes list from JSON data"""
        return self.recipe_data.get('notes', [])
