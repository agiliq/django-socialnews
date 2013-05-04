DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'socialnews_db',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}
EMAIL_HOST = ''
EMAIL_HOST_USER= ''
EMAIL_FROM = ""
EMAIL_HOST_PASSWORD= ''
EMAIL_PORT= ''
SEND_BROKEN_LINK_EMAILS = True
DEFAULT_FROM_EMAIL = ""
SERVER_MAIL= ""
