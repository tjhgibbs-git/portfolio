from django.contrib import admin
from django import forms
from .models import Project, ProjectImage

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ('image', 'caption', 'order')

class ProjectAdminForm(forms.ModelForm):
    image_path = forms.CharField(required=False, help_text="Enter image path manually (e.g., 'projects/image.png')")
    
    class Meta:
        model = Project
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.image:
            self.fields['image_path'].initial = self.instance.image

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('image_path'):
            instance.image = self.cleaned_data['image_path']
        if commit:
            instance.save()
        return instance

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = ('title', 'date_created', 'featured')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'short_description', 'description')
        }),
        ('Images', {
            'fields': ('image', 'image_path'),
            'description': 'Upload a main image or provide a path'
        }),
        ('Details', {
            'fields': ('technologies', 'url', 'github_url', 'date_created', 'featured')
        }),
    )

@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'caption', 'order')
    list_filter = ('project',)