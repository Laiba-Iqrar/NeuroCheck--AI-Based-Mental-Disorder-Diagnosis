# core/assessment/depression.py
class DepressionAssessor:
    PHQ9_QUESTIONS = [
        {
            "text": "Little interest or pleasure in doing things",
            "options": [
                {"text": "Not at all", "score": 0},
                {"text": "Several days", "score": 1},
                {"text": "More than half the days", "score": 2},
                {"text": "Nearly every day", "score": 3}
            ]
        },
        {
            "text": "Feeling down, depressed, or hopeless",
            "options": [
                {"text": "Not at all", "score": 0},
                {"text": "Several days", "score": 1},
                {"text": "More than half the days", "score": 2},
                {"text": "Nearly every day", "score": 3}
            ]
        },
        # Add remaining 7 questions with same structure
    ]

    def __init__(self, score=0, current_question=0):
        self.score = score
        self.current_question = current_question

    def assess(self, answer: str):
        try:
            answer_score = int(answer)
            if not 0 <= answer_score <= 3:
                raise ValueError
        except (ValueError, TypeError):
            return {"error": "Please select a valid option (0-3)", "status": "error"}

        self.score += answer_score
        self.current_question += 1

        if self.current_question < len(self.PHQ9_QUESTIONS):
            return {
                "question": self.PHQ9_QUESTIONS[self.current_question]["text"],
                "options": [opt["text"] for opt in self.PHQ9_QUESTIONS[self.current_question]["options"]],
                "status": "continue"
            }
        return {
            "diagnosis": self._interpret_score(),
            "status": "complete"
        }

    def _interpret_score(self):
        if self.score >= 20:
            return "Severe depression - Urgent consultation recommended"
        elif self.score >= 15:
            return "Moderately severe depression"
        elif self.score >= 10:
            return "Moderate depression"
        elif self.score >= 5:
            return "Mild depression"
        return "Minimal depression - No significant symptoms"# core/assessment/depression.py
class DepressionAssessor:
    PHQ9_QUESTIONS = [
        {
            "text": "Little interest or pleasure in doing things",
            "options": [
                {"text": "Not at all", "score": 0},
                {"text": "Several days", "score": 1},
                {"text": "More than half the days", "score": 2},
                {"text": "Nearly every day", "score": 3}
            ]
        },
        {
            "text": "Feeling down, depressed, or hopeless",
            "options": [
                {"text": "Not at all", "score": 0},
                {"text": "Several days", "score": 1},
                {"text": "More than half the days", "score": 2},
                {"text": "Nearly every day", "score": 3}
            ]
        },
        # Add remaining 7 questions with same structure
    ]

    def __init__(self, score=0, current_question=0):
        self.score = score
        self.current_question = current_question

    def assess(self, answer: str):
        try:
            answer_score = int(answer)
            if not 0 <= answer_score <= 3:
                raise ValueError
        except (ValueError, TypeError):
            return {"error": "Please select a valid option (0-3)", "status": "error"}

        self.score += answer_score
        self.current_question += 1

        if self.current_question < len(self.PHQ9_QUESTIONS):
            return {
                "question": self.PHQ9_QUESTIONS[self.current_question]["text"],
                "options": [opt["text"] for opt in self.PHQ9_QUESTIONS[self.current_question]["options"]],
                "status": "continue"
            }
        return {
            "diagnosis": self._interpret_score(),
            "status": "complete"
        }

    def _interpret_score(self):
        if self.score >= 20:
            return "Severe depression - Urgent consultation recommended"
        elif self.score >= 15:
            return "Moderately severe depression"
        elif self.score >= 10:
            return "Moderate depression"
        elif self.score >= 5:
            return "Mild depression"
        return "Minimal depression - No significant symptoms"