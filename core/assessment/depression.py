class DepressionAssessor:
    def __init__(self, score=0, current_question=0):
        self.score = score
        self.current_question = current_question
        self.questions = self._load_questions()  # Instance-specific questions

    def _load_questions(self):
        """Dynamic question loader"""
        return [
            {
                "text": "Okay, I'll ask some questions to understand how you've been feeling. Have you had little interest or pleasure in doing things?",
                "options": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Have you been feeling down, depressed, or hopeless?",
                "options": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            # Add remaining questions here
        ]

    # Rest of the class methods remain the same as previous implementation

    def assess(self, answer: str):
        try:
            answer_score = int(answer)
            if not 0 <= answer_score <= 3:
                return {"error": "Please select a valid option (0-3)", "status": "error"}
        except (ValueError, TypeError):
            return {"error": "Please enter a number between 0-3", "status": "error"}

        self.score += answer_score
        self.current_question += 1

        if self.current_question < len(self.questions):
            return {
                "question": self.questions[self.current_question]["text"],
                "options": [opt["text"] for opt in self.questions[self.current_question]["options"]],
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