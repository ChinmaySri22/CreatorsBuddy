"""
Configuration module for YouTube Script Generator
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration settings"""
    
    # API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    # Paths
    DATA_DIR = "Data/processed"
    OUTPUT_DIR = "output"
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    NUM_TRANSCRIPTS_TO_LOAD = int(os.getenv('NUM_TRANSCRIPTS_TO_LOAD', '25'))
    MAX_SCRIPT_LENGTH_CHARS = int(os.getenv('MAX_SCRIPT_LENGTH_CHARS', '20000'))
    SPEECH_WPM = int(os.getenv('SPEECH_WPM', '140'))  # average Hindi speaking pace
    
    # Default Script Parameters
    DEFAULT_TONE = os.getenv('DEFAULT_TONE', 'friendly_and_informative')
    DEFAULT_TARGET_AUDIENCE = os.getenv('DEFAULT_TARGET_AUDIENCE', 'tech_enthusiasts')
    DEFAULT_LENGTH_MINUTES = int(os.getenv('DEFAULT_LENGTH_MINUTES', '10'))
    
    # Valid Tones
    VALID_TONES = [
        'friendly_and_informative',
        'enthusiastic_and_energetic', 
        'professional_and_formal',
        'casual_and_conversational',
        'dramatic_and_engaging',
        'technical_and_detailed',
        'humorous_and_entertaining'
    ]
    
    # Valid Target Audiences
    VALID_AUDIENCES = [
        'tech_enthusiasts',
        'general_audience',
        'beginners',
        'professionals',
        'students',
        'gamers',
        'content_creators'
    ]
    
    # Supported Length Categories
    LENGTH_CATEGORIES = {
        'short': (2, 5),      # 2-5 minutes
        'medium': (5, 12),    # 5-12 minutes  
        'long': (12, 20),     # 12-20 minutes
        'very_long': (20, 40) # 20-40 minutes
    }
    
    # YouTube Creator Mapping (based on actual transcript data)
    YOUTUBE_CREATORS = {
        'Trakin Tech': {
            'style': 'tech_reviewer_indian',
            'language_mix': 'hinglish_heavy',
            'tone_preference': 'enthusiastic_and_energetic',
            'specialization': 'smartphone_reviews'
        },
        'TechBar': {
            'style': 'tech_reviewer_detailed', 
            'language_mix': 'hinglish_balanced',
            'tone_preference': 'friendly_and_informative',
            'specialization': 'comprehensive_tech_reviews'
        }
    }
    
    # Language Processing Settings
    MIN_TRANSCRIPT_WORDS = 100
    MAX_CONTEXT_WINDOW_GPT = 15000  # Leave room for generated content
    
    @classmethod
    def validate_config(cls):
        """Validate configuration on startup"""
        errors = []
        
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
            
        if not os.path.exists(cls.DATA_DIR):
            errors.append(f"Data directory {cls.DATA_DIR} does not exist")
            
        if errors:
            raise ValueError("Configuration errors: " + "; ".join(errors))
        
        return True

