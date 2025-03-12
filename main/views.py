from django.shortcuts import render

def home(request):
    """View function for the home page."""
    return render(request, 'main/home.html')

def about(request):
    return render(request, 'main/about.html')

def portfolio(request):
    return render(request, 'main/portfolio.html')

def contact(request):
    return render(request, 'main/contact.html')

def blog(request):
    return render(request, 'main/blog.html')