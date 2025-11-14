from django.core.management.base import BaseCommand
from mpesa.models import MpesaConfiguration
from decouple import config

class Command(BaseCommand):
    help = 'Setup initial M-Pesa configuration'

    def handle(self, *args, **options):
        # Check if configuration already exists
        if MpesaConfiguration.objects.exists():
            self.stdout.write(
                self.style.WARNING('M-Pesa configuration already exists')
            )
            return

        # Create default configuration (sandbox)
        config_obj = MpesaConfiguration.objects.create(
            name='Sandbox Configuration',
            consumer_key=config('MPESA_CONSUMER_KEY', default=''),
            consumer_secret=config('MPESA_CONSUMER_SECRET', default=''),
            business_short_code=config('MPESA_BUSINESS_SHORT_CODE', default='174379'),
            passkey=config('MPESA_PASSKEY', default=''),
            is_live=False
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully created M-Pesa sandbox configuration')
        )