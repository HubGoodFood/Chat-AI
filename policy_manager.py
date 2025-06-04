import os
import logging

logger = logging.getLogger(__name__)

class PolicyManager:
    """Load and search policy text for quick lookup."""

    def __init__(self, policy_file='policy.md'):
        self.policy_file = policy_file
        self.lines = []
        self.load_policy()

    def load_policy(self):
        if not os.path.isabs(self.policy_file):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.policy_file = os.path.join(base_dir, self.policy_file)
        try:
            with open(self.policy_file, 'r', encoding='utf-8') as f:
                self.lines = [line.strip() for line in f if line.strip()]
            logger.info(f"Policy loaded from {self.policy_file}, {len(self.lines)} lines")
        except FileNotFoundError:
            logger.warning(f"Policy file {self.policy_file} not found")
            self.lines = []

    def find_policy_excerpt(self, keywords):
        """Return the first matching line using keywords priority."""
        for kw in keywords:
            for line in self.lines:
                if kw in line:
                    return line
        return ''
