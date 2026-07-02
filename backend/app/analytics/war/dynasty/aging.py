class AgingCurve:

    def multiplier(
        self,
        age: float,
        position: str,
    ) -> float:

        return 1.0

# class DynastyAgeCurve:


#     def multiplier(
#         self,
#         age: float,
#     ) -> float:


#         if age <= 23:
#             return 1.20

#         if age <= 25:
#             return 1.10

#         if age <= 27:
#             return 1.00

#         if age <= 29:
#             return 0.85

#         if age <= 31:
#             return 0.65

#         return 0.45