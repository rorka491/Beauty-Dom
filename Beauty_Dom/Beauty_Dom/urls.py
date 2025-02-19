from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from mainapp.views import *
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mainapp.urls')),
    path('adminapp/', include('adminapp.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)







