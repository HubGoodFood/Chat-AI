import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class PolicyManager:
    """Load and search policy text with lightweight and semantic capabilities."""

    def __init__(self, policy_file='data/policy.json', model_name='paraphrase-multilingual-MiniLM-L12-v2', lazy_load=True):
        self.policy_file = policy_file
        self.policy_data: Dict[str, Any] = {}
        self.policy_sentences: List[str] = []
        self.policy_embeddings = None
        self.model_name = model_name
        self.model: Optional[Any] = None  # SentenceTransformer model (heavy)
        self.lightweight_manager = None  # Lightweight policy manager
        self.lazy_load = lazy_load
        self._model_loaded = False

        # 总是加载政策数据（这很快）
        self.load_policy()

        # 优先初始化轻量级管理器
        self._init_lightweight_manager()

        # 根据lazy_load决定是否立即加载重型模型
        if not lazy_load:
            self._load_model()
            self._generate_embeddings()

    def _init_lightweight_manager(self):
        """初始化轻量级政策管理器"""
        try:
            from .lightweight_manager import LightweightPolicyManager
            self.lightweight_manager = LightweightPolicyManager(
                policy_file=self.policy_file,
                lazy_load=True
            )
            logger.info("轻量级政策管理器初始化成功")
        except Exception as e:
            logger.warning(f"轻量级政策管理器初始化失败: {e}")
            self.lightweight_manager = None

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

    def _ensure_model_loaded(self):
        """确保模型已加载（懒加载）"""
        if not self._model_loaded:
            self._load_model()
            self._generate_embeddings()
            self._model_loaded = True

    def _load_model(self):
        """Loads the sentence transformer model (heavy dependency)."""
        try:
            # 懒加载重型依赖
            from sentence_transformers import SentenceTransformer

            logger.info(f"正在加载SentenceTransformer模型 '{self.model_name}'...")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"SentenceTransformer model '{self.model_name}' loaded successfully.")
        except ImportError:
            logger.warning("sentence-transformers未安装，将仅使用轻量级政策搜索")
            self.model = None
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
        # 确保模型已加载（懒加载）
        if self.lazy_load:
            self._ensure_model_loaded()

        if not self.model or self.policy_embeddings is None:
            logger.warning("Semantic search not available: model or embeddings missing.")
            # Fallback to keyword search if semantic search is not available
            keyword_result = self.find_policy_excerpt([query]) # Use the old method as fallback
            return [keyword_result] if keyword_result else []

        try:
            # 懒加载重型依赖
            from sentence_transformers import util
            import torch

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

        except ImportError:
            logger.warning("重型依赖未安装，回退到关键词搜索")
            keyword_result = self.find_policy_excerpt([query])
            return [keyword_result] if keyword_result else []
        except Exception as e:
            logger.error(f"An error occurred during semantic search: {e}")
            # Fallback to keyword search on error
            keyword_result = self.find_policy_excerpt([query]) # Use the old method as fallback
            return [keyword_result] if keyword_result else []

    def search_policy(self, query: str, top_k: int = 3) -> List[str]:
        """
        搜索政策，优先使用轻量级方法，重型方法作为备选

        Args:
            query (str): 搜索查询
            top_k (int): 返回结果数量

        Returns:
            List[str]: 相关政策句子列表
        """
        # 优先使用轻量级管理器
        if self.lightweight_manager:
            try:
                results = self.lightweight_manager.search_policy(query, top_k)
                if results:
                    logger.debug(f"轻量级政策搜索找到 {len(results)} 条结果")
                    return results
            except Exception as e:
                logger.warning(f"轻量级政策搜索失败: {e}，回退到语义搜索")

        # 回退到重型语义搜索
        try:
            results = self.find_policy_excerpt_semantic(query, top_k)
            if results:
                logger.debug(f"语义政策搜索找到 {len(results)} 条结果")
                return results
        except Exception as e:
            logger.warning(f"语义政策搜索失败: {e}，回退到关键词搜索")

        # 最后回退到关键词搜索
        keyword_result = self.find_policy_excerpt([query])
        return [keyword_result] if keyword_result else ["请联系客服了解具体政策信息。"]

    def get_policy_categories(self) -> List[Dict[str, str]]:
        """
        获取政策类别列表，用于生成政策选择按钮

        Returns:
            List[Dict[str, str]]: 政策类别列表，每个包含display_text和payload
        """
        # 政策类别映射：section_key -> 用户友好的显示名称
        category_mapping = {
            'mission': '理念宗旨',
            'group_rules': '群规制度',
            'product_quality': '质量保证',
            'delivery': '配送政策',
            'payment': '付款方式',
            'pickup': '取货信息',
            'after_sale': '售后服务',
            'community': '社区互助'
        }

        categories = []
        if 'sections' in self.policy_data:
            for section_key, display_name in category_mapping.items():
                if section_key in self.policy_data['sections']:
                    categories.append({
                        'display_text': display_name,
                        'payload': f'policy_category:{section_key}'
                    })

        return categories

    def get_policy_by_category(self, category_key: str) -> str:
        """
        根据类别键获取具体政策内容

        Args:
            category_key (str): 政策类别键（如'delivery', 'payment'等）

        Returns:
            str: 格式化的政策内容
        """
        # 类别名称映射
        category_names = {
            'mission': '理念宗旨',
            'group_rules': '群规制度',
            'product_quality': '质量保证',
            'delivery': '配送政策',
            'payment': '付款方式',
            'pickup': '取货信息',
            'after_sale': '售后服务',
            'community': '社区互助'
        }

        if 'sections' not in self.policy_data or category_key not in self.policy_data['sections']:
            return f"抱歉，没有找到关于{category_names.get(category_key, category_key)}的政策信息。"

        category_name = category_names.get(category_key, category_key)
        policy_items = self.policy_data['sections'][category_key]

        if not policy_items:
            return f"抱歉，{category_name}的政策信息暂时为空。"

        # 格式化政策内容
        response_parts = [f"📋 {category_name}"]
        response_parts.append("")  # 空行

        for i, item in enumerate(policy_items, 1):
            response_parts.append(f"• {item}")

        # 添加版本信息
        version = self.get_policy_version()
        last_updated = self.get_policy_last_updated()
        response_parts.append("")
        response_parts.append(f"(政策版本: {version}, 最后更新: {last_updated})")

        # 添加引导信息
        response_parts.append("")
        response_parts.append("如需了解其他政策信息，您可以询问\"你们有什么政策？\"查看完整政策列表。")

        return "\n".join(response_parts)

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