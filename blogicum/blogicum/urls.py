from blog.views import ProfileLoginView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.urls import include, path, reverse_lazy
from django.views.generic.edit import CreateView

urlpatterns = [
    path('', include('blog.urls', namespace='blog')),
    path('pages/', include('pages.urls', namespace='pages')),
    path('auth/login/', ProfileLoginView.as_view(), name='login'),
    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('login'),
        ),
        name='registration',
    ),
    path('auth/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL,
           document_root=settings.MEDIA_ROOT)

handler404 = 'pages.views.handler404'
handler500 = 'pages.views.handler500'
