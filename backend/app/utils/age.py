from datetime import date, datetime


def calculate_age(birthdate) -> float:

    if not birthdate:
        return 99

    if isinstance(birthdate, str):

        # handles YYYY-MM-DD
        birthdate = datetime.strptime(
            birthdate,
            "%Y-%m-%d"
        ).date()

    today = date.today()

    days = (
        today - birthdate
    ).days

    return round(
        days / 365.25,
        2,
    )