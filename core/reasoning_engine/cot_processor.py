"""
Chain of Thought Processor for the Tesseract Project
Provides analysis of debate arguments with reasoning steps.
"""
import re
import os
import json
import httpx
from typing import List, Dict, Any, Optional

class ChainOfThoughtProcessor:
    """Implements chain-of-thought reasoning for debate arguments."""
    
    def __init__(self, complexity_level: int = 1, use_ai: bool = True):
        """
        Initialize the COT processor with complexity level.
        
        Args:
            complexity_level: Controls depth of reasoning (1-3)
            use_ai: Whether to use AI for enhanced analysis when available
        """
        self.complexity_level = min(max(complexity_level, 1), 3)
        self.use_ai = use_ai
        
        # Keywords that signal evidence
        self.evidence_keywords = [
            "because", "since", "given that", "research", "studies", "data", 
            "evidence", "according to", "example", "for instance"
        ]
        
        # AI configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = "gpt-3.5-turbo"
        
        # Cache for previously processed arguments
        self.process_cache = {}
        
    def process_argument(self, argument_text: str) -> Dict[str, Any]:
        """
        Process an argument using chain-of-thought reasoning.
        
        Args:
            argument_text: The text of the argument to analyze
            
        Returns:
            Dict containing steps of reasoning and evaluation
        """
        # Check cache first
        cache_key = hash(f"{argument_text}_{self.complexity_level}")
        if cache_key in self.process_cache:
            return self.process_cache[cache_key]
        
        # Try AI-powered analysis if enabled
        if self.use_ai and self.openai_api_key:
            try:
                ai_result = self._process_with_ai(argument_text)
                # Cache the result
                self.process_cache[cache_key] = ai_result
                return ai_result
            except Exception as e:
                print(f"Error using AI analysis: {str(e)}. Falling back to local analysis.")
        
        # Basic clean-up of text
        clean_text = argument_text.strip()
        
        # Extract key components
        claim = self._extract_claim(clean_text)
        evidence = self._extract_evidence(clean_text)
        conclusion = self._extract_conclusion(clean_text)
        
        # Generate reasoning steps
        reasoning_steps = self._generate_reasoning_steps(claim, evidence, conclusion)
        
        # Evaluate argument quality
        validity_score = self._calculate_validity_score(claim, evidence, conclusion)
        
        result = {
            "original_argument": argument_text,
            "claim": claim,
            "evidence": evidence,
            "conclusion": conclusion,
            "reasoning_steps": reasoning_steps,
            "validity_score": validity_score,
            "improvement_suggestions": self._generate_suggestions(validity_score, claim, evidence, conclusion),
            "counterpoints": self._generate_simple_counterpoints(claim),
            "strongest_counterpoint": None
        }

        # Set the strongest counterpoint if available
        if result["counterpoints"]:
            result["strongest_counterpoint"] = result["counterpoints"][0]
        
        # Also add a rebuttal difficulty score for frontend compatibility
        result["rebuttal_difficulty"] = 0.5
        
        # Cache the result
        self.process_cache[cache_key] = result
        return result
    
    def _process_with_ai(self, argument_text: str) -> Dict[str, Any]:
        """
        Process an argument using OpenAI API for chain-of-thought reasoning.
        
        Args:
            argument_text: The argument text to analyze
            
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
        
        # Construct a prompt that will return structured JSON, adjusted for complexity level
        system_prompt = f"""
        You are an expert in argument analysis using chain-of-thought reasoning. 
        Analyze the given argument at complexity level {self.complexity_level} (on a scale of 1-3) and provide a structured evaluation.
        
        Your response should be a valid JSON object with the following structure:
        {{
            "claim": string (the main claim of the argument),
            "evidence": [strings] (list of evidence statements supporting the claim),
            "conclusion": string (the conclusion drawn from evidence),
            "reasoning_steps": [strings] (list of reasoning steps, depth based on complexity level {self.complexity_level}),
            "validity_score": float (0-1),
            "improvement_suggestions": [string],
            "counterpoints": [
                {{
                    "text": string,
                    "strategy": string,
                    "attack_type": string
                }}
            ]
        }}
        """
        
        user_prompt = f"Analyze this argument using chain-of-thought reasoning: {argument_text}\n\nProvide the analysis in JSON format only."
        
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
                
                # Add original argument to the result
                analysis["original_argument"] = argument_text
                return analysis
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _extract_claim(self, text: str) -> str:
        """Extract the main claim from the argument text."""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if not sentences:
            return ""
            
        # Use first sentence as the claim
        return sentences[0]
    
    def _extract_evidence(self, text: str) -> List[str]:
        """Extract supporting evidence from the argument text."""
        evidence_list = []
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        for sentence in sentences[1:]:  # Skip the first sentence (claim)
            if any(keyword in sentence.lower() for keyword in self.evidence_keywords):
                evidence_list.append(sentence)
        
        return evidence_list
    
    def _extract_conclusion(self, text: str) -> str:
        """Extract the conclusion from the argument text."""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) <= 1:  # Need at least 2 sentences
            return ""
            
        # Check if last sentence contains conclusion indicators
        conclusion_indicators = ["therefore", "thus", "hence", "in conclusion", "consequently"]
        if any(indicator in sentences[-1].lower() for indicator in conclusion_indicators):
            return sentences[-1]
            
        # If no explicit indicators, use last sentence if different from claim
        if sentences[-1] != self._extract_claim(text):
            return sentences[-1]
            
        return ""
    
    def _generate_reasoning_steps(self, claim: str, evidence: List[str], conclusion: str) -> List[str]:
        """Generate chain-of-thought reasoning steps based on complexity level."""
        steps = []
        
        # Basic steps (level 1)
        steps.append(f"Identified claim: {claim}")
        
        if evidence:
            for i, ev in enumerate(evidence):
                steps.append(f"Evidence {i+1}: {ev}")
        else:
            steps.append("No explicit evidence was provided to support the claim.")
        
        if conclusion:
            steps.append(f"Conclusion: {conclusion}")
        else:
            steps.append("No explicit conclusion was drawn from the evidence.")
            
        # Add more complex reasoning for higher levels
        if self.complexity_level >= 2:
            # Analyze evidence strength
            if evidence:
                evidence_quality = "The evidence appears to be "
                if len(evidence) >= 2:
                    evidence_quality += "relatively strong with multiple supporting points."
                else:
                    evidence_quality += "somewhat limited with only one supporting point."
                steps.append(evidence_quality)
            
            # Analyze logical flow
            if claim and evidence and conclusion:
                steps.append("The argument has a complete structure with claim, evidence, and conclusion.")
            elif claim and evidence:
                steps.append("The argument provides evidence but lacks a clear conclusion.")
            elif claim and conclusion:
                steps.append("The argument states a conclusion but lacks supporting evidence.")
                
        # Add even more detailed analysis for level 3
        if self.complexity_level >= 3:
            # Consider potential counterarguments
            steps.append("A potential counterargument could challenge the assumption that the evidence directly supports the claim.")
            
            # Analyze evidence relevance
            if evidence:
                steps.append("The relevance of the evidence to the claim could be strengthened with more direct connections.")
            
        return steps
    
    def _calculate_validity_score(self, claim: str, evidence: List[str], conclusion: str) -> float:
        """Calculate a validity score based on argument components."""
        score = 0.5  # Start with neutral score
        
        # Add points for having components
        if claim:
            score += 0.1
        
        if evidence:
            score += 0.2 * min(1, len(evidence) / 3)  # Up to 0.2 for evidence (max at 3 pieces)
        
        if conclusion:
            score += 0.1
            
        # Add points for completeness
        if claim and evidence and conclusion:
            score += 0.1
            
        return min(1.0, score)  # Cap at 1.0
    
    def _generate_suggestions(self, validity_score: float, claim: str, evidence: List[str], conclusion: str) -> List[str]:
        """Generate improvement suggestions based on the analysis."""
        suggestions = []
        
        if not claim:
            suggestions.append("Start with a clear claim that states your position.")
        
        if not evidence:
            suggestions.append("Add specific evidence to support your claim (facts, statistics, or examples).")
        elif len(evidence) < 2:
            suggestions.append("Include more pieces of evidence to strengthen your argument.")
        
        if not conclusion:
            suggestions.append("End with a conclusion that follows from your evidence.")
            
        # Add more specific suggestions based on validity score
        if validity_score < 0.7:
            if validity_score < 0.4:
                suggestions.append("Consider restructuring your argument to follow a clear claim-evidence-conclusion format.")
            else:
                suggestions.append("Make sure your evidence directly supports your claim and leads to your conclusion.")
                
        return suggestions
    
    def _generate_simple_counterpoints(self, claim: str) -> List[Dict[str, Any]]:
        """Generate simple counterpoints for the claim."""
        if not claim:
            return []
            
        # Create some generic counterpoints
        counterpoints = [
            {
                "text": f"The claim that {claim} may not consider all perspectives.",
                "strategy": "alternative_perspective",
                "attack_type": "perspectival"
            },
            {
                "text": f"While {claim} has merit, it overlooks important factors.",
                "strategy": "contextual_challenge",
                "attack_type": "contextual"
            },
            {
                "text": f"The evidence for {claim} might be insufficient.",
                "strategy": "evidence_challenge",
                "attack_type": "evidential"
            }
        ]
        
        return counterpoints