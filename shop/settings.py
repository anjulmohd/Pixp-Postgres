"""
Django settings for shop project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()
import dj_database_url
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.getenv("SECRET_KEY")
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['pixp.up.railway.app','https://pixp.up.railway.app','127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://pixp.up.railway.app']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
    'login',
    'adminpanel',
    'cart',
    'userapp',
    'order',
    'payment',
    
    'whitenoise.runserver_nostatic',


    'django.contrib.sites',  # Required for django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
        # Google provider
    
    
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Move this AFTER AuthenticationMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'login.middleware.BlockedUserMiddleware'  # Keep this if necessary
    
]

ROOT_URLCONF = 'shop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
         'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart_item_count',
                'cart.context_processors.wishlist_item_count'
            ],
        },
    },
]



SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]



SOCIALACCOUN_PROVIDERS ={
        "google": {

            "SCOPE" : [

                "profile",
                "email"
            ],
            'APP': {
                'client_id' : os.environ['CLIENT_ID'],
                'secret' : os.environ['CLIENT_SECRET']
            },
            
            "AUTH_PARAMS" : {"access_type" : "online"}
            
        }



}



LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'



# # Disable default signups (force Google login)
# ACCOUNT_EMAIL_VERIFICATION = "optional"
# ACCOUNT_AUTHENTICATION_METHOD = "email"
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_SIGNUP_REDIRECT_URL = "/"  # Prevent signup redirection
# ACCOUNT_ADAPTER = 'myapp.adapters.NoSignupAccountAdapter'  # Custom adapter to block signups












EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # SMTP server for Gmail
EMAIL_PORT = 587  # SMTP port for TLS
EMAIL_USE_TLS = True  # Use TLS for secure email transmission
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")  # Replace with your Gmail email address
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")  # Replace with your Gmail password or App Password
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")  # Email address to send emails from

# EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
# DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")



WSGI_APPLICATION = 'shop.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# DATABASE_URL = os.getenv("DATABASE_URL")

# DATABASES = {
#     'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pixp_aws',              # Your RDS database name
        'USER': 'postgres',            # Your RDS username
        'PASSWORD': os.getenv("DATABASE_AWS_PASSWORD"),    # Your RDS password
        'HOST': 'database-1.czi8cwissmyc.eu-north-1.rds.amazonaws.com',     # e.g., mydb.xxxxxx.ap-south-1.rds.amazonaws.com
        'PORT':'5432',
        }
}

AUTH_USER_MODEL = 'login.CustomUser'


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'),]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR,'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'




