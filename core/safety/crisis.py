class CrisisDetector:
    CRISIS_KEYWORDS = {
        'suicide': ['kill myself', 'end it all', 'suicide'],
        'self_harm': ['cutting', 'self harm'],
        'emergency': ['help me', 'can\'t breathe']
    }

    def detect_crisis(self, text: str):
        text_lower = text.lower()
        for category, keywords in self.CRISIS_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return {
                    "is_crisis": True,
                    "category": category,
                    "resources": self._get_resources(category)
                }
        return {"is_crisis": False}

    def _get_resources(self, category):
        return {
            'suicide': ["National Suicide Prevention Lifeline: 1-800-273-TALK (8255)"],
            'self_harm': ["Self-Harm Hotline: 1-800-DONT-CUT"],
            # ... others
        }[category]