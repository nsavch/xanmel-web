"""
Django settings for xanmel_web project.

Generated by 'django-admin startproject' using Django 1.10.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '8wjx-h-=&h!d(z%se#8n&n7m*m#u+29t$t67owb@-g-(9=2f!i'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_jinja',
    'map_rating',
    'xdf',
    'xanmel_db'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'xanmel_db.middleware.XanmelDBMiddleware'
]

ROOT_URLCONF = 'xanmel_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django_jinja.backend.Jinja2',
        'APP_DIRS': True,
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'OPTIONS': {
            'match_extension': '.jinja',
            'globals': {
                'query_param': 'map_rating.jinja_helpers.query_param',
                'time_format': 'map_rating.jinja_helpers.time_format'
            },
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'xanmel_web.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

with open('../xanmel/xanmel.yaml', 'r') as f:
    XANMEL_CONFIG = yaml.safe_load(f)

XONOTIC_SERVERS = XANMEL_CONFIG['modules']['xanmel.modules.xonotic.XonoticModule']['servers']
XONOTIC_ELO_REQUEST_SIGNATURE = 'gQEBTrBWi2M7i5cInTMatx0iHAxmN4Xta2NZdXD2OsFls/x/k6XrxoevCGARC4jhC2DzgYHFM5vA40aih59tlXSzrFQ6EiiSgoWG+h1oERFHYWdg3KNwgEkUfnskEy2FS6BhdTs6JdpBAsEq348+NysGVhe7ZYMHlJUTFYE/nJVKC4qBAQGPqnGoD6GhuHLYN+Sf73ROColneBdJ7ttuVwm32FvI8LuD5aLDll7bpqfHTWhgbTW02CYvkTAYtoz2RZmIGK5ZHHaM/V6vcSXnq2ab/7mFRiag7D5OUsmIFY9E3IqcqtP7+wXSVgiNFY3DBPy27bXjk8ZJ9nUD5dQBL9sG8TzWd4EBAdZmc6gLKdO16z5PJQGsWrf1yOViENd/VANx+7aGPQsouAuhwzOlB06SkZ6dxx2zLyfagVthXTXY4JfUoAaa9vSkwqH/7TNIyHxBI220ZyFtekGzJFro2b7zRYiOqs3bKr0pec7qakn9blY0YfgO9W9GI8vG+JsQIk7MJNmSBupTgQEBQUDrksY28iujDepIsG4mXaZdvKM2RhWKKxI4VgrXQ33FVmAQqPwrA3U0EMEE6DR+O8tf6kHsN5efub9aU30E5nRcKEKBln5ro3RHtnLMtBikG5Tqy4o3grx4/SHfFPhs4CMvOYT304A6y1f35TsUj83ahbORkFjaKetTq97vZkk='
XONOTIC_XDF_DATABASES = {
    4: '../../server.db.defrag'
}
