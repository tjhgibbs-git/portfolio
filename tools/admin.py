from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.management import call_command
from django.utils import timezone
from django.db.models import Q, F
from .models import Tool

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'view_count', 'created_at', 'needs_export_display', 'preview_link']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['name', 'description', 'slug']
    readonly_fields = ['slug', 'created_at', 'updated_at', 'last_exported', 'view_count', 'preview_tool']
    actions = ['export_selected_tools', 'mark_as_active', 'mark_as_inactive']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'is_active')
        }),
        ('Tool Content', {
            'fields': ('html_content', 'preview_tool'),
            'description': 'Paste your complete Claude artifact HTML code in the field below:'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_exported', 'view_count'),
            'classes': ('collapse',)
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('backup-all/', self.admin_site.admin_view(self.backup_all_tools), name='tools_tool_backup_all'),
        ]
        return my_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Add backup button to changelist
        tools_needing_export = Tool.objects.filter(
            Q(last_exported__isnull=True) | 
            Q(updated_at__gt=F('last_exported'))
        ).count()
        
        extra_context['tools_needing_export'] = tools_needing_export
        extra_context['backup_url'] = reverse('admin:tools_tool_backup_all')
        
        return super().changelist_view(request, extra_context)
    
    def backup_all_tools(self, request):
        """Custom admin view to backup all tools"""
        try:
            # Call the management command
            call_command('export_tools', git_commit=True, verbosity=0)
            
            messages.success(
                request, 
                format_html(
                    '✅ Tools backup completed successfully! '
                    'All changed tools have been exported and committed to git.'
                )
            )
        except Exception as e:
            messages.error(
                request,
                format_html('❌ Backup failed: {}', str(e))
            )
        
        return HttpResponseRedirect(reverse('admin:tools_tool_changelist'))
    
    def export_selected_tools(self, request, queryset):
        """Admin action to export selected tools"""
        try:
            # Mark selected tools as needing export by clearing last_exported
            queryset.update(last_exported=None)
            
            # Run export command
            call_command('export_tools', git_commit=True, verbosity=0)
            
            self.message_user(
                request,
                f'Successfully exported {queryset.count()} selected tool(s) to git backup.',
                messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                f'Export failed: {str(e)}',
                messages.ERROR
            )
    
    export_selected_tools.short_description = "🔄 Export selected tools to git backup"
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} tool(s) marked as active.')
    mark_as_active.short_description = "✅ Mark selected tools as active"
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} tool(s) marked as inactive.')
    mark_as_inactive.short_description = "❌ Mark selected tools as inactive"
    
    def preview_link(self, obj):
        if obj.pk:
            url = reverse('tools:detail', kwargs={'slug': obj.slug})
            return format_html('<a href="{}" target="_blank">View Tool →</a>', url)
        return "Save to preview"
    preview_link.short_description = "Preview"
    
    def needs_export_display(self, obj):
        if obj.needs_export:
            return format_html('<span style="color: orange; font-weight: bold;">●</span> Needs Export')
        return format_html('<span style="color: green;">●</span> Up to date')
    needs_export_display.short_description = "Export Status"
    
    def preview_tool(self, obj):
        if obj.html_content:
            # Extract title for display
            title = obj.extract_title_from_html()
            return format_html(
                '''
                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #f9f9f9;">
                    <h4>Tool Preview: {}</h4>
                    <p><strong>URL:</strong> <code>{}</code></p>
                    <p><strong>Status:</strong> {}</p>
                    <p><strong>HTML Length:</strong> {} characters</p>
                    {}
                </div>
                ''',
                title,
                obj.get_absolute_url() if obj.pk else 'Not saved yet',
                'Active' if obj.is_active else 'Inactive',
                len(obj.html_content),
                '<p><a href="{}" target="_blank" style="background: #007cba; color: white; padding: 8px 16px; text-decoration: none; border-radius: 3px;">Open Tool →</a></p>' 
                if obj.pk else '<p><em>Save the tool to generate preview link</em></p>'
            )
        return "No content yet"
    preview_tool.short_description = "Tool Preview"
    
    def save_model(self, request, obj, form, change):
        # Auto-generate name from HTML title if name is empty
        if not obj.name and obj.html_content:
            extracted_title = obj.extract_title_from_html()
            if extracted_title != "Untitled Tool":
                obj.name = extracted_title
        
        super().save_model(request, obj, form, change)
        
        # Show success message with link
        if obj.pk:
            self.message_user(
                request,
                format_html(
                    'Tool "{}" saved successfully! <a href="{}" target="_blank">View it here →</a>',
                    obj.name,
                    obj.get_absolute_url()
                )
            )
    
    class Media:
        css = {
            'all': ('css/tools_admin.css',)
        }
        js = ('js/tools_admin.js',)