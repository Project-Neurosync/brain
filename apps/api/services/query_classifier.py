"""LLM-powered query classifier to determine if a query needs RAG or can be answered directly."""

import json
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class QueryClassifier:
    """LLM-powered classifier that determines if queries need RAG retrieval or direct response."""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        
        # Classification prompt template - completely dynamic, no hardcoded examples
        self.classification_prompt = """You are an intelligent query classifier for NeuroSync, a software development team assistant.

Analyze the user's query and determine if it needs RAG (Retrieval-Augmented Generation) to access project-specific data, or if it can be answered directly.

**Use RAG when the query:**
- Asks about specific project details, code, or files
- Requests information that would be in project documentation, issues, or discussions
- Seeks status updates, progress reports, or project-specific data
- References team members, decisions, or project history
- Needs context from integrated tools (GitHub, Jira, Slack, etc.)

**Use DIRECT response when the query:**
- Is conversational, greeting, or acknowledgment
- Asks general questions not specific to their project
- Requests explanations of concepts or tutorials
- Is about the AI assistant itself
- Is vague and needs clarification first
- Can be answered with general knowledge

Analyze the intent and specificity of the query. Be intelligent about distinguishing between project-specific requests and general conversation.

Respond with ONLY a JSON object:
{
  "needs_rag": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of your decision"
}

Query: "{query}"
Project context: {project_context}

Classification:"""
    
    async def classify_query(self, query: str, project_id: str = None) -> Tuple[bool, float, str]:
        """
        Use LLM to classify if a query needs RAG retrieval.
        
        Args:
            query: The user's query text
            project_id: Optional project ID context
            
        Returns:
            Tuple of (needs_rag: bool, confidence: float, reason: str)
        """
        try:
            if not self.llm_service:
                # Fallback to simple heuristics if no LLM available
                return self._fallback_classify(query, project_id)
            
            # Prepare context information
            project_context = f"User is working on project {project_id}" if project_id else "No specific project context"
            
            # Create classification prompt
            prompt = self.classification_prompt.format(
                query=query.strip(),
                project_context=project_context
            )
            
            # Get LLM classification
            response = await self.llm_service.complete(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=150
            )
            
            # Parse JSON response
            if response.text:
                try:
                    # Extract JSON from response (handle potential extra text)
                    response_text = response.text.strip()
                    
                    # Clean up common JSON formatting issues
                    response_text = response_text.replace('\n', ' ').replace('\t', ' ')
                    
                    if '{' in response_text:
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        json_text = response_text[json_start:json_end]
                        
                        # Remove any extra whitespace or newlines that might break JSON
                        json_text = ' '.join(json_text.split())
                        
                        classification = json.loads(json_text)
                        
                        needs_rag = classification.get('needs_rag', True)
                        confidence = float(classification.get('confidence', 0.7))
                        reasoning = classification.get('reasoning', 'LLM classification')
                        
                        logger.info(f"LLM classification: needs_rag={needs_rag}, confidence={confidence:.2f}, reasoning={reasoning}")
                        return needs_rag, confidence, reasoning
                        
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse LLM classification response: {e}")
                    logger.warning(f"Raw response: {response.text}")
            
            # Fallback if parsing fails
            return self._fallback_classify(query, project_id)
            
        except Exception as e:
            logger.error(f"Error in LLM query classification: {e}")
            return self._fallback_classify(query, project_id)
    
    def _fallback_classify(self, query: str, project_id: str = None) -> Tuple[bool, float, str]:
        """Simple fallback classification when LLM is not available."""
        query_lower = query.lower().strip()
        
        # Simple greetings and basic queries
        simple_indicators = ['hello', 'hi', 'hey', 'what is', 'define', 'explain', 'how are you', 'who are you']
        if any(indicator in query_lower for indicator in simple_indicators) and len(query) < 50:
            return False, 0.8, "Simple greeting or general question"
        
        # Project-specific indicators
        rag_indicators = ['project', 'code', 'issue', 'bug', 'commit', 'status', 'show me', 'find', 'github', 'jira']
        if any(indicator in query_lower for indicator in rag_indicators) or project_id:
            return True, 0.8, "Contains project-specific terms or has project context"
        
        # Default to RAG for safety
        return True, 0.6, "Default to RAG for unknown query type"
    
    async def get_classification_info(self, query: str, project_id: str = None) -> Dict:
        """Get detailed classification information for debugging."""
        needs_rag, confidence, reason = await self.classify_query(query, project_id)
        
        return {
            'needs_rag': needs_rag,
            'confidence': confidence,
            'reason': reason,
            'query_length': len(query),
            'word_count': len(query.split()),
            'has_project_context': bool(project_id),
            'classifier_type': 'LLM-powered' if self.llm_service else 'fallback'
        }

# Global classifier instance (will be initialized with LLM service)
query_classifier = QueryClassifier()
