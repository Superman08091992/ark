class KennyAgent:
    def validate_plan(self, plan):
        print("Kenny validating plan")
        return True

    def execute(self, plan, validation_passed):
        if not validation_passed:
            raise Exception("Validation required")
        print("Kenny executing with full authorization")
        return {"execution": f"done: {plan}"}
