from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission


class Command(BaseCommand):
    def execute(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(User)
        Permission.objects.create(codename='can_access_sorm', name='Can Access SORM', content_type=ct)
