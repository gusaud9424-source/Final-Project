import secrets


def generate_numeric_code(length=6):
    return "".join(secrets.choice("0123456789") for _ in range(length))
