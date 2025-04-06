"""
Argument Validator for the Tesseract Project
Detects logical fallacies and evaluates argument validity using AI.
"""
import re
import os
import json
import httpx
from typing import List, Dict, Any, Optional

class ArgumentValidator:
    """Detects logical fallacies and validates debate arguments."""
    
    def __init__(self, use_openai: bool = True):
        """Initialize the argument validator with fallacy patterns and API configurations."""
        # Dictionary of common fallacy patterns and their descriptions
        self.fallacy_patterns = {
            "ad_hominem": {
                "patterns": ["attack", "person", "character", "stupid", "idiot", "incompetent"],
                "description": "Attacking the person instead of addressing their argument",
                "example": "We can't trust her research because she's politically biased",
                "severity": 0.8
            },
            "straw_man": {
                "patterns": ["not what", "didn't say", "misrepresent", "exaggerat"],
                "description": "Misrepresenting an opponent's argument to make it easier to attack",
                "example": "You think we should let everyone in without checking",
                "severity": 0.7
            },
            "false_dichotomy": {
                "patterns": ["either", "or", "only two", "only choice", "black and white"],
                "description": "Presenting only two options when others exist",
                "example": "Either we cut taxes or the economy will collapse",
                "severity": 0.6
            },
            "appeal_to_authority": {
                "patterns": ["expert", "authority", "professor", "doctor", "scientist said"],
                "description": "Using an authority figure to support an argument without providing evidence",
                "example": "Dr. Smith says this treatment works, so it must be effective",
                "severity": 0.5
            },
            "slippery_slope": {
                "patterns": ["lead to", "next thing", "first step", "eventually", "ultimately"],
                "description": "Asserting that a small step will lead to significant negative consequences",
                "example": "If we allow this exception, soon there will be no rules at all",
                "severity": 0.6
            }
        }
        
        # Set up APIs for enhanced validation
        self.use_openai = use_openai
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = "gpt-3.5-turbo"  # Default model
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        
        # Cache for previously validated arguments
        self.validation_cache = {}
    
    def validate_argument(self, argument_text: str) -> Dict[str, Any]:
        """
        Validate an argument for logical fallacies and other issues.
        
        Args:
            argument_text: The text of the argument to validate
            
        Returns:
            Dict containing validation results and detected fallacies
        """
        # Check cache first
        cache_key = hash(argument_text)
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
            
        # Try AI-powered validation if enabled
        if self.use_openai and self.openai_api_key:
            try:
                ai_result = self._validate_with_openai(argument_text)
                # Cache the result
                self.validation_cache[cache_key] = ai_result
                return ai_result
            except Exception as e:
                print(f"Error using OpenAI validation: {str(e)}. Falling back to local validation.")
        
        # Fall back to local validation methods
        # Check for various fallacies
        detected_fallacies = self._detect_fallacies(argument_text)
        
        # Evaluate structural integrity
        structure_analysis = self._analyze_structure(argument_text)
        
        # Calculate overall validity score
        validity_score = self._calculate_validity_score(detected_fallacies, structure_analysis)
        
        # Generate improvement suggestions
        suggestions = self._generate_suggestions(detected_fallacies, structure_analysis)
        
        result = {
            "validity_score": validity_score,
            "detected_fallacies": detected_fallacies,
            "structure_analysis": structure_analysis,
            "improvement_suggestions": suggestions
        }
        
        # Cache the result
        self.validation_cache[cache_key] = result
        return result
    
    def _validate_with_openai(self, argument_text: str) -> Dict[str, Any]:
        """
        Validate argument using OpenAI API for more accurate analysis.
        
        Args:
            argument_text: The argument text to analyze
            
        Returns:
            Dict containing enhanced validation results
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is not set")
            
        # Prepare the API request
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        
        # Construct a prompt that will return structured JSON
        system_prompt = """
        You are an expert in argument analysis. Analyze the given argument and provide a structured evaluation.
        Your response should be a valid JSON object with the following structure:
        {
            "validity_score": float (0-1),
            "detected_fallacies": [
                {
                    "fallacy_type": string,
                    "description": string,
                    "severity": float (0-1),
                    "context": string (the text surrounding the fallacy)
                }
            ],
            "structure_analysis": {
                "has_claim": boolean,
                "has_evidence": boolean,
                "has_conclusion": boolean,
                "sentence_count": integer,
                "has_complete_structure": boolean
            },
            "improvement_suggestions": [string]
        }
        """
        
        user_prompt = f"Analyze this argument: {argument_text}\n\nProvide the analysis in JSON format only."
        
        payload = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,  # Lower temperature for more consistent results
            "response_format": {"type": "json_object"}  # Ensure JSON response
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # Extract the JSON content from the response
                content = result["choices"][0]["message"]["content"]
                analysis = json.loads(content)
                return analysis
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _validate_with_huggingface(self, argument_text: str) -> Dict[str, Any]:
        """
        Validate argument using HuggingFace Inference API as a fallback.
        
        Args:
            argument_text: The argument text to analyze
            
        Returns:
            Dict containing validation results
        """
        if not self.hf_api_key:
            raise ValueError("HuggingFace API key is not set")
            
        # Use a suitable HuggingFace model for text classification
        url = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"
        headers = {"Authorization": f"Bearer {self.hf_api_key}"}
        
        # This is a simplified example - in practice, you would use a more specialized model
        payload = {"inputs": argument_text}
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # Process the result and convert to our format
                # This is just placeholder logic - you'd need to adapt this to the actual model output
                score = 0.5  # Default score
                if isinstance(result, list) and len(result) > 0:
                    if "score" in result[0]:
                        score = result[0]["score"]
                        
                # Fall back to local detection for other components
                detected_fallacies = self._detect_fallacies(argument_text)
                structure_analysis = self._analyze_structure(argument_text)
                suggestions = self._generate_suggestions(detected_fallacies, structure_analysis)
                
                return {
                    "validity_score": score,
                    "detected_fallacies": detected_fallacies,
                    "structure_analysis": structure_analysis,
                    "improvement_suggestions": suggestions
                }
        except Exception as e:
            raise Exception(f"HuggingFace API error: {str(e)}")
    
    def _detect_fallacies(self, text: str) -> List[Dict[str, Any]]:
        """Detect logical fallacies in the argument text."""
        text_lower = text.lower()
        detected = []
        
        for fallacy_name, fallacy_info in self.fallacy_patterns.items():
            for pattern in fallacy_info["patterns"]:
                pattern_regex = r'\b' + re.escape(pattern.lower()) + r'\b'
                if re.search(pattern_regex, text_lower):
                    # Find the context around the matched pattern
                    match = re.search(pattern_regex, text_lower)
                    if match:
                        start_pos = max(0, match.start() - 20)
                        end_pos = min(len(text_lower), match.end() + 20)
                        context = text_lower[start_pos:end_pos]
                    else:
                        context = ""
                    
                    detected.append({
                        "fallacy_type": fallacy_name,
                        "description": fallacy_info["description"],
                        "matched_pattern": pattern,
                        "example": fallacy_info["example"],
                        "severity": fallacy_info["severity"],
                        "context": "..." + context + "..."
                    })
                    break  # Once we've matched a pattern for this fallacy, move to next fallacy
        
        return detected
    
    def _analyze_structure(self, text: str) -> Dict[str, Any]:
        """Analyze the structural integrity of the argument."""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Basic structure analysis
        has_claim = len(sentences) > 0  # Assume first sentence is claim
        
        # Look for evidence indicators
        evidence_indicators = ["because", "since", "given that", "research", "studies", "data", "evidence"]
        has_evidence = any(indicator in text.lower() for indicator in evidence_indicators)
        
        # Look for conclusion indicators
        conclusion_indicators = ["therefore", "thus", "hence", "consequently", "so", "conclude"]
        has_conclusion = any(indicator in text.lower() for indicator in conclusion_indicators)
        
        # If no explicit conclusion indicator but more than one sentence, check last sentence
        if not has_conclusion and len(sentences) > 1:
            last_sentence = sentences[-1].lower()
            has_conclusion = any(word in last_sentence for word in ["should", "must", "need", "recommend"])
            
        return {
            "has_claim": has_claim,
            "has_evidence": has_evidence,
            "has_conclusion": has_conclusion,
            "sentence_count": len(sentences),
            "has_complete_structure": has_claim and has_evidence and has_conclusion
        }
    
    def _calculate_validity_score(self, fallacies: List[Dict[str, Any]], structure: Dict[str, Any]) -> float:
        """Calculate an overall validity score based on fallacies and structure."""
        # Start with a base score
        score = 0.7
        
        # Penalize for each fallacy detected, adjusted by severity
        for fallacy in fallacies:
            score -= fallacy["severity"] * 0.1
        
        # Adjust based on structure
        if not structure["has_claim"]:
            score -= 0.2
        if not structure["has_evidence"]:
            score -= 0.2
        if not structure["has_conclusion"]:
            score -= 0.1
        
        # Bonus for good structure
        if structure["has_complete_structure"]:
            score += 0.1
            
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _generate_suggestions(self, fallacies: List[Dict[str, Any]], structure: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions based on validation results."""
        suggestions = []
        
        # Suggestions for fallacies
        if fallacies:
            for fallacy in fallacies[:3]:  # Limit to top 3 fallacies to avoid overwhelming
                suggestions.append(f"Avoid {fallacy['fallacy_type'].replace('_', ' ')}: {fallacy['description']}.")
        
        # Suggestions for structure
        if not structure["has_claim"]:
            suggestions.append("Include a clear main claim or thesis statement at the beginning of your argument.")
        if not structure["has_evidence"]:
            suggestions.append("Add specific evidence to support your claim (facts, statistics, or examples).")
        if not structure["has_conclusion"]:
            suggestions.append("Include a conclusion that ties your evidence to your claim.")
        
        if structure["sentence_count"] < 3:
            suggestions.append("Expand your argument with more supporting details and evidence.")
            
        return suggestions
    
    def highlight_fallacies(self, argument_text: str) -> Dict[str, Any]:
        """
        Create a highlighted version of text with fallacies marked.
        
        Args:
            argument_text: Original argument text
            
        Returns:
            Dict with original text and marked version highlighting fallacies
        """
        fallacies = self._detect_fallacies(argument_text)
        highlighted_text = argument_text
        
        # Create markers for each fallacy
        for fallacy in fallacies:
            pattern = fallacy["matched_pattern"]
            pattern_regex = r'\b' + re.escape(pattern) + r'\b'
            replacement = f'**{pattern}**'  # Mark with asterisks for highlighting
            highlighted_text = re.sub(pattern_regex, replacement, highlighted_text, flags=re.IGNORECASE)
        
        return {
            "original": argument_text,
            "highlighted": highlighted_text,
            "fallacies": fallacies
        }