import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security and debug come from environment in production
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-for-local')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'yes')

# ALLOWED_HOSTS: Always include Render domain + localhost for dev
ALLOWED_HOSTS = ['theher.onrender.com', 'localhost', '127.0.0.1']
# Add custom hosts from env if provided
ALLOWED_HOSTS_ENV = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS.extend([h.strip() for h in ALLOWED_HOSTS_ENV.split(',') if h.strip()])
# In debug mode, also accept all hosts
if DEBUG:
    ALLOWED_HOSTS.append('*')

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'her',
]

# Use WhiteNoise for static file serving in production
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

# CSRF settings for production
CSRF_TRUSTED_ORIGINS = [
    'https://theher.onrender.com',
]
if DEBUG:
    CSRF_TRUSTED_ORIGINS.append('http://localhost:8000')
    CSRF_TRUSTED_ORIGINS.append('http://127.0.0.1:8000')

ROOT_URLCONF = 'theher_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'webapp', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'theher_django.wsgi.application'

# Database: prefer DATABASE_URL, fallback to local sqlite
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'webapp', 'static')]
# Directory where `collectstatic` will collect static files for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise: set compressed/static manifest
WHITENOISE_AUTOREFRESH = False
WHITENOISE_USE_FINDERS = True
