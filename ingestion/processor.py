import re
import spacy
from typing import List, Tuple, Dict

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_md")
except:
    # Fallback if model not loaded/installed yet
    print("Warning: spaCy model 'en_core_web_md' not found. NER will be limited.")
    nlp = None

# PII RegEx patterns
EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_PATTERN = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
ADDRESS_PATTERN = r'\d{1,5}\s\w.\s(\w\s?){1,3}\s(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr)'

def mask_pii(text: str) -> str:
    """Masks emails, phones, and basic addresses in text."""
    text = re.sub(EMAIL_PATTERN, "[EMAIL]", text)
    text = re.sub(PHONE_PATTERN, "[PHONE]", text)
    # Simple address masking - can be more aggressive if needed
    text = re.sub(ADDRESS_PATTERN, "[ADDRESS]", text)
    return text

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extracts PERSON, ORG, GPE, and LOC from text using spaCy."""
    if not nlp:
        return {"PERSON": [], "ORG": [], "GPE": [], "LOC": []}
    
    doc = nlp(text)
    entities = {
        "PERSON": [],
        "ORG": [],
        "GPE": [],
        "LOC": []
    }
    
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text.strip())
            
    # Deduplicate
    for label in entities:
        entities[label] = list(set(entities[label]))
        
    return entities

def get_text_quality(text: str) -> float:
    """Estimates text quality based on length and common word density."""
    if not text:
        return 0.0
    # Very basic heuristic: longer text with spaces is usually better than empty/gibberish
    # In real world, would check against dictionary or OCR confidence scores
    length_weight = min(len(text) / 1000, 1.0)
    space_density = text.count(' ') / (len(text) + 1)
    return (length_weight * 0.5) + (min(space_density * 4, 1.0) * 0.5)
