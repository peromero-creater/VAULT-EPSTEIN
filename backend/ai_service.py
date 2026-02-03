"""
AI Service for Document Analysis and Story Generation
Supports OpenAI, Google Gemini, and Grok
"""
import os
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import json

load_dotenv()

class AIService:
    def __init__(self):
        self.provider = os.getenv('AI_PROVIDER', 'grok').lower()  # Default to Grok
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.google_key = os.getenv('GOOGLE_AI_API_KEY')
        self.grok_key = os.getenv('GROK_API_KEY')
        
        # Initialize the appropriate client
        self.client = None
        
        if self.provider == 'grok' and self.grok_key:
            # Grok uses OpenAI-compatible API
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.grok_key,
                    base_url="https://api.x.ai/v1"
                )
                self.model = "grok-beta"  # or grok-4-latest
                print("✅ Grok AI initialized (specialized Epstein knowledge)")
            except ImportError:
                print("OpenAI library needed for Grok. Run: pip install openai")
        
        elif self.provider == 'openai' and self.openai_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_key)
                self.model = "gpt-4-turbo-preview"
                print("✅ OpenAI GPT-4 initialized")
            except ImportError:
                print("OpenAI library not installed. Run: pip install openai")
        
        elif self.provider == 'google' and self.google_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_key)
                self.client = genai.GenerativeModel('gemini-pro')
                self.model = 'gemini-pro'
                print("✅ Google Gemini initialized")
            except ImportError:
                print("Google AI library not installed. Run: pip install google-generativeai")
    
    def is_available(self) -> bool:
        """Check if AI service is configured and ready"""
        return self.client is not None
    
    def analyze_document(self, text: str, max_length: int = 4000) -> Dict:
        """
        Analyze document text to extract:
        - Key entities (people, organizations, locations)
        - Relationships
        - Key facts
        - Summary
        """
        if not self.is_available():
            return {'error': 'AI service not configured'}
        
        # Truncate text if too long
        text = text[:max_length]
        
        prompt = f"""Analyze this document excerpt from the Epstein case files.

Extract:
1. People mentioned (names only)
2. Organizations mentioned
3. Locations/Countries mentioned
4. Key relationships between entities
5. A brief summary (2-3 sentences)

Document text:
{text}

Respond in JSON format:
{{
    "people": ["name1", "name2"],
    "organizations": ["org1"],
    "locations": ["location1"],
    "relationships": [
        {{"source": "person1", "target": "person2", "type": "associate", "description": "brief description"}}
    ],
    "summary": "Brief summary here"
}}
"""
        
        try:
            if self.provider in ['openai', 'grok']:
                # Both use OpenAI-compatible API
                system_prompt = "You are an expert analyst specializing in the Jeffrey Epstein case files and court documents." if self.provider == 'grok' else "You are an expert analyst specializing in extracting structured information from legal documents."
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                result = json.loads(response.choices[0].message.content)
                return result
            
            elif self.provider == 'google':
                response = self.client.generate_content(prompt)
                # Try to parse JSON from response
                result = json.loads(response.text)
                return result
            
        except Exception as e:
            print(f"AI analysis error: {e}")
            return {'error': str(e)}
    
    def generate_narrative(self, entities: List[str], context: str = "") -> str:
        """Generate a story/narrative about the entities"""
        if not self.is_available():
            return "AI service not configured"
        
        entities_str = ", ".join(entities[:10])  # Limit to 10 entities
        
        prompt = f"""Based on the Epstein case documents, create a concise 2-3 sentence narrative about: {entities_str}

Context: {context}

The narrative should be factual, based on documented evidence, and highlight key connections or events. Keep it brief and impactful."""
        
        try:
            if self.provider in ['openai', 'grok']:
                system_prompt = "You are an investigative journalist with deep knowledge of the Jeffrey Epstein case, connections, and court proceedings." if self.provider == 'grok' else "You are a journalist writing about the Epstein case based on court documents."
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == 'google':
                response = self.client.generate_content(prompt)
                return response.text.strip()
        
        except Exception as e:
            print(f"Narrative generation error: {e}")
            return f"Unable to generate narrative: {str(e)}"
    
    def find_connections(
        self, 
        entity_name: str, 
        document_snippets: List[str]
    ) -> List[Dict]:
        """
        Discover connections for an entity across multiple documents
        Returns list of discovered relationships
        """
        if not self.is_available():
            return []
        
        # Combine snippets (limit total length)
        combined_text = "\n\n---\n\n".join(document_snippets[:5])[:6000]
        
        prompt = f"""Analyze these document excerpts and identify all connections and relationships involving "{entity_name}".

For each connection found, specify:
- Who they're connected to
- The type of relationship (associate, business partner, co-passenger, etc.)
- A brief description of the connection evidence

Documents:
{combined_text}

Respond in JSON format:
{{
    "connections": [
        {{
            "target": "person/org name",
            "type": "relationship type",
            "description": "evidence description"
        }}
    ]
}}
"""
        
        try:
            if self.provider in ['openai', 'grok']:
                system_prompt = "You are an expert investigator with comprehensive knowledge of the Epstein network, flight logs, and connections between individuals." if self.provider == 'grok' else "You are an investigative analyst finding connections in legal documents."
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                result = json.loads(response.choices[0].message.content)
                return result.get('connections', [])
            
            elif self.provider == 'google':
                response = self.client.generate_content(prompt)
                result = json.loads(response.text)
                return result.get('connections', [])
        
        except Exception as e:
            print(f"Connection discovery error: {e}")
            return []
    
    def summarize_country_intel(self, country_code: str, documents: List[Dict]) -> str:
        """Generate AI summary for a country's intelligence"""
        if not self.is_available():
            return "AI service not configured"
        
        # Extract key info from documents
        doc_previews = []
        for doc in documents[:5]:  # Limit to 5 docs
            preview = doc.get('text', '')[:500]
            doc_previews.append(preview)
        
        combined = "\n\n".join(doc_previews)
        
        prompt = f"""Summarize the intelligence related to {country_code} from these Epstein case documents.

Focus on:
- Key individuals mentioned in connection with this country
- Significant events or activities
- Properties or locations

Keep it to 2-3 sentences.

Documents:
{combined}
"""
        
        try:
            if self.provider in ['openai', 'grok']:
                system_prompt = "You are an intelligence analyst specializing in geopolitical connections related to the Epstein case." if self.provider == 'grok' else "You are an intelligence analyst."
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,
                    max_tokens=150
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == 'google':
                response = self.client.generate_content(prompt)
                return response.text.strip()
        
        except Exception as e:
            print(f"Country summary error: {e}")
            return f"Unable to generate summary for {country_code}"


# Singleton instance
_ai_service = None

def get_ai_service() -> AIService:
    """Get the global AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
