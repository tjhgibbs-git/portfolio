from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from .models import Recipe
import json


class RecipeAdminForm(forms.ModelForm):
    """Custom form for Recipe admin with JSON paste support"""
    json_input = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 20,
            'class': 'vLargeTextField',
            'style': 'width: 95%; font-family: monospace; font-size: 14px;',
            'placeholder': 'Paste your recipe JSON here...'
        }),
        help_text='Paste the complete recipe JSON here. It will automatically populate the fields below.'
    )

    class Meta:
        model = Recipe
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'vLargeTextField', 'style': 'width: 95%; font-size: 18px;'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'vLargeTextField', 'style': 'width: 95%;'}),
            'recipe_data': forms.Textarea(attrs={
                'rows': 15,
                'class': 'vLargeTextField',
                'style': 'width: 95%; font-family: monospace; font-size: 12px;',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate json_input with existing recipe_data if editing
        if self.instance and self.instance.pk and self.instance.recipe_data:
            self.fields['json_input'].initial = json.dumps(self.instance.recipe_data, indent=2)

    def clean(self):
        cleaned_data = super().clean()
        json_input = cleaned_data.get('json_input')

        # If JSON input is provided, parse it and set recipe_data
        if json_input and json_input.strip():
            try:
                recipe_json = json.loads(json_input)
                cleaned_data['recipe_data'] = recipe_json

                # Auto-populate other fields from JSON if they're empty
                if not cleaned_data.get('name'):
                    cleaned_data['name'] = recipe_json.get('name', '')
                if not cleaned_data.get('description'):
                    cleaned_data['description'] = recipe_json.get('description', '')
                if not cleaned_data.get('prep_time'):
                    cleaned_data['prep_time'] = recipe_json.get('prepTime', '')
                if not cleaned_data.get('cook_time'):
                    cleaned_data['cook_time'] = recipe_json.get('cookTime', '')
                if not cleaned_data.get('total_time'):
                    cleaned_data['total_time'] = recipe_json.get('totalTime', '')
                if not cleaned_data.get('servings'):
                    cleaned_data['servings'] = recipe_json.get('servings', '')
                if not cleaned_data.get('difficulty') or cleaned_data.get('difficulty') == Recipe.EASY:
                    cleaned_data['difficulty'] = recipe_json.get('difficulty', 'Easy')

            except json.JSONDecodeError as e:
                raise forms.ValidationError(f'Invalid JSON format: {e}')

        return cleaned_data


class PublishStatusFilter(admin.SimpleListFilter):
    """Filter recipes by publish status"""
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


class DifficultyFilter(admin.SimpleListFilter):
    """Filter recipes by difficulty"""
    title = 'Difficulty'
    parameter_name = 'difficulty'

    def lookups(self, request, model_admin):
        return (
            ('Easy', '🟢 Easy'),
            ('Medium', '🟡 Medium'),
            ('Hard', '🔴 Hard'),
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
        (None, {
            'fields': ('json_input',),
            'classes': ('wide',),
            'description': '⬇️ Paste your recipe JSON here first (recommended)',
        }),
        ('Recipe Details', {
            'fields': ('name', 'slug', 'description'),
            'classes': ('wide',),
        }),
        ('Recipe Metadata', {
            'fields': ('prep_time', 'cook_time', 'total_time', 'servings', 'difficulty'),
            'classes': ('wide',),
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at'),
            'classes': ('wide',),
            'description': '⚠️ Recipe must be published to appear on site and be viewable via "View on site" button',
        }),
        ('Advanced', {
            'fields': ('recipe_data',),
            'classes': ('collapse',),
            'description': 'Raw JSON data (auto-populated from JSON input above)',
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
        """Display difficulty with an icon"""
        icons = {
            'Easy': '🟢',
            'Medium': '🟡',
            'Hard': '🔴',
        }
        icon = icons.get(obj.difficulty, '⚪')
        return format_html('{} {}', icon, obj.difficulty)
    difficulty_display.short_description = 'Difficulty'

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

    def view_on_site(self, obj):
        """Only return URL if recipe is published"""
        if obj.is_published:
            return obj.get_absolute_url()
        return None
