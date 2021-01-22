import os  # noqa


# _envrion = dict(os.environ)  # noqa
# _envrion['DJANGO_SETTINGS_MODULE'] = 'oel.settings'
# _envrion['OEL_DB_NAME'] = 'OEL_TEST_DB'
# os.environ.update(_envrion)

# os.environ.setdefault('OEL_DB_NAME', 'OEL_TEST_DB')  # noqa
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oel.settings")  # noqa
from django.core.wsgi import get_wsgi_application  # noqa
application = get_wsgi_application()
