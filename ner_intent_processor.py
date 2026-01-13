"""
NER and Intent Recognition Processor for YouTube Videos

This module provides:
1. Named Entity Recognition (NER) using spaCy
2. Context extraction from transcripts
3. Intent recognition using LLM
"""

import re
from typing import List, Dict, Optional, Tuple
from collections import Counter
import spacy
from anthropic import Anthropic

from config import config


class NERIntentProcessor:
    """Process transcripts for NER, context, and intent recognition"""
    
    def __init__(self):
        """Initialize NER and intent processor"""
        self.nlp = None
        self.llm_client = None
        self._load_models()
    
    def _load_models(self):
        """Load spaCy and LLM models"""
        try:
            # Load spaCy model (use en_core_web_sm for NER)
            print("   Loading spaCy NER model...")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("   ⚠️  spaCy model not found. Installing...")
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
                self.nlp = spacy.load("en_core_web_sm")
            print("   ✅ spaCy model loaded")
        except Exception as e:
            print(f"   ⚠️  Could not load spaCy: {e}")
            print("   Install with: pip install spacy && python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Initialize LLM client
        try:
            self.llm_client = Anthropic(api_key=config.llm.api_key)
            print("   ✅ LLM client initialized")
        except Exception as e:
            print(f"   ⚠️  Could not initialize LLM: {e}")
            self.llm_client = None
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extract named entities from text using spaCy
        
        Args:
            text: Input text
            
        Returns:
            Dictionary mapping entity types to lists of entities
        """
        if not self.nlp:
            return {}
        
        # Process text
        doc = self.nlp(text)
        
        # Group entities by type
        entities_by_type = {}
        
        for ent in doc.ents:
            entity_type = ent.label_
            entity_text = ent.text.strip()
            
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            
            # Avoid duplicates
            if entity_text not in [e['text'] for e in entities_by_type[entity_type]]:
                entities_by_type[entity_type].append({
                    'text': entity_text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'label': entity_type
                })
        
        return entities_by_type
    
    def extract_key_concepts(self, text: str, top_n: int = 20) -> List[Dict]:
        """
        Extract key concepts and topics from transcript
        
        Args:
            text: Transcript text
            top_n: Number of top concepts to return
            
        Returns:
            List of concept dictionaries with frequency
        """
        if not self.nlp:
            return []
        
        # Process text
        doc = self.nlp(text)
        
        # Extract noun phrases and important terms
        concepts = []
        
        # Get noun phrases
        for chunk in doc.noun_chunks:
            text_lower = chunk.text.lower().strip()
            # Filter out common words and short phrases
            if len(text_lower) > 3 and text_lower not in ['the', 'a', 'an', 'this', 'that', 'these', 'those']:
                concepts.append(text_lower)
        
        # Get important named entities
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW']:
                concepts.append(ent.text.lower().strip())
        
        # Count frequencies
        concept_counts = Counter(concepts)
        
        # Return top concepts
        top_concepts = []
        for concept, count in concept_counts.most_common(top_n):
            top_concepts.append({
                'concept': concept,
                'frequency': count,
                'importance': min(count / len(concepts) * 100, 100) if concepts else 0
            })
        
        return top_concepts
    
    def recognize_intent(self, title: str, description: str, transcript: str) -> Dict[str, any]:
        """
        Recognize the intent/purpose of the video using LLM
        
        Args:
            title: Video title
            description: Video description
            transcript: Video transcript (first 2000 chars)
            
        Returns:
            Dictionary with intent classification
        """
        if not self.llm_client:
            return {'intent': 'unknown', 'confidence': 0.0}
        
        # Truncate transcript for analysis
        transcript_sample = transcript[:2000] if len(transcript) > 2000 else transcript
        
        prompt = f"""Analyze this YouTube video and determine its primary intent/purpose.

Title: {title}
Description: {description[:500]}
Transcript Sample: {transcript_sample}

Classify the video into ONE of these categories:
1. Educational/Tutorial - Teaching concepts, explaining topics, how-to guides
2. Conference/Talk - Conference presentation, keynote, panel discussion
3. Product Demo - Demonstrating a product or service
4. Interview - Interview with an expert or notable person
5. News/Update - News, updates, announcements
6. Entertainment - Entertainment content, casual discussion
7. Research/Academic - Research findings, academic discussion
8. Other - Other types of content

Respond with ONLY a JSON object in this format:
{{
    "intent": "category_name",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "key_topics": ["topic1", "topic2", "topic3"],
    "target_audience": "description of intended audience"
}}"""

        try:
            response = self.llm_client.messages.create(
                model=config.llm.model,
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract JSON from response
            content = response.content[0].text
            
            # Try to extract JSON
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                import json
                intent_data = json.loads(json_match.group())
                return intent_data
            
            # Fallback: parse text response
            return {
                'intent': 'unknown',
                'confidence': 0.5,
                'reasoning': content[:200]
            }
            
        except Exception as e:
            print(f"   ⚠️  Error recognizing intent: {e}")
            return {'intent': 'unknown', 'confidence': 0.0, 'error': str(e)}
    
    def extract_context(self, transcript: str, segments: List[Dict]) -> Dict[str, any]:
        """
        Extract contextual information from transcript
        
        Args:
            transcript: Full transcript text
            segments: List of transcript segments with timestamps
            
        Returns:
            Dictionary with contextual information
        """
        context = {
            'total_duration': 0,
            'speaker_changes': 0,
            'key_moments': [],
            'technical_terms': [],
            'questions_asked': [],
            'conclusions': []
        }
        
        # Calculate total duration
        if segments:
            last_segment = segments[-1]
            context['total_duration'] = last_segment.get('end_seconds', 0)
        
        # Extract questions
        question_pattern = r'[^.!?]*\?[^.!?]*'
        questions = re.findall(question_pattern, transcript)
        context['questions_asked'] = [q.strip() for q in questions[:10]]
        
        # Extract technical terms (capitalized words, acronyms)
        technical_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', transcript)
        technical_terms += re.findall(r'\b[A-Z]{2,}\b', transcript)
        context['technical_terms'] = list(set(technical_terms))[:20]
        
        # Identify key moments (segments with high information density)
        if segments:
            for segment in segments[:20]:  # Sample first 20 segments
                text = segment.get('text', '')
                # Simple heuristic: longer segments with specific keywords
                if len(text) > 100:
                    keywords = ['important', 'key', 'main', 'summary', 'conclusion', 'takeaway']
                    if any(kw in text.lower() for kw in keywords):
                        context['key_moments'].append({
                            'timestamp': segment.get('start', ''),
                            'text': text[:200]
                        })
        
        return context
    
    def process_video(self, title: str, description: str, transcript: str, segments: List[Dict]) -> Dict[str, any]:
        """
        Complete processing: NER, context, and intent recognition
        
        Args:
            title: Video title
            description: Video description
            transcript: Full transcript
            segments: List of transcript segments
            
        Returns:
            Dictionary with all extracted information
        """
        print("\n🧠 Processing video with NER, context, and intent recognition...")
        
        result = {
            'entities': {},
            'key_concepts': [],
            'intent': {},
            'context': {}
        }
        
        # Extract entities
        if self.nlp:
            print("   Extracting named entities...")
            result['entities'] = self.extract_entities(transcript)
            entity_count = sum(len(v) for v in result['entities'].values())
            print(f"   ✅ Found {entity_count} entities")
        
        # Extract key concepts
        if self.nlp:
            print("   Extracting key concepts...")
            result['key_concepts'] = self.extract_key_concepts(transcript, top_n=20)
            print(f"   ✅ Found {len(result['key_concepts'])} key concepts")
        
        # Recognize intent
        if self.llm_client:
            print("   Recognizing intent...")
            result['intent'] = self.recognize_intent(title, description, transcript)
            print(f"   ✅ Intent: {result['intent'].get('intent', 'unknown')}")
        
        # Extract context
        print("   Extracting context...")
        result['context'] = self.extract_context(transcript, segments)
        print(f"   ✅ Context extracted")
        
        return result


# Global instance
_processor = None

def get_processor() -> NERIntentProcessor:
    """Get or create global processor instance"""
    global _processor
    if _processor is None:
        _processor = NERIntentProcessor()
    return _processor

