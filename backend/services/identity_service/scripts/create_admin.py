import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils import timezone
from django.contrib.auth.hashers import make_password

from infrastructure.db.core.models import Organization, Role, User, UserCredential, UserRole

DEFAULT_ROLES = [
    ("super admin", "Platform owner with full access"),
    ("admin", "System administrator"),
    ("supervisor", "Department supervisor"),
    ("housekeeper", "Housekeeping staff"),
    ("maintenance", "Maintenance technician"),
    ("front desk", "Front desk agent"),
    ("concierge", "Concierge staff"),
    ("guest experience", "Guest experience team"),
    ("compliance", "Compliance officer"),
    ("security", "Security staff"),
    ("inventory", "Inventory controller"),
    ("procurement", "Procurement officer"),
]


def main():
    org_name = os.environ.get("ADMIN_ORG_NAME", "Default Organization")
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@local")
    admin_display_name = os.environ.get("ADMIN_DISPLAY_NAME", "Admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Sansons1$")

    org, _ = Organization.objects.get_or_create(
        name=org_name,
        defaults={
            "legal_name": org_name,
            "status": "active",
        },
    )

    for role_name, description in DEFAULT_ROLES:
        Role.objects.get_or_create(
            org=org,
            name=role_name,
            defaults={"description": description},
        )

    role = Role.objects.filter(org=org, name__iexact="admin").first()
    if not role:
        role = Role.objects.create(org=org, name="admin", description="System administrator")

    user, created = User.objects.get_or_create(
        org=org,
        email=admin_email,
        defaults={
            "display_name": admin_display_name,
            "status": "active",
        },
    )

    credential, _ = UserCredential.objects.get_or_create(user=user)
    credential.password_hash = make_password(admin_password)
    credential.last_password_change_at = timezone.now()
    credential.save()

    UserRole.objects.get_or_create(user=user, role=role)

    print("Admin user ready")
    print(f"org={org.id} email={user.email} role=admin created={created}")


if __name__ == "__main__":
    main()
