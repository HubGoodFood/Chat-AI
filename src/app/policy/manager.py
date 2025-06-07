import os
import json
import logging
from typing import Dict, List, Any, Optional
from sentence_transformers import SentenceTransformer, util
import torch

logger = logging.getLogger(__name__)

class PolicyManager:
    """Load and search policy text with semantic capabilities."""

    def __init__(self, policy_file='data/policy.json', model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        self.policy_file = policy_file
        self.policy_data: Dict[str, Any] = {}
        self.policy_sentences: List[str] = []
        self.policy_embeddings = None
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.load_policy()
        self._load_model()
        self._generate_embeddings()

    def load_policy(self):
        """Loads policy data from the JSON file."""
        # Removed path modification logic, self.policy_file is expected to be correct
            
        logger.info(f"Attempting to load policy from: {self.policy_file}")

        try:
            with open(self.policy_file, 'r', encoding='utf-8') as f:
                self.policy_data = json.load(f)
            logger.info(f"Policy loaded successfully from {self.policy_file}")
            
            # Extract sentences for embedding
            self.policy_sentences = []
            if 'sections' in self.policy_data:
                for section_key, sentences in self.policy_data['sections'].items():
                    if isinstance(sentences, list):
                        self.policy_sentences.extend(sentences)
            logger.info(f"Extracted {len(self.policy_sentences)} sentences for embedding.")

        except FileNotFoundError:
            logger.error(f"Policy file {self.policy_file} not found.")
            self.policy_data = {}
            self.policy_sentences = []
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from policy file {self.policy_file}.")
            self.policy_data = {}
            self.policy_sentences = []
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading policy: {e}")
            self.policy_data = {}
            self.policy_sentences = []

    def _load_model(self):
        """Loads the sentence transformer model."""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"SentenceTransformer model '{self.model_name}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model '{self.model_name}': {e}")
            self.model = None

    def _generate_embeddings(self):
        """Generates embeddings for all policy sentences."""
        if self.model and self.policy_sentences:
            try:
                self.policy_embeddings = self.model.encode(self.policy_sentences, convert_to_tensor=True)
                logger.info(f"Generated embeddings for {len(self.policy_sentences)} policy sentences.")
            except Exception as e:
                logger.error(f"Failed to generate policy embeddings: {e}")
                self.policy_embeddings = None
        else:
            logger.warning("Skipping embedding generation: model not loaded or no sentences found.")
            self.policy_embeddings = None

    def find_policy_excerpt_semantic(self, query: str, top_k: int = 3) -> List[str]:
        """
        Finds policy excerpts semantically similar to the query.

        Args:
            query (str): The user's query.
            top_k (int): The number of top similar sentences to return.

        Returns:
            List[str]: A list of the most relevant policy sentences.
        """
        if not self.model or self.policy_embeddings is None:
            logger.warning("Semantic search not available: model or embeddings missing.")
            # Fallback to keyword search if semantic search is not available
            keyword_result = self.find_policy_excerpt([query]) # Use the old method as fallback
            return [keyword_result] if keyword_result else []

        try:
            query_embedding = self.model.encode(query, convert_to_tensor=True)
            # Compute cosine-similarity between the query and all policy sentences
            cosine_scores = util.cos_sim(query_embedding, self.policy_embeddings)[0]

            # Find the top_k scores
            top_results = torch.topk(cosine_scores, k=min(top_k, len(self.policy_sentences)))

            relevant_sentences = []
            for score, idx in zip(top_results[0], top_results[1]):
                # Optional: Add a similarity threshold if needed
                # if score.item() > 0.5:
                relevant_sentences.append(self.policy_sentences[idx.item()])
                logger.debug(f"Semantic match: Score {score.item():.4f}, Sentence: {self.policy_sentences[idx.item()]}")

            return relevant_sentences

        except Exception as e:
            logger.error(f"An error occurred during semantic search: {e}")
            # Fallback to keyword search on error
            keyword_result = self.find_policy_excerpt([query]) # Use the old method as fallback
            return [keyword_result] if keyword_result else []

    def find_policy_excerpt(self, keywords: List[str]) -> str:
        """
        (Legacy) Return the first matching line using keywords priority from original lines.
        This method is kept for compatibility or fallback.
        """
        # Note: This method now operates on the extracted sentences from JSON,
        # not the original policy.md lines, unless load_policy failed.
        # If load_policy failed, self.policy_sentences will be empty,
        # and this method will return ''.
        
        # If policy_data was loaded, use the extracted sentences
        if self.policy_sentences:
             for kw in keywords:
                for sentence in self.policy_sentences:
                    if kw.lower() in sentence.lower():
                        return sentence
        # If policy_data failed to load, self.policy_sentences is empty,
        # so the loops above won't run. Return empty string.
        return ''

    def get_policy_version(self) -> str:
        """Returns the policy version."""
        return self.policy_data.get('version', 'N/A')

    def get_policy_last_updated(self) -> str:
        """Returns the last updated date of the policy."""
        return self.policy_data.get('last_updated', 'N/A')

    def get_policy_section(self, section_key: str) -> List[str]:
        """Returns sentences from a specific policy section."""
        return self.policy_data.get('sections', {}).get(section_key, [])

    def get_all_sections(self) -> List[str]:
        """Returns a list of all available policy section keys."""
        return list(self.policy_data.get('sections', {}).keys())

# Example Usage (for testing)
if __name__ == '__main__':
    # Assuming policy.json is in the same directory (or data/policy.json if run from root)
    # For this example to run standalone from src/app/policy, it would need policy_file='../../../data/policy.json'
    # Or, more robustly, configure the path based on expected execution context.
    # For now, let's assume it's run where 'data/policy.json' is accessible.
    policy_manager = PolicyManager(policy_file='data/policy.json') # Explicitly set for clarity if run from root

    print(f"Policy Version: {policy_manager.get_policy_version()}")
    print(f"Last Updated: {policy_manager.get_policy_last_updated()}")

    query = "运费怎么算？"
    print(f"\nSemantic search for '{query}':")
    results = policy_manager.find_policy_excerpt_semantic(query)
    for res in results:
        print(f"- {res}")

    query = "质量问题怎么办？"
    print(f"\nSemantic search for '{query}':")
    results = policy_manager.find_policy_excerpt_semantic(query)
    for res in results:
        print(f"- {res}")

    query = "你们卖什么？" # This query might not match well with policy sentences
    print(f"\nSemantic search for '{query}':")
    results = policy_manager.find_policy_excerpt_semantic(query)
    for res in results:
        print(f"- {res}")

    query = "退款" # Test keyword fallback
    print(f"\nKeyword search for '{query}':")
    result = policy_manager.find_policy_excerpt([query])
    print(f"- {result}")