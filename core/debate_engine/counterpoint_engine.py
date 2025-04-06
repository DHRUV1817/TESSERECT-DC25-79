"""
Counterpoint Engine for the Tesseract Project
Generates intelligent counterarguments for debate practice.
"""
import re
import random
from typing import List, Dict, Any, Optional

class CounterpointEngine:
    """Generates intelligent counterarguments for debate practice."""
    
    def __init__(self, level: int = 2):
        """
        Initialize the counterpoint engine with complexity level.
        
        Args:
            level: Complexity level (1-3) for counterargument generation
        """
        self.level = min(max(level, 1), 3)
        
        # Counterargument strategies by types
        self.strategy_templates = {
            "evidence_challenge": [
                "The evidence provided for {claim} is inadequate because {reason}.",
                "While {claim} may sound plausible, the evidence cited is problematic: {reason}."
            ],
            "causal_fallacy": [
                "The argument incorrectly assumes that {claimed_cause} causes {effect}, when in fact {alternative}.",
                "The causal relationship between {claimed_cause} and {effect} is questionable. A more likely explanation is {alternative}."
            ],
            "false_dichotomy": [
                "This argument presents a false choice between {option1} and {option2}. In reality, {alternative}.",
                "Reducing this complex issue to a choice between {option1} and {option2} ignores that {alternative}."
            ],
            "alternative_perspective": [
                "From a different perspective, {claim} actually leads to {alternative_outcome}.",
                "Looking at this issue through the lens of {perspective}, we see that {alternative_view}."
            ],
            "unintended_consequences": [
                "While {proposal} might achieve {intended_outcome}, it would also cause {negative_consequence}.",
                "The proposal to {proposal} overlooks the serious side effect of {negative_consequence}."
            ]
        }
        
        # Attack types categorization
        self.attack_types = {
            "evidence_challenge": "evidential",
            "causal_fallacy": "causal",
            "false_dichotomy": "logical",
            "alternative_perspective": "perspectival",
            "unintended_consequences": "consequential"
        }
        
    def generate_counterpoints(
        self, 
        argument: str, 
        topic: str = "",
        count: int = 3
    ) -> Dict[str, Any]:
        """
        Generate counterpoints to an argument.
        
        Args:
            argument: The argument text to counter
            topic: Optional topic context
            count: Number of counterpoints to generate
            
        Returns:
            Dict containing generated counterpoints and analysis
        """
        # Extract key components from the argument
        components = self._analyze_argument(argument, topic)
        
        # Generate counterpoints based on complexity level
        counterpoints = []
        
        # Determine which strategies to use based on complexity level
        strategies = self._select_strategies(components)
        
        # Generate counterpoints for each selected strategy
        for strategy in strategies[:count]:
            counterpoint = self._generate_counterpoint(components, strategy)
            if counterpoint:
                counterpoints.append(counterpoint)
        
        # If we couldn't generate enough counterpoints, fill with generic ones
        while len(counterpoints) < count:
            generic = self._generate_generic_counterpoint(components)
            if generic:
                counterpoints.append(generic)
            
        # Determine the strongest counterpoint
        strongest_counterpoint = self._find_strongest_counterpoint(counterpoints)
        
        # Calculate rebuttal difficulty
        rebuttal_difficulty = self._calculate_rebuttal_difficulty(counterpoints)
        
        return {
            "counterpoints": counterpoints,
            "strongest_counterpoint": strongest_counterpoint,
            "rebuttal_difficulty": rebuttal_difficulty,
            "argument_summary": components["claim"]
        }
    
    def _analyze_argument(self, argument: str, topic: str = "") -> Dict[str, Any]:
        """
        Extract key components from the argument for targeted counterpoints.
        
        Args:
            argument: The argument text to analyze
            topic: Optional topic context
            
        Returns:
            Dict containing extracted components
        """
        sentences = [s.strip() for s in argument.split('.') if s.strip()]
        
        # Try to identify the main claim
        claim = sentences[0] if sentences else argument
        
        # Extract potential evidence
        evidence = []
        for sentence in sentences[1:]:
            lower_sent = sentence.lower()
            if any(marker in lower_sent for marker in ["because", "since", "given that", "research", "studies", "data", "evidence"]):
                evidence.append(sentence)
        
        # Use topic if available and claim is short
        if topic and len(claim) < 50:
            enhanced_claim = f"{claim} regarding {topic}"
        else:
            enhanced_claim = claim
            
        return {
            "claim": enhanced_claim,
            "evidence": evidence,
            "full_text": argument,
            "topic": topic
        }
    
    def _select_strategies(self, components: Dict[str, Any]) -> List[str]:
        """
        Select appropriate counterargument strategies.
        
        Args:
            components: Extracted argument components
            
        Returns:
            List of selected strategy names
        """
        available_strategies = []
        
        # Evidence challenge if evidence is provided
        if components["evidence"]:
            available_strategies.append("evidence_challenge")
        
        # Include general strategies
        available_strategies.append("false_dichotomy")
        available_strategies.append("alternative_perspective")
        available_strategies.append("unintended_consequences")
        
        # Shuffle strategies for variety
        random.shuffle(available_strategies)
        
        # Select subset based on complexity level
        if self.level == 1:
            return available_strategies[:2]
        elif self.level == 2:
            return available_strategies[:3]
        else:
            return available_strategies[:4]
    
    def _generate_counterpoint(self, components: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        """
        Generate a counterpoint using a specific strategy.
        
        Args:
            components: Extracted argument components
            strategy: Strategy to apply
            
        Returns:
            Dict containing counterpoint details
        """
        if strategy not in self.strategy_templates:
            return None
            
        templates = self.strategy_templates[strategy]
        template = random.choice(templates)
        
        # Generate content based on strategy
        if strategy == "evidence_challenge":
            return self._generate_evidence_challenge(components, template)
        elif strategy == "causal_fallacy":
            return self._generate_causal_fallacy(components, template)
        elif strategy == "false_dichotomy":
            return self._generate_false_dichotomy(components, template)
        elif strategy == "alternative_perspective":
            return self._generate_alternative_perspective(components, template)
        elif strategy == "unintended_consequences":
            return self._generate_unintended_consequences(components, template)
        
        return None
        
    def _generate_evidence_challenge(self, components: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Generate an evidence challenge counterpoint."""
        claim = components["claim"]
        
        # Potential challenges to evidence
        challenges = [
            "it relies on outdated information",
            "the sample size is too small to be representative",
            "correlation doesn't imply causation in this case",
            "it fails to account for important factors",
            "the source is potentially biased"
        ]
        
        reason = random.choice(challenges)
        
        text = template.format(claim=claim, reason=reason)
        
        return {
            "text": text,
            "strategy": "evidence_challenge",
            "attack_type": self.attack_types["evidence_challenge"]
        }
        
    def _generate_causal_fallacy(self, components: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Generate a causal fallacy counterpoint."""
        claim = components["claim"]
        
        # Simple cause and effect extraction
        claimed_cause = "the proposed cause"
        effect = "the claimed effect"
        
        # Alternative explanations
        alternatives = [
            "there may be a third factor influencing both",
            "the relationship is more complex and multifaceted",
            "the correlation is coincidental rather than causal",
            "the causation may actually run in the opposite direction"
        ]
        
        alternative = random.choice(alternatives)
        
        text = template.format(claimed_cause=claimed_cause, effect=effect, alternative=alternative)
        
        return {
            "text": text,
            "strategy": "causal_fallacy",
            "attack_type": self.attack_types["causal_fallacy"]
        }
        
    def _generate_false_dichotomy(self, components: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Generate a false dichotomy counterpoint."""
        # Generate generic options
        topic = components["topic"] if components["topic"] else "this issue"
        option1 = f"completely supporting {topic}"
        option2 = f"completely opposing {topic}"
        
        # Alternative approaches
        alternatives = [
            f"there are many middle-ground positions that could be more effective",
            f"a more nuanced approach combines elements of both while avoiding extremes",
            f"the issue requires a case-by-case analysis rather than a one-size-fits-all solution"
        ]
        
        alternative = random.choice(alternatives)
        
        text = template.format(option1=option1, option2=option2, alternative=alternative)
        
        return {
            "text": text,
            "strategy": "false_dichotomy",
            "attack_type": self.attack_types["false_dichotomy"]
        }
        
    def _generate_alternative_perspective(self, components: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Generate an alternative perspective counterpoint."""
        claim = components["claim"]
        
        # Potential perspectives
        perspectives = [
            "economic efficiency",
            "social justice",
            "environmental sustainability",
            "individual liberty",
            "cultural values"
        ]
        perspective = random.choice(perspectives)
        
        # Alternative views
        alternative_views = [
            "we see different priorities emerge that challenge the original premise",
            "the argument's assumptions are revealed to be culturally biased",
            "the short-term benefits are overshadowed by long-term concerns"
        ]
        alternative_view = random.choice(alternative_views)
        
        # Possible alternative outcomes
        alternative_outcomes = [
            "different outcomes than those predicted",
            "unintended consequences that undermine the original goal",
            "benefits for some groups but harms for others"
        ]
        alternative_outcome = random.choice(alternative_outcomes)
        
        if "alternative_view" in template:
            text = template.format(
                claim=claim,
                perspective=perspective,
                alternative_view=alternative_view
            )
        else:
            text = template.format(
                claim=claim,
                alternative_outcome=alternative_outcome
            )
        
        return {
            "text": text,
            "strategy": "alternative_perspective",
            "attack_type": self.attack_types["alternative_perspective"]
        }
        
    def _generate_unintended_consequences(self, components: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Generate an unintended consequences counterpoint."""
        # Extract proposal from claim
        claim = components["claim"]
        proposal = claim
        topic = components["topic"] if components["topic"] else "the issue"
            
        # Generate intended outcome
        intended_outcomes = [
            f"improving {topic}",
            f"solving the problems with {topic}",
            f"addressing concerns about {topic}"
        ]
        intended_outcome = random.choice(intended_outcomes)
        
        # Potential negative consequences
        negative_consequences = [
            "creating perverse incentives that worsen the original problem",
            "disproportionately harming vulnerable populations",
            "excessive implementation costs that drain resources from other priorities",
            "establishing precedents that could be misused in other contexts",
            "creating a false sense of security while ignoring root causes"
        ]
        negative_consequence = random.choice(negative_consequences)
        
        text = template.format(
            proposal=proposal,
            intended_outcome=intended_outcome,
            negative_consequence=negative_consequence
        )
        
        return {
            "text": text,
            "strategy": "unintended_consequences",
            "attack_type": self.attack_types["unintended_consequences"]
        }
        
    def _generate_generic_counterpoint(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a generic counterpoint when specific strategies aren't applicable."""
        claim = components["claim"]
        
        # Generic counterpoint templates
        templates = [
            f"The argument that {claim} fails to consider important alternatives.",
            f"While {claim} has some merit, it overlooks critical factors that lead to a different conclusion.",
            f"The reasoning behind {claim} contains logical gaps that undermine its conclusion.",
            f"A more careful analysis of {claim} reveals flaws in its underlying assumptions."
        ]
        
        text = random.choice(templates)
        
        return {
            "text": text,
            "strategy": "generic_challenge",
            "attack_type": "general"
        }
        
    def _find_strongest_counterpoint(self, counterpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Determine the strongest counterpoint based on strategy effectiveness.
        
        Args:
            counterpoints: List of generated counterpoints
            
        Returns:
            Dict representing the strongest counterpoint
        """
        if not counterpoints:
            return None
            
        # Strategy strength rankings (higher is stronger)
        strategy_strength = {
            "evidence_challenge": 5,
            "causal_fallacy": 4,
            "false_dichotomy": 3,
            "alternative_perspective": 2,
            "unintended_consequences": 4,
            "generic_challenge": 1
        }
        
        # Find counterpoint with highest strength score
        strongest = max(counterpoints, key=lambda cp: strategy_strength.get(cp["strategy"], 0))
        return strongest
        
    def _calculate_rebuttal_difficulty(self, counterpoints: List[Dict[str, Any]]) -> float:
        """
        Calculate how difficult it would be to rebut these counterpoints.
        
        Args:
            counterpoints: List of generated counterpoints
            
        Returns:
            Difficulty score (0-1)
        """
        if not counterpoints:
            return 0.0
            
        # Base difficulty by level
        base_difficulty = 0.3 * self.level
        
        # Add difficulty based on strongest counterpoint
        strongest = self._find_strongest_counterpoint(counterpoints)
        if strongest:
            strategy_difficulty = {
                "evidence_challenge": 0.2,
                "causal_fallacy": 0.15,
                "false_dichotomy": 0.1,
                "alternative_perspective": 0.05,
                "unintended_consequences": 0.15,
                "generic_challenge": 0.05
            }
            
            base_difficulty += strategy_difficulty.get(strongest["strategy"], 0)
            
        # Cap at 1.0
        return min(1.0, base_difficulty)