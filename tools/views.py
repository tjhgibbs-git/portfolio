from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from .models import Tool

def tool_list(request):
    """Display list of tools with search functionality"""
    tools = Tool.objects.filter(is_active=True)

    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        tools = tools.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Order by most recent
    tools = tools.order_by('-created_at')

    context = {
        'tools': tools,
        'search_query': search_query,
    }
    return render(request, 'tools/tool_list.html', context)

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


