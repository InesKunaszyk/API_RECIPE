""""URL mappings for the recipe app"""

from django.urls import (
    path,
    include
)

from rest_framework.routers import DefaultRouter
# provided by DjangoRestFramework - automatically create routes for ALL ofthe different options

from recipe import views

router = DefaultRouter()
router.register('recipes', views.RecipeViewSet)
# assign of all the deifferent edpoints from our RECIPE VIEW set to that endpoint
# - > Recipe view has auto generated URL, which depends on functionality in viewset
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)

app_name = "recipe"

urlpatterns = [
    path('', include(router.urls)),
]
