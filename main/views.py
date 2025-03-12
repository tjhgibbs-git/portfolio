from django.shortcuts import render, get_object_or_404
from .models import Project
import markdown
from django.utils.safestring import mark_safe

def home(request):
    return render(request, 'main/home.html')

def about(request):
    return render(request, 'main/about.html')

def portfolio(request):
    projects = Project.objects.all().order_by('-featured', '-date_created')
    return render(request, 'main/portfolio.html', {'projects': projects})

def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    
    # Convert markdown to HTML
    description_html = mark_safe(markdown.markdown(project.description))
    
    return render(request, 'main/project_detail.html', {
        'project': project,
        'description_html': description_html
    })

def contact(request):
    return render(request, 'main/contact.html')

def blog(request):
    return render(request, 'main/blog.html')