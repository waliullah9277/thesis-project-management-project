from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, password=None, **extra_fields):
        role = extra_fields.get("role")

        if role == "STUDENT":
            if not extra_fields.get("student_id"):
                raise ValueError("Student ID is required.")
        else:
            email = extra_fields.get("email")
            if not email:
                raise ValueError("Email is required.")
            extra_fields["email"] = self.normalize_email(email)

        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("email", email)
        extra_fields.setdefault("role", "SUPER_ADMIN")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_first_login", False)
        extra_fields.setdefault("must_change_password", False)

        return self.create_user(password=password, **extra_fields)