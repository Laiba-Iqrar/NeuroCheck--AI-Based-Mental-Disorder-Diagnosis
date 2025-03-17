# utils/helpers.py

def get_recommendations(diagnosis: str) -> list:
    """Return clinical recommendations based on PHQ-9 score interpretation"""
    recommendations = {
        'severe': [
            "Immediate consultation with mental health professional",
            "Crisis hotline: 1-800-273-TALK (8255)",
            "Consider psychiatric evaluation for medication options",
            "Weekly therapy sessions recommended"
        ],
        'moderately severe': [
            "Schedule clinical evaluation within 1 week",
            "Begin CBT-based interventions",
            "Mood tracking exercise",
            "Consider antidepressant therapy"
        ],
        'moderate': [
            "Follow-up assessment in 2 weeks",
            "Guided mindfulness exercises",
            "Behavioral activation planning",
            "Peer support group referral"
        ],
        'mild': [
            "Self-help resources (workbook link)",
            "Weekly mood check-ins",
            "Physical activity planning",
            "Sleep hygiene education"
        ],
        'minimal': [
            "Regular self-monitoring",
            "Preventive education materials",
            "Monthly check-ins recommended"
        ]
    }

    # Map diagnosis text to recommendation keys
    if 'severe' in diagnosis.lower():
        return recommendations['severe']
    if 'moderately severe' in diagnosis.lower():
        return recommendations['moderately severe']
    if 'moderate' in diagnosis.lower():
        return recommendations['moderate']
    if 'mild' in diagnosis.lower():
        return recommendations['mild']
    
    return recommendations['minimal']