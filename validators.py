import re

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def validate_password(password: str, username: str | None = None) -> None:
    """Validate password strength.

    Rules:
      - At least 8 characters
      - At least one lowercase, one uppercase, one digit, one special character
      - Must not contain the username (case-insensitive)

    Raises:
      ValueError with a user-friendly message when validation fails.
    """
    if not password:
        raise ValueError("Password is required")
    if not PASSWORD_REGEX.match(password):
        raise ValueError("Password must be at least 8 characters and include upper and lower case letters, a number, and a special character")
    if username and username.lower() in password.lower():
        raise ValueError("Password must not contain the username")


def validate_username(username: str) -> None:
    # As requested, allow any length, but ensure non-empty
    if not username or not username.strip():
        raise ValueError("Username is required")


def validate_name(name: str) -> None:
    # name can be any length, but ensure non-empty
    if not name or not name.strip():
        raise ValueError("Name is required")


# Phone validation: require exactly 9 digits (any combination)
import re

PHONE_RE = re.compile(r"^\d{9}$")

def validate_phone(number: str, country: str = None, required_digits: int = 9) -> None:
    if not number or not number.strip():
        raise ValueError("Phone number is required")
    raw = number.strip()
    if not PHONE_RE.match(raw):
        raise ValueError(f"Phone number must be exactly {required_digits} digits")


