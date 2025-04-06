"""
Filler Detector for the Tesseract Project
Analyzes speech for fillers and hesitations.
"""
import re
import os
import httpx
import json
from typing import Dict, Any, List, Optional

class FillerDetector:
    """Detects filler words and hesitations in speech transcripts."""
    
    def __init__(self, use_ai: bool = True):
        """
        Initialize the filler detector with common filler patterns.
        
        Args:
            use_ai: Whether to use AI for enhanced analysis when available
        """
        # Common filler words and phrases
        self.filler_words = [
            "um", "uh", "er", "ah", "like", "you know", "sort of", "kind of",
            "basically", "literally", "actually", "so", "well", "I mean"
        ]
        
        # Regular expression patterns for detecting fillers
        self.filler_patterns = [
            r'\b' + re.escape(word) + r'\b' 
            for word in self.filler_words
        ]
        
        # Combined pattern for easier matching
        self.combined_pattern = re.compile('|'.join(self.filler_patterns), re.IGNORECASE)
        
        # AI configuration
        self.use_ai = use_ai
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = "gpt-3.5-turbo"
        
        # Cache for previously analyzed transcripts
        self.analysis_cache = {}
    
    def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze a speech transcript for filler words and hesitations.
        
        Args:
            transcript: The text transcript of the speech to analyze
            
        Returns:
            Dict containing analysis results and improvement suggestions
        """
        # Check cache first
        cache_key = hash(transcript)
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # Try AI-powered analysis if enabled
        if self.use_ai and self.openai_api_key:
            try:
                ai_result = self._analyze_with_ai(transcript)
                # Update cache
                self.analysis_cache[cache_key] = ai_result
                return ai_result
            except Exception as e:
                print(f"Error using AI analysis: {str(e)}. Falling back to local analysis.")
        
        # Find all filler words
        fillers = self._find_fillers(transcript)
        
        # Calculate filler density
        word_count = len(transcript.split())
        filler_count = sum(fillers.values())
        filler_density = filler_count / max(1, word_count)
        
        # Calculate fluency score
        fluency_score = self._calculate_fluency_score(filler_density)
        
        result = {
            "filler_count": filler_count,
            "word_count": word_count,
            "filler_density": filler_density,
            "filler_breakdown": fillers,
            "fluency_score": fluency_score,
            "improvement_suggestions": self._generate_suggestions(fillers, fluency_score)
        }
        
        # Update cache
        self.analysis_cache[cache_key] = result
        return result
    
    def _analyze_with_ai(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze speech transcript using OpenAI API for more accurate analysis.
        
        Args:
            transcript: The speech transcript to analyze
            
        Returns:
            Dict containing enhanced analysis results
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
        You are an expert in speech analysis. Analyze the given speech transcript and provide a structured evaluation.
        Focus on filler words, hesitations, and overall fluency. Your response should be a valid JSON object with the following structure:
        {
            "filler_count": integer,
            "word_count": integer,
            "filler_density": float (0-1),
            "filler_breakdown": {"word1": count1, "word2": count2, ...},
            "fluency_score": float (0-1),
            "improvement_suggestions": [string],
            "additional_insights": string (any extra observations)
        }
        """
        
        user_prompt = f"Analyze this speech transcript for fillers and hesitations: {transcript}\n\nProvide the analysis in JSON format only."
        
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
    
    def _find_fillers(self, text: str) -> Dict[str, int]:
        """Find and count all filler words in the text."""
        fillers = {}
        for filler in self.filler_words:
            pattern = re.compile(r'\b' + re.escape(filler) + r'\b', re.IGNORECASE)
            matches = pattern.findall(text)
            if matches:
                fillers[filler] = len(matches)
        
        return fillers
    
    def _calculate_fluency_score(self, filler_density: float) -> float:
        """Calculate an overall fluency score based on filler density."""
        # Start with a perfect score
        score = 1.0
        
        # Penalize for filler density
        if filler_density > 0.0:
            penalty = min(0.8, filler_density * 4)  # Cap penalty at 0.8
            score -= penalty
            
        return max(0.1, score)  # Ensure score is at least 0.1
    
    def _generate_suggestions(self, fillers: Dict[str, int], fluency_score: float) -> List[str]:
        """Generate improvement suggestions based on analysis results."""
        suggestions = []
        
        # Suggestions for fillers
        if fillers:
            common_fillers = sorted(fillers.items(), key=lambda x: x[1], reverse=True)[:3]
            
            if common_fillers:
                filler_list = ", ".join([f"'{f[0]}'" for f in common_fillers])
                suggestions.append(f"Watch out for common filler words: {filler_list}")
        
        # General fluency suggestions
        if fluency_score < 0.7:
            suggestions.append("Record yourself speaking and listen for fillers and hesitations")
            suggestions.append("Practice speaking more slowly and deliberately to reduce fillers")
            suggestions.append("Prepare outlines for your speeches to improve fluency")
        
        if not suggestions:
            suggestions.append("Your speech fluency is good. Focus on content and delivery.")
            
        return suggestions
        
    def highlight_fillers(self, transcript: str) -> str:
        """
        Create a highlighted version of transcript with fillers marked.
        
        Args:
            transcript: Original speech transcript
            
        Returns:
            Text with fillers wrapped in ** for emphasis
        """
        def replace_match(match):
            return f"**{match.group(0)}**"
            
        return self.combined_pattern.sub(replace_match, transcript)
    
    def get_common_fillers(self) -> List[str]:
        """Get the list of common filler words being detected."""
        return self.filler_words
    
    def add_custom_filler(self, word: str) -> None:
        """
        Add a custom filler word to the detection list.
        
        Args:
            word: The filler word to add
        """
        if word and word not in self.filler_words:
            self.filler_words.append(word)
            # Update patterns
            self.filler_patterns.append(r'\b' + re.escape(word) + r'\b')
            self.combined_pattern = re.compile('|'.join(self.filler_patterns), re.IGNORECASE)