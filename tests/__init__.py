import os  # noqa


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oel.settings")  # noqa
from django.core.wsgi import get_wsgi_application  # noqa
application = get_wsgi_application()
