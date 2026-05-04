import argparse
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
    parser = argparse.ArgumentParser(description="Create an admin/super admin user.")
    parser.add_argument("--org-id", type=int, default=os.environ.get("ADMIN_ORG_ID"))
    parser.add_argument("--org-name", default=os.environ.get("ADMIN_ORG_NAME", "Default Organization"))
    parser.add_argument("--email", default=os.environ.get("ADMIN_EMAIL", "admin@local"))
    parser.add_argument("--display-name", default=os.environ.get("ADMIN_DISPLAY_NAME", "Admin"))
    parser.add_argument("--password", default=os.environ.get("ADMIN_PASSWORD", "Sansons1$"))
    parser.add_argument("--role", default=os.environ.get("ADMIN_ROLE", "admin"))
    args = parser.parse_args()

    org_id = int(args.org_id) if args.org_id else None
    org_name = args.org_name
    admin_email = args.email
    admin_display_name = args.display_name
    admin_password = args.password
    role_name = args.role.strip()

    if org_id:
        org = Organization.objects.filter(id=org_id).first()
        if not org:
            print(f"Organization id {org_id} not found")
            sys.exit(1)
    else:
        org, _ = Organization.objects.get_or_create(
            name=org_name,
            defaults={
                "legal_name": org_name,
                "status": "active",
            },
        )

    for default_role_name, description in DEFAULT_ROLES:
        Role.objects.get_or_create(
            org=org,
            name=default_role_name,
            defaults={"description": description},
        )

    role = Role.objects.filter(org=org, name__iexact=role_name).first()
    if not role:
        role = Role.objects.create(org=org, name=role_name, description=f"{role_name} role")

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
    print(f"org={org.id} email={user.email} role={role.name} created={created}")


if __name__ == "__main__":
    main()
