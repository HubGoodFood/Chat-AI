# 数据库迁移实施指南

## 🎯 目标
将CSV文件数据迁移到SQLite/PostgreSQL数据库，提升查询性能和数据管理能力。

## 📊 当前状态分析

### 现有数据文件:
- `data/products.csv` - 产品数据（59条记录）
- `data/policy.json` - 政策数据（54条句子）
- `data/intent_training_data.csv` - 意图训练数据

### 性能问题:
- 每次启动都要重新加载CSV文件
- 无法进行复杂查询和过滤
- 没有索引支持，查询效率低
- 无法支持并发访问

## 🗄️ 数据库设计

### 1. 产品表 (products)
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2),
    unit VARCHAR(20),
    description TEXT,
    availability BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_availability ON products(availability);
```

### 2. 政策表 (policies)
```sql
CREATE TABLE policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    keywords TEXT, -- JSON格式存储关键词
    priority INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_policies_section ON policies(section);
CREATE INDEX idx_policies_active ON policies(active);
-- 全文搜索索引（SQLite FTS5）
CREATE VIRTUAL TABLE policies_fts USING fts5(content, keywords);
```

### 3. 意图训练数据表 (intent_training)
```sql
CREATE TABLE intent_training (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    intent VARCHAR(50) NOT NULL,
    confidence DECIMAL(3,2),
    source VARCHAR(20) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_intent_training_intent ON intent_training(intent);
CREATE INDEX idx_intent_training_source ON intent_training(source);
```

### 4. 缓存表 (cache_entries)
```sql
CREATE TABLE cache_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_value TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_cache_key ON cache_entries(cache_key);
CREATE INDEX idx_cache_expires ON cache_entries(expires_at);
```

## 🛠️ 实施步骤

### 第一步: 创建数据库连接管理器

创建文件: `src/core/database.py`
```python
#!/usr/bin/env python3
"""
数据库连接管理器
支持SQLite和PostgreSQL
"""

import sqlite3
import os
import logging
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "data/chatai.db"):
        self.db_path = db_path
        self.ensure_database()
    
    def ensure_database(self):
        """确保数据库和表存在"""
        with self.get_connection() as conn:
            self.create_tables(conn)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        try:
            yield conn
        finally:
            conn.close()
    
    def create_tables(self, conn):
        """创建所有表"""
        # 在这里执行上面的CREATE TABLE语句
        pass
```

### 第二步: 创建数据迁移脚本

创建文件: `scripts/migrate_data.py`
```python
#!/usr/bin/env python3
"""
数据迁移脚本
将CSV和JSON数据迁移到数据库
"""

import csv
import json
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.database import DatabaseManager

def migrate_products():
    """迁移产品数据"""
    db = DatabaseManager()
    
    with open('data/products.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        products = list(reader)
    
    with db.get_connection() as conn:
        for product in products:
            conn.execute("""
                INSERT INTO products (name, category, price, unit, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                product['name'],
                product.get('category', ''),
                float(product.get('price', 0)),
                product.get('unit', ''),
                product.get('description', '')
            ))
        conn.commit()
    
    print(f"迁移了 {len(products)} 条产品数据")

def migrate_policies():
    """迁移政策数据"""
    # 实现政策数据迁移
    pass

def migrate_intent_data():
    """迁移意图训练数据"""
    # 实现意图数据迁移
    pass

if __name__ == "__main__":
    migrate_products()
    migrate_policies()
    migrate_intent_data()
    print("数据迁移完成！")
```

### 第三步: 创建数据访问层

创建文件: `src/core/repositories.py`
```python
#!/usr/bin/env python3
"""
数据访问层
提供高级的数据库操作接口
"""

from typing import List, Dict, Optional, Any
from .database import DatabaseManager

class ProductRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """获取所有产品"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM products 
                WHERE availability = TRUE 
                ORDER BY category, name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """搜索产品"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM products 
                WHERE availability = TRUE 
                AND (name LIKE ? OR description LIKE ?)
                ORDER BY 
                    CASE WHEN name LIKE ? THEN 1 ELSE 2 END,
                    name
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按类别获取产品"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM products 
                WHERE category = ? AND availability = TRUE
                ORDER BY name
            """, (category,))
            return [dict(row) for row in cursor.fetchall()]

class PolicyRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def search_policies(self, query: str) -> List[Dict[str, Any]]:
        """搜索政策"""
        with self.db.get_connection() as conn:
            # 使用全文搜索
            cursor = conn.execute("""
                SELECT p.* FROM policies p
                JOIN policies_fts fts ON p.id = fts.rowid
                WHERE policies_fts MATCH ?
                AND p.active = TRUE
                ORDER BY rank
            """, (query,))
            return [dict(row) for row in cursor.fetchall()]
```

### 第四步: 更新现有管理器

修改 `src/app/products/manager.py`:
```python
# 添加数据库支持
from src.core.repositories import ProductRepository
from src.core.database import DatabaseManager

class ProductManager:
    def __init__(self, cache_manager=None, use_database=True):
        self.cache_manager = cache_manager
        self.use_database = use_database
        
        if use_database:
            self.db_manager = DatabaseManager()
            self.product_repo = ProductRepository(self.db_manager)
        else:
            # 保持原有CSV逻辑作为备选
            self.load_products_from_csv()
    
    def get_all_products(self):
        if self.use_database:
            return self.product_repo.get_all_products()
        else:
            return self.products  # 原有逻辑
```

## 🧪 测试计划

### 1. 单元测试
创建文件: `tests/test_database.py`
```python
import unittest
from src.core.database import DatabaseManager
from src.core.repositories import ProductRepository

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")  # 内存数据库
        self.product_repo = ProductRepository(self.db)
    
    def test_product_crud(self):
        # 测试产品的增删改查
        pass
    
    def test_product_search(self):
        # 测试产品搜索功能
        pass
```

### 2. 性能测试
创建文件: `tests/test_performance.py`
```python
import time
import unittest
from src.core.repositories import ProductRepository

class TestPerformance(unittest.TestCase):
    def test_query_performance(self):
        # 对比CSV和数据库查询性能
        pass
```

### 3. 迁移测试
创建文件: `tests/test_migration.py`
```python
import unittest
from scripts.migrate_data import migrate_products

class TestMigration(unittest.TestCase):
    def test_data_integrity(self):
        # 验证迁移后数据完整性
        pass
```

## 📈 性能优化

### 1. 索引优化
```sql
-- 复合索引
CREATE INDEX idx_products_category_availability ON products(category, availability);

-- 部分索引
CREATE INDEX idx_active_policies ON policies(section) WHERE active = TRUE;
```

### 2. 查询优化
```python
# 使用预编译语句
class ProductRepository:
    def __init__(self, db_manager):
        self.db = db_manager
        self._prepare_statements()
    
    def _prepare_statements(self):
        # 预编译常用查询
        pass
```

### 3. 连接池
```python
# 对于PostgreSQL，使用连接池
import psycopg2.pool

class PostgreSQLManager:
    def __init__(self):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host="localhost",
            database="chatai",
            user="username",
            password="password"
        )
```

## 🚀 部署步骤

### 1. 开发环境
```bash
# 1. 运行迁移脚本
python scripts/migrate_data.py

# 2. 运行测试
python -m pytest tests/test_database.py

# 3. 更新环境变量
export USE_DATABASE=true
export DATABASE_URL=sqlite:///data/chatai.db
```

### 2. 生产环境
```bash
# 1. 使用PostgreSQL
export DATABASE_URL=postgresql://user:pass@host:5432/chatai

# 2. 运行迁移
python scripts/migrate_data.py --production

# 3. 验证数据
python scripts/verify_migration.py
```

## 📊 预期收益

### 性能提升:
- 产品查询: 5-10x 更快
- 复杂搜索: 支持全文搜索和模糊匹配
- 并发支持: 支持多用户同时访问

### 功能增强:
- 数据一致性保证
- 事务支持
- 备份和恢复
- 数据分析能力

### 运维改善:
- 标准化数据管理
- 更好的监控和日志
- 数据迁移和版本管理

完成数据库迁移后，您的Chat AI将具备企业级的数据管理能力！
