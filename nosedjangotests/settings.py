from os import getenv

from django.conf import global_settings

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

if hasattr(global_settings, 'DATABASES'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'nosedjango',
            'USER': 'root',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        }
    }

    if getenv('JENNKINS_URL', False):
        # We're on Jenkins
        DATABASES['default'].update({
            'ENGINE': getenv('DBA_SQL_DJANGO_ENGINE'),
            'USER': getenv('DBA_SQL_ADMIN'),
            'PASSWORD': getenv('DBA_SQL_ADMIN_PASSWORD'),
            'HOST': getenv('DBA_SQL_HOST'),
            'PORT': getenv('DBA_SQL_PORT'),

        })
else:
    DATABASE_ENGINE = 'sqlite3'
    DATABASE_NAME = 'nosedjango'
    DATABASE_USER = 'root'
    DATABASE_PASSWORD = ''
    DATABASE_HOST = ''
    DATABASE_PORT = ''

    if getenv('JENNKINS_URL', False):
        # We're on Jenkins
        DATABASE_ENGINE = getenv('DBA_SQL_DJANGO_ENGINE')
        DATABASE_USER = getenv('DBA_SQL_ADMIN')
        DATABASE_PASSWORD = getenv('DBA_SQL_ADMIN_PASSWORD')
        DATABASE_HOST = getenv('DBA_SQL_HOST')
        DATABASE_PORT = getenv('DBA_SQL_PORT')

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1

USE_I18N = True
MEDIA_ROOT = ''
MEDIA_URL = ''

ADMIN_MEDIA_PREFIX = '/media/'
SECRET_KEY = 'w9*+(qevfn*j2959ikv-_7kj7ivptt#8&n*gy0o&ktisx@%rzt'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'nosedjangotests.urls'

TEMPLATE_DIRS = (
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',

    'nosedjangotests.polls',
)
