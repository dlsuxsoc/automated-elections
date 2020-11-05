"""autoelect URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Fake admin path /admin/
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),

    # Actual admin path /rndadmin/
    path('rndadmin/', admin.site.urls),

    # /login/
    path('login/', include('login.urls')),

    # /
    path('', include('vote.urls')),

    # /logout/
    path('logout/', include('logout.urls')),

    # /officer/
    path('officer/', include('passcode.urls')),

    # /sysadmin/
    path('sysadmin/', include('sysadmin.urls')),
]
