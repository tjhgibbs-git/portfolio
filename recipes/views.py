from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Recipe


def recipe_list(request):
    """Display list of published recipes with search functionality"""
    recipes = Recipe.objects.filter(is_published=True)

    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        recipes = recipes.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Order by most recent
    recipes = recipes.order_by('-published_at', '-created_at')

    context = {
        'recipes': recipes,
        'search_query': search_query,
    }
    return render(request, 'recipes/recipe_list.html', context)


def recipe_detail(request, slug):
    """Display a single recipe detail"""
    recipe = get_object_or_404(Recipe, slug=slug, is_published=True)

    context = {
        'recipe': recipe,
    }
    return render(request, 'recipes/recipe_detail.html', context)
