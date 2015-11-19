from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Do nothing, other than shadow djangos syncdb command.'

    def handle(self, *args, **options):
        pass
