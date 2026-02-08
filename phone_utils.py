_HAVE_PHONENUMBERS = True
try:
    import phonenumbers
    from phonenumbers import NumberParseException, PhoneNumberFormat, region_code_for_number, format_number
except Exception:
    phonenumbers = None
    NumberParseException = Exception
    PhoneNumberFormat = None
    region_code_for_number = lambda *_: None
    format_number = lambda *_: None
    _HAVE_PHONENUMBERS = False
    import warnings
    warnings.warn("'phonenumbers' package is not installed. Install it with: python -m pip install phonenumbers")

# A small curated list of countries to show in forms. Key is ISO 3166-1 alpha-2 code.
COUNTRY_CHOICES = [
    ("HR", "Croatia (+385)"),
    ("US", "United States (+1)"),
    ("GB", "United Kingdom (+44)"),
    ("DE", "Germany (+49)"),
    ("FR", "France (+33)"),
    ("IT", "Italy (+39)"),
    ("ES", "Spain (+34)"),
]

# Dial codes for the above countries (ISO2 -> country calling code)
DIAL_CODES = {
    "HR": "385",
    "US": "1",
    "GB": "44",
    "DE": "49",
    "FR": "33",
    "IT": "39",
    "ES": "34",
}

# Countries that commonly use a leading zero in national format (heuristic)
LEADING_ZERO_COUNTRIES = {"HR", "GB", "DE", "FR", "IT", "ES"}


def example_for_country(country_code: str) -> dict:
    """Return example numbers for a country.

    Examples:
      - national: a national-format example (may include leading zero)
      - international: E.164 example with 9 digits '123456789' after the country code
      - display: short string joining both for UI
    """
    digits = "123456789"  # 9 digits using 1-9 as requested
    dial = DIAL_CODES.get(country_code, "")
    international = f"+{dial}{digits}" if dial else f"+{digits}"
    # Use plain 9-digit example as requested (no leading zero prefix)
    national = digits
    display = digits
    return {"national": national, "international": international, "display": display}


def normalize_phone(number: str, default_region: str = None) -> dict:
    """Parse and validate a phone number.

    Args:
      number: The user-entered phone number. Can be in national form (e.g. 0996662838)
              or in international form (e.g. +385996662838).
      default_region: Optional 2-letter region (e.g. 'HR') used when number has no + prefix.

    Returns:
      dict with keys: 'e164' (e.g. '+385996662838') and 'country' (ISO alpha-2, e.g. 'HR').

    Raises:
      ValueError if the number is invalid or cannot be parsed.
    """
    if not _HAVE_PHONENUMBERS:
        raise ValueError("phonenumbers library is not installed. Install with: python -m pip install phonenumbers")

    if not number or not number.strip():
        raise ValueError("empty phone number")

    raw = number.strip()
    try:
        if raw.startswith("+"):
            parsed = phonenumbers.parse(raw, None)
        else:
            # If no default_region provided, try to infer from raw E.164 - but parse will fail without region.
            if not default_region:
                raise ValueError("Missing country for national-format phone number")
            parsed = phonenumbers.parse(raw, default_region)

        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number")

        e164 = format_number(parsed, PhoneNumberFormat.E164)
        country = region_code_for_number(parsed)
        return {"e164": e164, "country": country, "parsed": parsed}

    except NumberParseException as e:
        raise ValueError(str(e))


def validate_phone(number: str, default_region: str = None, required_digits: int = 9) -> dict:
    """Validate phone and ensure the national significant number has required_digits length.

    Returns same dict as normalize_phone but without the parsed object.
    Raises ValueError with a helpful message when validation fails.
    """
    if not _HAVE_PHONENUMBERS:
        raise ValueError("phonenumbers library is not installed. Install with: python -m pip install phonenumbers")

    res = normalize_phone(number, default_region)
    parsed = res.get('parsed')
    if not parsed:
        raise ValueError('Unable to parse phone number')

    nat = str(parsed.national_number)
    if len(nat) != required_digits:
        raise ValueError(f"Phone number must have {required_digits} digits in national format (without country code)")

    # Remove parsed from result before returning
    res.pop('parsed', None)
    return res


def get_country_from_e164(e164_number: str) -> str:
    """Return the ISO region code for a given E.164 phone number, or None."""
    if not _HAVE_PHONENUMBERS:
        return None
    try:
        parsed = phonenumbers.parse(e164_number, None)
        return region_code_for_number(parsed)
    except Exception:
        return None
