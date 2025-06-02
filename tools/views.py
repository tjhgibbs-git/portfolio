from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.generic import ListView
from .models import Tool

class ToolListView(ListView):
    model = Tool
    template_name = 'tools/tool_list.html'
    context_object_name = 'tools'
    paginate_by = 12
    
    def get_queryset(self):
        return Tool.objects.filter(is_active=True).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_tools'] = Tool.objects.filter(is_active=True).count()
        return context

def tool_detail(request, slug):
    """Serve the tool HTML directly"""
    tool = get_object_or_404(Tool, slug=slug, is_active=True)
    
    # Increment view count
    tool.increment_view_count()
    
    # Return the HTML content directly
    return HttpResponse(tool.html_content, content_type='text/html')

def tool_preview(request, slug):
    """Preview tool with wrapper (for admin/development)"""
    tool = get_object_or_404(Tool, slug=slug)
    
    context = {
        'tool': tool,
        'is_preview': True
    }
    
    return render(request, 'tools/tool_preview.html', context)


