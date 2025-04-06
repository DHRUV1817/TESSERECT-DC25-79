"""
RAG (Retrieval-Augmented Generation) Pipeline for the Tesseract Project
Enhances responses with knowledge retrieval from external sources.
"""
import os
from typing import List, Dict, Any, Optional
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Path to knowledge base
KNOWLEDGE_DIR = "data/knowledge"

class RAGPipeline:
    """Implements a simple Retrieval-Augmented Generation pipeline."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG pipeline.
        
        Args:
            model_name: Name of the SentenceTransformer model to use
        """
        # Create knowledge directory if it doesn't exist
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        
        # Load the embedding model
        self.model = SentenceTransformer(model_name)
        
        # Load or initialize the knowledge base
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load the knowledge base from files."""
        knowledge_items = []
        
        # Load from JSON files in the knowledge directory
        for filename in os.listdir(KNOWLEDGE_DIR):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(KNOWLEDGE_DIR, filename), 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            knowledge_items.extend(data)
                        else:
                            knowledge_items.append(data)
                except Exception as e:
                    print(f"Error loading knowledge file {filename}: {str(e)}")
        
        # If no knowledge files exist, create a sample knowledge base
        if not knowledge_items:
            sample_knowledge = self._create_sample_knowledge()
            self._save_knowledge_item(sample_knowledge, "sample_knowledge.json")
            knowledge_items = sample_knowledge
            
        # Calculate embeddings for all items if not already present
        for item in knowledge_items:
            if "embedding" not in item:
                text_to_embed = item["title"] + ". " + item["content"]
                item["embedding"] = self.model.encode(text_to_embed).tolist()
                
        return knowledge_items
    
    def _create_sample_knowledge(self) -> List[Dict[str, Any]]:
        """Create a sample knowledge base for initial setup."""
        return [
            {
                "title": "Climate Change Evidence",
                "topic": "climate change",
                "content": "Multiple lines of evidence confirm that Earth's climate is changing. Global temperatures have risen by about 1.1°C since the late 19th century. The rate of warming has doubled since 1981. The past decade was the warmest on record. This warming is primarily driven by human emissions of greenhouse gases, particularly carbon dioxide from burning fossil fuels.",
                "source": "Scientific consensus"
            },
            {
                "title": "Renewable Energy Benefits",
                "topic": "renewable energy",
                "content": "Renewable energy sources like solar and wind power produce electricity without generating greenhouse gas emissions during operation. They have minimal environmental impact compared to fossil fuels and help combat climate change. Additionally, the cost of renewable technologies has decreased significantly, making them economically competitive with conventional energy sources in many markets.",
                "source": "Energy research"
            },
            {
                "title": "Social Media Regulation",
                "topic": "social media",
                "content": "Social media platforms face increasing calls for regulation due to concerns about privacy, misinformation, and content moderation. Potential regulatory approaches include mandating transparency in algorithms, implementing stronger data protection laws, establishing oversight boards, and clarifying platform liability for user content. Critics argue excessive regulation could stifle innovation and free speech.",
                "source": "Policy research"
            },
            {
                "title": "Free College Education",
                "topic": "education",
                "content": "Proponents of free college education argue it would increase access, reduce student debt, and create a more educated workforce. Opponents contend it would be prohibitively expensive, potentially reduce educational quality, and disproportionately benefit middle and upper-class families who would attend college anyway rather than addressing deeper inequalities in the education system.",
                "source": "Education policy analysis"
            }
        ]
    
    def _save_knowledge_item(self, items: List[Dict[str, Any]], filename: str) -> None:
        """Save knowledge items to a file."""
        try:
            with open(os.path.join(KNOWLEDGE_DIR, filename), 'w') as f:
                json.dump(items, f, indent=2)
        except Exception as e:
            print(f"Error saving knowledge file {filename}: {str(e)}")
    
    def add_knowledge(self, title: str, content: str, topic: str = "", source: str = "") -> bool:
        """
        Add a new item to the knowledge base.
        
        Args:
            title: Title of the knowledge item
            content: Main content text
            topic: Topic category
            source: Source of the information
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            # Create the knowledge item
            text_to_embed = title + ". " + content
            embedding = self.model.encode(text_to_embed).tolist()
            
            knowledge_item = {
                "title": title,
                "topic": topic,
                "content": content,
                "source": source,
                "embedding": embedding
            }
            
            # Add to knowledge base
            self.knowledge_base.append(knowledge_item)
            
            # Save to a file
            filename = f"{topic.replace(' ', '_')}_{len(self.knowledge_base)}.json"
            self._save_knowledge_item([knowledge_item], filename)
            
            return True
        except Exception as e:
            print(f"Error adding knowledge: {str(e)}")
            return False
    
    def retrieve(self, query: str, topic: str = "", top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge items for a query.
        
        Args:
            query: The query text
            topic: Optional topic filter
            top_k: Number of items to retrieve
            
        Returns:
            List of relevant knowledge items
        """
        if not self.knowledge_base:
            return []
            
        # Filter by topic if provided
        candidates = self.knowledge_base
        if topic:
            topic_lower = topic.lower()
            candidates = [item for item in candidates if topic_lower in item.get("topic", "").lower()]
            
        if not candidates:
            return []
            
        # Encode the query
        query_embedding = self.model.encode(query)
        
        # Calculate similarity with all candidates
        similarities = []
        for item in candidates:
            embedding = np.array(item["embedding"])
            similarity = cosine_similarity([query_embedding], [embedding])[0][0]
            similarities.append((item, similarity))
            
        # Sort by similarity and return top_k
        sorted_items = sorted(similarities, key=lambda x: x[1], reverse=True)
        
        # Return items without the embedding to keep response clean
        results = []
        for item, score in sorted_items[:top_k]:
            item_copy = {k: v for k, v in item.items() if k != "embedding"}
            item_copy["relevance_score"] = float(score)
            results.append(item_copy)
            
        return results
    
    def enhance_response(self, text: str, topic: str = "") -> Dict[str, Any]:
        """
        Enhance a response with relevant knowledge.
        
        Args:
            text: Original text to enhance
            topic: Optional topic for filtering
            
        Returns:
            Dict with enhanced text and retrieved knowledge
        """
        # Retrieve relevant knowledge
        retrieved_items = self.retrieve(text, topic)
        
        if not retrieved_items:
            return {
                "original_text": text,
                "enhanced_text": text,
                "knowledge_items": []
            }
        
        # Create enhanced text by appending relevant facts
        enhanced_text = text
        
        # Add a section with supporting facts
        facts = []
        for item in retrieved_items:
            if item["relevance_score"] > 0.6:  # Only use highly relevant items
                facts.append(f"- {item['content']}")
        
        if facts:
            enhanced_text += "\n\nSupporting information:\n" + "\n".join(facts)
        
        return {
            "original_text": text,
            "enhanced_text": enhanced_text,
            "knowledge_items": retrieved_items
        }
    
    def enhance_counterpoints(self, counterpoints: List[Dict[str, Any]], topic: str = "") -> List[Dict[str, Any]]:
        """
        Enhance counterpoints with relevant knowledge.
        
        Args:
            counterpoints: List of counterpoint dictionaries
            topic: Optional topic for filtering
            
        Returns:
            Enhanced counterpoints
        """
        enhanced_counterpoints = []
        
        for counterpoint in counterpoints:
            text = counterpoint["text"]
            
            # Retrieve relevant knowledge
            retrieved_items = self.retrieve(text, topic, top_k=1)
            
            # Copy the counterpoint
            enhanced = counterpoint.copy()
            
            # Add supporting info if we found relevant knowledge
            if retrieved_items and retrieved_items[0]["relevance_score"] > 0.6:
                item = retrieved_items[0]
                enhanced["text"] = f"{text} This is supported by evidence: {item['content']}"
                enhanced["source"] = item["source"]
                enhanced["knowledge_enhanced"] = True
            else:
                enhanced["knowledge_enhanced"] = False
                
            enhanced_counterpoints.append(enhanced)
            
        return enhanced_counterpoints

# Singleton instance
rag_pipeline = None

def get_rag_pipeline() -> RAGPipeline:
    """Get or create the RAG pipeline instance."""
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = RAGPipeline()
    return rag_pipeline