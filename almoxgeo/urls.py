"""
URLs raiz do projeto Sistema de Gestão de Estoque
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin do Django (mantido para superusuário)
    path('admin/', admin.site.urls),

    # Todas as URLs do app estoque
    path('', include('estoque.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
