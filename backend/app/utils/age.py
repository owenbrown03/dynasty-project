from datetime import date, datetime


def calculate_age(
    birth_date: str | None,
) -> float | None:

    if not birth_date:
        return None

    try:
        dob = datetime.strptime(
            birth_date,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        return None

    today = date.today()

    years = (
        today.year
        - dob.year
        - (
            (today.month, today.day)
            < (dob.month, dob.day)
        )
    )

    try:
        last_birthday = dob.replace(
            year=today.year,
        )
    except ValueError:
        # Feb 29 birthday on non-leap year
        last_birthday = date(
            today.year,
            2,
            28,
        )

    if last_birthday > today:
        try:
            last_birthday = dob.replace(
                year=today.year - 1,
            )
        except ValueError:
            last_birthday = date(
                today.year - 1,
                2,
                28,
            )

    days_since_birthday = (
        today - last_birthday
    ).days

    return round(
        years + days_since_birthday / 365.25,
        1,
    )