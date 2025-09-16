# from django.contrib import admin
# from django.urls import path, include
# from django.conf.urls.static import static
# from django.conf import settings
# from django.contrib.staticfiles.urls import staticfiles_urlpatterns


# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('home.urls')),
#     path('product/', include('products.urls')),
#     path('accounts/', include('accounts.urls')),
#     path("accounts/", include("allauth.urls")),
    
# ]


# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL,
#                           document_root=settings.MEDIA_ROOT)


# urlpatterns += staticfiles_urlpatterns()




from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Apps
    path('', include('home.urls')),               # Homepage
    path('products/', include('products.urls')),  # Products app

    # Accounts
    path('accounts/', include('accounts.urls')),  # Your custom accounts app (if exists)
    path('accounts/', include('allauth.urls')),   # Social auth (Google, Facebook, etc.)
]

# Serve media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
