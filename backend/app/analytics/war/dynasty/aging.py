class AgingCurve:
    """
    Placeholder dynasty aging curve.

    Dynasty WAR currently applies no age-based multiplier.
    Keep the policy centralized here so a future curve can be
    introduced without changing downstream calculators.
    """

    def multiplier(
        self,
        age: float,
        position: str,
    ) -> float:
        return 1.0
