from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Create a superuser with email and password'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Superuser email')
        parser.add_argument('--password', required=True, help='Superuser password')
        parser.add_argument('--first-name', default='', help='Superuser first name')
        parser.add_argument('--last-name', default='', help='Superuser last name')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        try:
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'User with email {email} already exists')
                )
                return

            # Create superuser
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {email}')
            )

        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Validation error: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
