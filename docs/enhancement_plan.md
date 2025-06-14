# 智能果蔬AI增强计划

**核心目标：** 保持现有产品信息查询和政策解答的核心功能，显著提升产品推荐的精准度和用户体验。

**计划概览图 (Mermaid Diagram):**

```mermaid
graph TD
    A[增强计划] --> B{数据层面优化};
    A --> C{算法层面优化};
    A --> D{政策解答增强 (次要)};
    A --> E{评估与迭代};

    B --> B1[优化 products.csv 数据质量];
    B1 --> B1a[丰富产品关键词 Keywords];
    B1 --> B1b[增加产品多维度标签 (如口感, 产地)];

    C --> C1[优化 ProductManager];
    C1 --> C1a[审视模糊匹配 FUZZY_MATCH_THRESHOLD];
    C1a -- 影响 --> C1b[改进 fuzzy_match_product 逻辑];
    C1b --> C1b1[考虑引入拼音/编辑距离];
    C1b --> C1b2[优化关键词提取与权重];

    C --> C2[优化 ChatHandler 推荐逻辑];
    C2 --> C2a[深化用户偏好学习 (user_sessions)];
    C2 --> C2b[引入推荐多样性与新颖性策略];
    C2 --> C2c[探索情境感知推荐 (时间/历史)];
    C2 --> C2d[提供推荐解释];
    C2 --> C2e[优化 LLM Fallback 的上下文与参数];

    D --> D1[审视 policy.json 结构];
    D --> D2[评估语义搜索模型效果];

    E --> E1[定义推荐精准度评估指标];
    E --> E2[建立测试用例];
    E --> E3[考虑 A/B 测试框架];
```

**详细步骤：**

**Phase 1: 数据基础强化 (提升推荐的源头质量)**

1.  **优化产品数据 (`products.csv`)**
    *   **目标：** 确保产品信息的准确性、完整性和丰富性，为精准推荐打下坚实基础。
    *   **行动：**
        *   **全面审查 `Keywords` 字段**：
            *   检查现有产品的 `Keywords` 是否全面、准确。
            *   补充同义词、常见错别字、用户可能使用的口语化表达。
            *   例如：“车厘子”的关键词可以补充“大樱桃”。
        *   **(可选，但推荐) 增加产品多维度标签/属性**：
            *   在 `products.csv` 中添加新的列，如 `Taste` (口感: 如甜、酸、脆、糯), `Origin` (产地), `Benefits` (主要功效/特点: 如富含维C、有机), `SuitableFor` (适合人群: 如儿童、健身人士)。
            *   这将使得推荐系统可以根据更细致的用户需求进行匹配。
            *   *需要同步修改 `product_manager.py` 中的 `load_product_data` 函数以加载新列。*

**Phase 2: 核心算法升级 (提升推荐的智能性)**

2.  **优化产品匹配算法 (`product_manager.py`)**
    *   **目标：** 提高根据用户输入查找产品的准确率和召回率。
    *   **行动：**
        *   **审视与调整模糊匹配阈值**：
            *   分析当前 `config.py` 中的 `FUZZY_MATCH_THRESHOLD = 0.6` 是否最优。可以通过测试不同阈值下的匹配效果来确定。
        *   **改进 `fuzzy_match_product` 函数**：
            *   **考虑引入拼音匹配**：对于中文输入，用户可能使用拼音或拼音首字母，增加对拼音的识别能力。
            *   **考虑引入编辑距离算法** (如 Levenshtein distance)：更好地处理用户输入中的少量错别字。
            *   **优化关键词权重**：不仅仅是匹配到关键词，还要考虑关键词在产品名称或描述中的重要性。
            *   **上下文感知匹配**：如果聊天上下文中已提及某个品类，在模糊匹配时可以适当提高该品类下产品的匹配优先级。

3.  **优化推荐生成逻辑 (`chat_handler.py`)**
    *   **目标：** 使推荐更个性化、多样化、且更具说服力。
    *   **行动：**
        *   **深化用户偏好学习 (基于 `user_sessions`)**：
            *   在 `handle_recommendation` 中，更积极地利用 `session['preferences']['categories']` 和 `session['preferences']['products']`。
            *   如果用户多次查询或购买某一类产品，后续推荐中应优先考虑该品类或相关品类。
            *   可以考虑为偏好设置权重或衰减机制（近期偏好更重要）。
        *   **引入推荐多样性与新颖性策略**：
            *   避免重复推荐少数几个热门产品。
            *   在推荐结果中适当引入一些用户可能未曾接触但评分较高或与用户偏好相似的新品。
            *   可以结合一定的随机性，或者基于物品的协同过滤思路（“喜欢A的用户也喜欢B”）。
        *   **探索情境感知推荐**：
            *   **时间因素**：例如，在特定节日推荐相关礼品类果蔬，在不同季节主推当季水果。
            *   **用户近期行为**：如果用户刚询问了“苹果”，可以追问是否需要“苹果削皮器”或推荐“苹果派的配料”。（这需要扩展产品范围或与其他系统集成）
        *   **提供推荐解释**：
            *   当给出推荐时，简要说明推荐理由。例如：“为您推荐这款XX牌的苹果，因为它是当季新品，而且很多用户评价说口感很脆甜。” 或者 “根据您常购买的水果类型，为您推荐这款XX。”
            *   这可以增加用户对推荐的信任感。
        *   **优化 LLM Fallback 的推荐能力**：
            *   在 `handle_llm_fallback` 函数中，当需要LLM进行推荐时，向LLM提供更结构化、更丰富的上下文信息。例如，明确告知LLM用户的历史偏好、当前对话的上下文、以及希望LLM推荐的侧重点（如“请推荐几款适合榨汁的水果”）。
            *   试验 `config.py` 中的 `LLM_TEMPERATURE` 参数，找到一个平衡点，使得LLM的推荐既有一定新意又不失准确性。

**Phase 3: 政策解答与辅助功能 (保持与微调)**

4.  **政策解答模块审视 (`policy_manager.py`, `policy.json`)**
    *   **目标：** 确保政策解答的准确性和易用性。
    *   **行动：**
        *   **审视 `policy.json` 的内容和结构**：确保所有政策条款都是最新的，并且分类清晰。
        *   **评估语义搜索模型效果**：通过一些典型的政策咨询问题测试 `find_policy_excerpt_semantic` 的效果。如果发现匹配不准，可以考虑：
            *   调整 `policy.json` 中句子的表述，使其更易于被模型理解。
            *   尝试 `sentence-transformers` 库中其他预训练模型（可能需要评估模型大小和性能的平衡）。

**Phase 4: 评估与迭代 (持续改进)**

5.  **建立评估体系并持续迭代**
    *   **目标：** 量化推荐效果，指导后续优化方向。
    *   **行动：**
        *   **定义推荐精准度评估指标**：
            *   例如：点击率 (CTR)、转化率 (CVR)（如果系统涉及购买）、推荐列表的覆盖率、新颖度等。
            *   对于查询匹配，可以使用准确率 (Precision) 和召回率 (Recall)。
        *   **建立测试用例集**：
            *   准备一批典型的用户查询（包括产品查询、推荐请求、政策咨询），以及期望的理想输出。
            *   用于回归测试，确保改动不会破坏原有功能，并能衡量改进效果。
        *   **(可选) 考虑 A/B 测试框架**：
            *   如果条件允许，可以部署不同的推荐策略版本，通过真实用户数据对比效果。