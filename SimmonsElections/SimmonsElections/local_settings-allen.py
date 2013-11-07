# Settings local to deployment on Allen's computer

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'C:/Users/Allen/Desktop/Dropbox/backup/MIT Random/Simmons/Tech/SimmonsElections/results',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

SECRET_KEY = '^=l)5@w!ggq8=e!v&amp;fy7wq3zm4(!0ba98ai9r0yb3(&amp;nqx+2=-'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "C:/Users/Allen/Desktop/Dropbox/backup/MIT Random/Simmons/Tech/SimmonsElections/SimmonsElections/templates",
)

MEDIA_ROOT = ''

MEDIA_URL = ''

STATIC_ROOT = ''

STATIC_URL = '/static/'
