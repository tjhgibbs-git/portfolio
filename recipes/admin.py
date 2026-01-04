from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from .models import Recipe
import json


class RecipeAdminForm(forms.ModelForm):
    """Custom form for Recipe admin with simplified JSON paste workflow"""
    json_input = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 20,
            'class': 'vLargeTextField',
            'style': 'width: 95%; font-family: monospace; font-size: 14px;',
            'placeholder': 'Paste your recipe JSON here and save - that\'s it! Fields below will auto-populate.'
        }),
        help_text='Paste your complete recipe JSON here. All fields will be automatically populated. You can optionally edit them below before saving.'
    )

    class Meta:
        model = Recipe
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'vLargeTextField', 'style': 'width: 95%; font-size: 18px;'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'vLargeTextField', 'style': 'width: 95%;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate json_input with existing recipe_data if editing
        if self.instance and self.instance.pk and hasattr(self.instance, 'recipe_data') and self.instance.recipe_data:
            self.fields['json_input'].initial = json.dumps(self.instance.recipe_data, indent=2)
        # Make json_input optional for editing existing recipes
        if self.instance and self.instance.pk:
            self.fields['json_input'].required = False

        # Make form fields optional - they'll be populated from JSON in clean()
        # Only modify fields if they exist in the form
        if 'name' in self.fields:
            self.fields['name'].required = False
        if 'recipe_data' in self.fields:
            self.fields['recipe_data'].required = False

    def clean(self):
        cleaned_data = super().clean()
        json_input = cleaned_data.get('json_input')

        # If JSON input is provided, parse it and populate ALL fields from it
        if json_input and json_input.strip():
            try:
                recipe_json = json.loads(json_input)
                # Store the JSON data
                cleaned_data['recipe_data'] = recipe_json

                # Always auto-populate all fields from JSON (override existing values)
                cleaned_data['name'] = recipe_json.get('name', '')
                cleaned_data['description'] = recipe_json.get('description', '')
                cleaned_data['prep_time'] = recipe_json.get('prepTime', '')
                cleaned_data['cook_time'] = recipe_json.get('cookTime', '')
                cleaned_data['total_time'] = recipe_json.get('totalTime', '')
                cleaned_data['servings'] = recipe_json.get('servings', '')
                cleaned_data['difficulty'] = recipe_json.get('difficulty', 'Easy')

                # Auto-generate slug from name if not provided
                if not cleaned_data.get('slug'):
                    from django.utils.text import slugify
                    cleaned_data['slug'] = slugify(cleaned_data['name'])

            except json.JSONDecodeError as e:
                raise forms.ValidationError(f'Invalid JSON format: {e}')
        elif not self.instance.pk:
            # For new recipes, JSON is required
            raise forms.ValidationError('Please paste recipe JSON to create a new recipe.')

        return cleaned_data


class PublishStatusFilter(admin.SimpleListFilter):
    """Filter recipes by publish status"""
    title = 'Status'
    parameter_name = 'publish_status'

    def lookups(self, request, model_admin):
        return (
            ('published', 'Published'),
            ('draft', 'Draft'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'published':
            return queryset.filter(is_published=True)
        if self.value() == 'draft':
            return queryset.filter(is_published=False)
        return queryset


class DifficultyFilter(admin.SimpleListFilter):
    """Filter recipes by difficulty"""
    title = 'Difficulty'
    parameter_name = 'difficulty'

    def lookups(self, request, model_admin):
        return (
            ('Easy', 'Easy'),
            ('Medium', 'Medium'),
            ('Hard', 'Hard'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(difficulty=self.value())
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm
    list_display = ('colored_name', 'difficulty_display', 'status_display', 'servings', 'total_time', 'formatted_date')
    list_filter = (PublishStatusFilter, DifficultyFilter)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'published_at'
    save_on_top = True
    actions_on_top = True
    actions_on_bottom = True

    fieldsets = (
        ('Step 1: Paste Recipe JSON', {
            'fields': ('json_input',),
            'classes': ('wide',),
            'description': 'Paste your recipe JSON here and save. All fields below will auto-populate. That\'s it!',
        }),
        ('Step 2 (Optional): Review & Edit Auto-Populated Fields', {
            'fields': ('name', 'slug', 'description'),
            'classes': ('wide',),
            'description': 'These fields are automatically filled from your JSON. Edit if needed.',
        }),
        ('Recipe Info (Auto-Populated)', {
            'fields': ('prep_time', 'cook_time', 'total_time', 'servings', 'difficulty'),
            'classes': ('wide',),
        }),
        ('Publishing (Published by Default)', {
            'fields': ('is_published', 'published_at'),
            'classes': ('wide',),
            'description': 'New recipes are published by default. Uncheck to save as draft.',
        }),
    )

    readonly_fields = ()

    def colored_name(self, obj):
        """Display name with a color indicator of difficulty"""
        colors = {
            'Easy': '#4CAF50',    # Green
            'Medium': '#FF9800',  # Orange
            'Hard': '#F44336',    # Red
        }
        color = colors.get(obj.difficulty, '#2f2d2e')
        name = obj.name
        if len(name) > 50:
            name = name[:47] + '...'
        return format_html(
            '<span style="border-left: 4px solid {}; padding-left: 8px;">{}</span>',
            color, name
        )
    colored_name.short_description = 'Recipe Name'

    def difficulty_display(self, obj):
        """Display difficulty with color"""
        colors = {
            'Easy': '#4CAF50',    # Green
            'Medium': '#FF9800',  # Orange
            'Hard': '#F44336',    # Red
        }
        color = colors.get(obj.difficulty, '#2f2d2e')
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color, obj.difficulty
        )
    difficulty_display.short_description = 'Difficulty'

    def status_display(self, obj):
        """Display published status with color"""
        if obj.is_published:
            return format_html('<span style="color:#4CAF50; font-weight: 600;">Published</span>')
        return format_html('<span style="color:#FF5722; font-weight: 600;">Draft</span>')
    status_display.short_description = 'Status'

    def formatted_date(self, obj):
        """Format the published date nicely"""
        if obj.published_at:
            return obj.published_at.strftime('%b %d, %Y')
        return 'Not published'
    formatted_date.short_description = 'Date'

    def view_on_site(self, obj):
        """Only return URL if recipe is published"""
        if obj.is_published:
            return obj.get_absolute_url()
        return None
