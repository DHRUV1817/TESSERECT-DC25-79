"""
RAG (Retrieval-Augmented Generation) Processor for the Tesseract Project
Implements knowledge retrieval to enhance argument analysis.
"""
import os
import json
import httpx
from typing import List, Dict, Any, Optional
import hashlib
import time

class RAGProcessor:
    """Implements retrieval-augmented generation for enhanced argument analysis."""
    
    def __init__(self, use_vector_db: bool = False):
        """
        Initialize the RAG processor.
        
        Args:
            use_vector_db: Whether to use a vector database for retrieval (requires additional setup)
        """
        self.use_vector_db = use_vector_db
        
        # API configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = "gpt-3.5-turbo"
        
        # Knowledge base storage path
        self.knowledge_dir = os.path.join("data", "knowledge_base")
        os.makedirs(self.knowledge_dir, exist_ok=True)
        
        # Cache for retrieval results
        self.retrieval_cache = {}
        
        # Load knowledge index if available
        self.knowledge_index = self._load_knowledge_index()
    
    def retrieve_and_generate(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve relevant information and generate enhanced response.
        
        Args:
            query: The query or argument to process
            context: Optional additional context
            
        Returns:
            Dict containing the enhanced results
        """
        # Check cache first
        cache_key = self._get_cache_key(query, context)
        if cache_key in self.retrieval_cache:
            return self.retrieval_cache[cache_key]
        
        # Retrieve relevant knowledge
        retrieved_info = self._retrieve_relevant_information(query, context)
        
        # Generate enhanced response
        if self.openai_api_key:
            try:
                enhanced_result = self._generate_with_context(query, retrieved_info)
            except Exception as e:
                print(f"Error in RAG generation: {str(e)}. Using just retrieved information.")
                enhanced_result = {
                    "query": query,
                    "retrieved_information": retrieved_info,
                    "response": "Could not generate enhanced response.",
                    "sources": [info.get("source", "unknown") for info in retrieved_info]
                }
        else:
            enhanced_result = {
                "query": query,
                "retrieved_information": retrieved_info,
                "response": "OpenAI API key not configured. Using just retrieved information.",
                "sources": [info.get("source", "unknown") for info in retrieved_info]
            }
        
        # Cache the result
        self.retrieval_cache[cache_key] = enhanced_result
        return enhanced_result
    
    def _retrieve_relevant_information(self, query: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant information from the knowledge base.
        
        Args:
            query: The query to search for
            context: Optional additional context
            
        Returns:
            List of relevant information chunks
        """
        if self.use_vector_db:
            return self._retrieve_from_vector_db(query, context)
        else:
            return self._retrieve_from_simple_index(query, context)
    
    def _retrieve_from_simple_index(self, query: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve information using simple keyword matching.
        
        Args:
            query: The query to search for
            context: Optional additional context
            
        Returns:
            List of relevant information chunks
        """
        results = []
        
        # Simplify query for matching
        query_terms = set([term.lower() for term in query.split() if len(term) > 3])
        
        # Add context terms if available
        if context:
            context_terms = set([term.lower() for term in context.split() if len(term) > 3])
            query_terms.update(context_terms)
        
        # Filter to only substantive terms
        stop_words = {"with", "that", "from", "this", "have", "they", "their", "what", "when", "where", "which", "than"}
        query_terms = [term for term in query_terms if term not in stop_words]
        
        # Score each knowledge item
        for item_id, item_data in self.knowledge_index.items():
            score = 0
            item_text = item_data.get("text", "").lower()
            
            # Simple term matching
            for term in query_terms:
                if term in item_text:
                    score += 1
            
            if score > 0:
                results.append({
                    "id": item_id,
                    "text": item_data.get("text", ""),
                    "source": item_data.get("source", "unknown"),
                    "relevance_score": score / max(1, len(query_terms)),
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Return top results (max 3)
        return results[:3]
    
    def _retrieve_from_vector_db(self, query: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve information using vector embeddings (placeholder).
        
        Args:
            query: The query to search for
            context: Optional additional context
            
        Returns:
            List of relevant information chunks
        """
        # This is a placeholder for vector DB implementation
        # In a real implementation, you would:
        # 1. Convert query to embedding using an embedding model
        # 2. Search for nearest neighbors in vector DB
        # 3. Return results
        
        print("Vector DB retrieval not fully implemented. Using simple index instead.")
        return self._retrieve_from_simple_index(query, context)
    
    def _generate_with_context(self, query: str, retrieved_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate an enhanced response using OpenAI API with retrieved context.
        
        Args:
            query: The original query
            retrieved_info: Retrieved relevant information
            
        Returns:
            Dict containing the enhanced response
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is not set")
            
        # Prepare the API request
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        
        # Construct the context from retrieved information
        context_text = "\n\n".join([f"Information from {info['source']}:\n{info['text']}" for info in retrieved_info])
        
        # Construct the prompt
        system_prompt = """
        You are an AI assistant that provides well-informed responses based on retrieved information. 
        When analyzing arguments or responding to queries, use the provided context information to enhance your response.
        Always cite your sources when using specific information from the context.
        """
        
        user_prompt = f"""
        Query: {query}
        
        Retrieved Context Information:
        {context_text}
        
        Based on this information, provide a detailed and well-informed response. Cite sources when appropriate.
        """
        
        payload = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3  # Lower temperature for more factual responses
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # Extract the response content
                content = result["choices"][0]["message"]["content"]
                
                return {
                    "query": query,
                    "retrieved_information": retrieved_info,
                    "response": content,
                    "sources": [info.get("source", "unknown") for info in retrieved_info]
                }
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _load_knowledge_index(self) -> Dict[str, Any]:
        """
        Load the knowledge index from disk.
        
        Returns:
            Dict containing the knowledge index
        """
        index_path = os.path.join(self.knowledge_dir, "knowledge_index.json")
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading knowledge index: {str(e)}. Creating new index.")
        
        # If we can't load the index, create a default one with some sample entries
        default_index = self._create_default_index()
        self._save_knowledge_index(default_index)
        return default_index
    
    def _save_knowledge_index(self, index: Dict[str, Any]) -> None:
        """
        Save the knowledge index to disk.
        
        Args:
            index: The knowledge index to save
        """
        index_path = os.path.join(self.knowledge_dir, "knowledge_index.json")
        try:
            with open(index_path, 'w') as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            print(f"Error saving knowledge index: {str(e)}")
    
    def _create_default_index(self) -> Dict[str, Any]:
        """
        Create a default knowledge index with sample entries.
        
        Returns:
            Dict containing the default knowledge index
        """
        return {
            "logical_fallacies": {
                "text": "Logical fallacies are errors in reasoning that undermine the logic of an argument. Common fallacies include ad hominem (attacking the person), straw man (misrepresenting an opponent's argument), false dichotomy (presenting only two options when others exist), and appeal to authority (using an authority figure to support an argument without evidence).",
                "source": "Logical Reasoning Guide",
                "created_at": time.time()
            },
            "argument_structure": {
                "text": "A strong argument typically consists of a clear claim or thesis statement, supporting evidence (facts, statistics, examples), and a conclusion that follows logically from the evidence. The claim should be specific and debatable, the evidence should be relevant and credible, and the conclusion should summarize the argument and restate the main points.",
                "source": "Debate Handbook",
                "created_at": time.time()
            },
            "speech_fillers": {
                "text": "Filler words like 'um', 'uh', 'like', and 'you know' can detract from the clarity and impact of speech. Speakers who use excessive fillers may be perceived as less confident or knowledgeable. Techniques to reduce fillers include pausing instead of using fillers, recording and analyzing your speech, and practicing speaking more slowly and deliberately.",
                "source": "Public Speaking Guide",
                "created_at": time.time()
            }
        }
    
    def add_to_knowledge_base(self, text: str, source: str, item_id: Optional[str] = None) -> str:
        """
        Add new information to the knowledge base.
        
        Args:
            text: The text content to add
            source: The source of the information
            item_id: Optional item ID, will be generated if not provided
            
        Returns:
            The ID of the added item
        """
        # Generate ID if not provided
        if not item_id:
            item_id = hashlib.md5(f"{text}_{source}_{time.time()}".encode()).hexdigest()[:12]
        
        # Add to index
        self.knowledge_index[item_id] = {
            "text": text,
            "source": source,
            "created_at": time.time()
        }
        
        # Save updated index
        self._save_knowledge_index(self.knowledge_index)
        
        return item_id
    
    def _get_cache_key(self, query: str, context: Optional[str] = None) -> str:
        """Generate a cache key for the query and context."""
        context_str = context or ""
        return hashlib.md5(f"{query}_{context_str}".encode()).hexdigest()