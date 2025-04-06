"""
Improved Socratic Questioner for the Tesseract Project
Generates probing questions that challenge assumptions in arguments and provides answer hints.
"""

import re
import random
from typing import List, Dict, Any
from collections import Counter

class SocraticQuestioner:
    """Generates probing questions using the Socratic method with answer hints."""
    
    def __init__(self):
        """Initialize the Socratic questioner with question templates and hint patterns."""
        # Question templates organized by category
        self.question_templates = {
            "clarification": [
                "What do you mean by {term}?",
                "Could you explain {term} in more detail?",
                "How would you define {term} in this context?"
            ],
            "assumption": [
                "What are you assuming when you say {statement}?",
                "Is it always true that {statement}?",
                "What justifies the assumption that {statement}?"
            ],
            "evidence": [
                "What evidence supports your claim that {statement}?",
                "How do you know that {statement}?",
                "Could you point to specific data that demonstrates {statement}?"
            ],
            "alternative": [
                "Are there alternative explanations for {phenomenon}?",
                "Have you considered other perspectives on {phenomenon}?",
                "What would someone who disagrees with you say about {phenomenon}?"
            ],
            "implication": [
                "If {statement} is true, what else must be true?",
                "What are the consequences if everyone followed your reasoning about {statement}?",
                "What might be some unintended results of {statement}?"
            ],
            "counter": [
                "What would be a strong objection to your position that {statement}?",
                "How would you respond to someone who argues that {counter_position}?",
                "What is the best argument against your view that {statement}?"
            ]
        }
        
        # Answer hint templates for each question category
        self.hint_templates = {
            "clarification": [
                "A good answer would provide a precise definition of the term, possibly with examples.",
                "Consider providing both a general definition and how the term specifically applies in your argument.",
                "Think about distinguishing this term from related concepts to show precise understanding."
            ],
            "assumption": [
                "Identify the unstated beliefs or premises your argument relies on.",
                "Consider whether your assumption holds true in all circumstances or if there are exceptions.",
                "Reflect on whether your audience would share this assumption and how to justify it."
            ],
            "evidence": [
                "Strong answers cite specific studies, statistics, examples, or authoritative sources.",
                "Consider both the quality and quantity of evidence supporting your position.",
                "Address how recent and relevant your evidence is to the specific claim."
            ],
            "alternative": [
                "Explore explanations that could also account for the same facts but lead to different conclusions.",
                "Consider perspectives from different disciplines, cultures, or philosophical frameworks.",
                "Try to articulate the strongest version of opposing viewpoints, not just easy-to-defeat versions."
            ],
            "implication": [
                "Trace both intended and unintended consequences that logically follow from your position.",
                "Consider short-term and long-term implications, as well as effects on different stakeholders.",
                "Examine whether you're comfortable with all the logical extensions of your argument."
            ],
            "counter": [
                "Articulate the strongest version of the counterargument, not just easy-to-defeat versions.",
                "Consider addressing both factual challenges and value-based objections to your position.",
                "Explain why your position still holds despite valid criticisms."
            ]
        }
    
    def generate_questions(self, argument: str, count: int = 3) -> Dict[str, Any]:
        """
        Generate Socratic questions based on the argument text with answer hints.
        
        Args:
            argument: The argument text to analyze.
            count: Number of questions to generate.
            
        Returns:
            A dict containing generated questions with answer hints and an analysis of the argument.
        """
        # Use regex to split sentences more reliably (splitting on a period followed by whitespace)
        sentences = [s.strip() for s in re.split(r'\.\s+', argument) if s.strip()]
        
        # Extract claim (first sentence is often the claim)
        claim = sentences[0] if sentences else ""
        
        # Extract evidence (remaining sentences)
        evidence = sentences[1:] if len(sentences) > 1 else []
        
        # Extract key terms and concepts
        key_terms = self._extract_key_terms(argument)
        
        # Identify argument structure
        structure = self._analyze_argument_structure(argument)
        
        # Generate questions from different categories
        all_questions = []
        
        # Clarification questions about key terms (limit to top 2 terms)
        if key_terms:
            for term in key_terms[:2]:
                template = random.choice(self.question_templates["clarification"])
                hint = random.choice(self.hint_templates["clarification"])
                all_questions.append({
                    "question": template.format(term=term),
                    "category": "clarification",
                    "purpose": "To clarify understanding of key terms",
                    "hint": hint,
                    "focus_element": term
                })
        
        # Questions based on the main claim
        if claim:
            # Assumption question
            template = random.choice(self.question_templates["assumption"])
            hint = random.choice(self.hint_templates["assumption"])
            identified_assumption = self._identify_possible_assumption(claim)
            all_questions.append({
                "question": template.format(statement=claim),
                "category": "assumption",
                "purpose": "To examine unstated assumptions",
                "hint": hint + f" For example, you might be assuming that {identified_assumption}.",
                "focus_element": identified_assumption
            })
            
            # Evidence question
            template = random.choice(self.question_templates["evidence"])
            hint = random.choice(self.hint_templates["evidence"])
            missing_evidence = self._identify_missing_evidence(claim, evidence)
            all_questions.append({
                "question": template.format(statement=claim),
                "category": "evidence",
                "purpose": "To examine the factual basis",
                "hint": hint + f" In this case, you might want to provide evidence about {missing_evidence}.",
                "focus_element": missing_evidence
            })
            
            # Implication question
            template = random.choice(self.question_templates["implication"])
            hint = random.choice(self.hint_templates["implication"])
            possible_implication = self._generate_possible_implication(claim)
            all_questions.append({
                "question": template.format(statement=claim),
                "category": "implication",
                "purpose": "To explore logical consequences",
                "hint": hint + f" Consider whether {possible_implication} would be a logical outcome.",
                "focus_element": possible_implication
            })
            
            # Counter question with alternative position
            counter_position = self._generate_counter_position(claim)
            template = random.choice(self.question_templates["counter"])
            hint = random.choice(self.hint_templates["counter"])
            # Even if the chosen template does not contain {counter_position}, extra keys are tolerated.
            all_questions.append({
                "question": template.format(statement=claim, counter_position=counter_position),
                "category": "counter",
                "purpose": "To anticipate and address potential objections",
                "hint": hint,
                "focus_element": counter_position
            })
        
        # Alternative viewpoint question based on the argument topic
        if structure["topic"]:
            template = random.choice(self.question_templates["alternative"])
            hint = random.choice(self.hint_templates["alternative"])
            stakeholder = self._generate_stakeholder(structure["topic"])
            all_questions.append({
                "question": template.format(phenomenon=structure["topic"]),
                "category": "alternative",
                "purpose": "To consider different perspectives",
                "hint": hint + f" You might explore how {stakeholder} would view this issue.",
                "focus_element": structure["topic"]
            })
        
        # If not enough questions were generated, add generic ones
        if len(all_questions) < count:
            generic_questions = [
                {
                    "question": "What do you think is the strongest counterargument to your position?",
                    "category": "counter",
                    "purpose": "To anticipate and address potential objections",
                    "hint": "Identify the most challenging objection, not just one that's easy to refute. Consider objections to both your evidence and your reasoning.",
                    "focus_element": "counterargument"
                },
                {
                    "question": "How would you respond to someone who disagrees with your conclusion?",
                    "category": "counter",
                    "purpose": "To anticipate and address potential objections",
                    "hint": "Address their core concerns rather than peripheral issues. Acknowledge valid points while explaining why your position still holds.",
                    "focus_element": "disagreement"
                },
                {
                    "question": "What evidence would change your mind on this issue?",
                    "category": "evidence",
                    "purpose": "To examine open-mindedness",
                    "hint": "Specify concrete findings or data that would make you reconsider. This demonstrates intellectual honesty and the falsifiability of your position.",
                    "focus_element": "falsifiability"
                }
            ]
            all_questions.extend(generic_questions)
            
        # Shuffle and return the requested number of questions
        random.shuffle(all_questions)
        
        return {
            "questions": all_questions[:count],
            "argument_analysis": {
                "claim": claim,
                "key_terms": key_terms,
                "topic": structure["topic"],
                "structure_quality": structure["quality"]
            }
        }
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract important terms from the text by filtering out common and short words."""
        common_words = {
            'the', 'and', 'that', 'have', 'for', 'not', 'with', 'you', 'this', 'but', 
            'his', 'from', 'they', 'say', 'her', 'she', 'will', 'one', 'all', 'would', 
            'there', 'their', 'what', 'out', 'about', 'who', 'get', 'which'
        }
        
        # Tokenize words with at least 4 letters
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        word_counts = Counter(words)
        
        # Select the most common words not in the common_words set
        key_terms = [word for word, count in word_counts.most_common(7) if word not in common_words]
        return key_terms[:5]  # Limit to top 5 terms
    
    def _analyze_argument_structure(self, text: str) -> Dict[str, Any]:
        """Analyze the structure of the argument by checking for claim, evidence, and conclusion."""
        sentences = [s.strip() for s in re.split(r'\.\s+', text) if s.strip()]
        
        # Basic structure quality checks
        has_claim = len(sentences) > 0
        has_evidence = len(sentences) > 1
        has_conclusion = any(
            re.search(r'\b(therefore|thus|hence|consequently|in conclusion)\b', s.lower())
            for s in sentences
        )
        
        # Determine a quality score based on structure presence
        quality = 0
        if has_claim:
            quality += 0.3
        if has_evidence:
            quality += 0.4
        if has_conclusion:
            quality += 0.3
            
        topic = self._identify_topic(text)
            
        return {
            "quality": quality,
            "has_claim": has_claim,
            "has_evidence": has_evidence,
            "has_conclusion": has_conclusion,
            "topic": topic
        }
    
    def _identify_topic(self, text: str) -> str:
        """Attempt to identify the main topic of the argument from the first sentence."""
        first_sentence = text.split('.')[0] if '.' in text else text
        topic_indicators = [
            r'(?:regarding|concerning|about|on the topic of|on the subject of|with respect to)\s+([^,\.]+)',
            r'(?:The issue of|The question of|The problem of|The topic of)\s+([^,\.]+)',
            r'^([^,\.]{10,}?)\s+(?:is|are|should|must|can|will)'
        ]
        
        for pattern in topic_indicators:
            match = re.search(pattern, first_sentence, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: use the first few words as a topic
        words = first_sentence.split()
        return ' '.join(words[:3]) if len(words) >= 3 else (words[0] if words else "this topic")
    
    def _generate_counter_position(self, statement: str) -> str:
        """Generate a potential counter-position by negating parts of the statement."""
        statement_lower = statement.lower()
        
        # Check for common patterns and insert negation where appropriate
        if " is " in statement_lower:
            return statement.replace(" is ", " is not ", 1)
        elif " are " in statement_lower:
            return statement.replace(" are ", " are not ", 1)
        elif " will " in statement_lower:
            return statement.replace(" will ", " will not ", 1)
        elif " can " in statement_lower:
            return statement.replace(" can ", " cannot ", 1)
        elif " should " in statement_lower:
            return statement.replace(" should ", " should not ", 1)
        
        # Use a dictionary of common opposites if no direct pattern matches
        position_indicators = {
            "beneficial": "harmful",
            "effective": "ineffective",
            "important": "overrated",
            "necessary": "unnecessary",
            "right": "wrong",
            "good": "bad",
            "positive": "negative",
            "advantage": "disadvantage",
            "increase": "decrease",
            "significant": "insignificant"
        }
        
        for word, opposite in position_indicators.items():
            if word in statement_lower:
                return statement.replace(word, opposite)
        
        # Fallback generic counter-position
        return f"the opposite view that {statement} is incorrect"
    
    def _identify_possible_assumption(self, claim: str) -> str:
        """Identify a possible assumption underlying the claim."""
        claim_lower = claim.lower()
        
        if "should" in claim_lower:
            return "this action would have the intended effect without significant downsides"
        elif "best" in claim_lower or "better" in claim_lower:
            return "the criteria you're using for comparison are the most relevant ones"
        elif "will" in claim_lower or "going to" in claim_lower:
            return "current trends will continue without unexpected changes"
        elif any(word in claim_lower for word in ["all", "every", "always"]):
            return "there are no exceptions to your general rule"
        elif any(word in claim_lower for word in ["because", "due to"]):
            return "the relationship between your cause and effect is direct and not influenced by other factors"
        elif any(word in claim_lower for word in ["need", "must"]):
            return "there are no alternative approaches that could achieve the same goal"
        elif "?" in claim:
            return "the question is framed in a neutral way without hidden premises"
        else:
            return "your audience shares your basic values and priorities on this topic"
    
    def _identify_missing_evidence(self, claim: str, evidence_sentences: List[str]) -> str:
        """Identify what kind of evidence might be missing in support of the claim."""
        evidence_text = ' '.join(evidence_sentences).lower()
        
        has_statistics = bool(re.search(r'\b(percent|percentage|\d+%|\d+ percent|statistics|survey|study|studies)\b', evidence_text))
        has_examples = bool(re.search(r'\b(example|instance|case|illustration|scenario)\b', evidence_text))
        has_expert = bool(re.search(r'\b(expert|professor|researcher|scientist|authority|according to|study|research)\b', evidence_text))
        has_historical = bool(re.search(r'\b(history|historical|in the past|previously|precedent)\b', evidence_text))
        
        if not has_statistics:
            return "statistical data or research findings"
        elif not has_examples:
            return "specific examples or cases that illustrate your point"
        elif not has_expert:
            return "expert opinions or authoritative sources"
        elif not has_historical:
            return "historical precedents or relevant background context"
        else:
            return "counterarguments that you've considered and addressed"
    
    def _generate_possible_implication(self, statement: str) -> str:
        """Generate a possible implication of the statement."""
        statement_lower = statement.lower()
        
        if any(word in statement_lower for word in ["should", "must", "need to"]):
            return "this would create a precedent for similar situations"
        if any(word in statement_lower for word in ["right", "wrong", "moral", "ethical"]):
            return "we would need to apply the same moral standard consistently in other contexts"
        if any(word in statement_lower for word in ["is", "are"]):
            return "we would expect to see certain observable consequences in the real world"
        if any(word in statement_lower for word in ["will", "going to"]):
            return "we should prepare for this outcome rather than alternatives"
        
        return "other related claims would also likely be true or false for the same reasons"
    
    def _generate_stakeholder(self, topic: str) -> str:
        """Generate a relevant stakeholder based on the topic."""
        domain_stakeholders = {
            "education": ["teachers", "students", "parents", "school administrators"],
            "healthcare": ["doctors", "patients", "insurance companies", "public health officials"],
            "environment": ["environmental scientists", "future generations", "wildlife conservationists", "industry representatives"],
            "technology": ["tech developers", "consumers", "privacy advocates", "regulators"],
            "economy": ["workers", "business owners", "economists", "consumers"],
            "politics": ["voters", "politicians", "political minorities", "international allies"],
            "social": ["community organizations", "marginalized groups", "social workers", "religious institutions"]
        }
        
        for domain, stakeholders in domain_stakeholders.items():
            if domain in topic.lower():
                return random.choice(stakeholders)
        
        default_stakeholders = [
            "people with opposing political views",
            "those directly affected by this issue",
            "experts in this field",
            "those from different cultural backgrounds",
            "people with different economic circumstances"
        ]
        return random.choice(default_stakeholders)
    
    def get_category_descriptions(self) -> Dict[str, str]:
        """Return descriptions of the question categories."""
        return {
            "clarification": "Questions that clarify concepts and definitions",
            "assumption": "Questions that probe assumptions and premises",
            "evidence": "Questions that examine evidence and reasons",
            "alternative": "Questions that consider alternative viewpoints",
            "implication": "Questions that explore implications and consequences",
            "counter": "Questions that challenge the position with counterarguments"
        }
import uuid

def display_socratic_questions(questions):
    for i, q in enumerate(questions):
        unique_key = f"response_{i}_{uuid.uuid4()}"
        st.write(f"Q{i+1}: {q}")
        st.text_area(f"Your response to Q{i+1}", key=unique_key, height=100)
