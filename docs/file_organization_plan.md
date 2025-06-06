# 文件整理计划

## 目标
根据项目功能模块对现有文件进行结构化整理，以提高代码的可读性、可维护性和可扩展性。

## 拟议的文件整理计划步骤：

1.  **创建新的目录结构**：
    创建一系列新的目录来更好地组织代码和数据。主要包括：
    *   `src/`: 存放所有核心的 Python源代码。
        *   `src/app/`: 存放应用的主要逻辑，包括 Flask 入口、聊天处理、产品管理、策略管理和意图识别等模块。
        *   `src/core/`: 存放核心的辅助模块，如缓存管理。
        *   `src/config/`: 存放应用配置。
        *   `src/models/`: 存放训练好的机器学习模型文件（例如意图识别模型）。
        *   `src/scripts/`: 存放辅助脚本。
    *   `data/`: 存放所有数据文件，如 CSV 文件、JSON 数据等。
    *   `docs/`: 存放所有的 Markdown 文档。
    *   `static/` 和 `templates/`: 这两个目录将保持在项目根目录下。
    *   `tests/`: 测试目录也将保持在项目根目录下。

2.  **移动并重命名文件**：
    现有的文件将按照其功能被移动到新的目录结构中，部分文件可能会被重命名。
    *   `app.py` -> `src/app/main.py`
    *   `chat_handler.py` -> `src/app/chat/handler.py`
    *   `product_manager.py` -> `src/app/products/manager.py`
    *   `policy_manager.py` -> `src/app/policy/manager.py`
    *   `intent_classifier.py` -> `src/app/intent/classifier.py`
    *   `train_intent_model.py` -> `src/app/intent/trainer.py`
    *   `cache_manager.py` -> `src/core/cache.py`
    *   `config.py` -> `src/config/settings.py`
    *   `products.csv` -> `data/products.csv`
    *   `intent_training_data.csv` -> `data/intent_training_data.csv`
    *   `policy.json` -> `data/policy.json`
    *   `find_large_files.py` -> `src/scripts/find_large_files.py`
    *   所有 `.md` 文件 ( `README.md`, `deployment_plan.md`, etc.) -> `docs/` (可以保留一个顶层的 `README.md`)
    *   `intent_model/` 目录 (如果存在) -> `src/models/intent_model/`

3.  **添加 `__init__.py` 文件**：
    在 `src/` 下的每个新模块目录 (`app`, `app/chat`, `app/products`, `app/policy`, `app/intent`, `core`, `config`) 中创建空的 `__init__.py` 文件。

4.  **更新代码中的导入路径**：
    在所有移动和重命名的 `.py` 文件中，以及 `tests/` 下的测试文件中，更新所有的 `import` 语句以反映新的文件结构。

5.  **更新文件路径引用**：
    代码中所有硬编码的文件路径引用（例如加载数据文件、模型文件）都需要更新。
    对于 Flask 应用，如果主应用文件移动到了 `src/app/main.py`，而 `templates` 和 `static` 文件夹仍在根目录，需要调整 Flask 应用实例的创建方式：`app = Flask(__name__, template_folder='../../templates', static_folder='../../static')`。

6.  **调整测试配置**：
    确保 `tests/` 目录下的测试用例能够找到并导入位于 `src/` 目录下的模块。

7.  **更新文档**：
    更新项目文档（如 `README.md`）以反映新的项目结构。

## 整理后的项目结构示意图 (Mermaid Diagram):

```mermaid
graph TD
    Root[项目根目录]

    Root --> src[src/]
    Root --> data[data/]
    Root --> static[static/]
    Root --> templates[templates/]
    Root --> tests[tests/]
    Root --> docs[docs/]
    Root --> OtherFiles(...)

    subgraph src
        direction TB
        AppDir[app/]
        CoreDir[core/]
        ConfigDir[config/]
        ModelsDir[models/]
        ScriptsDir[scripts/]
    end

    subgraph AppDirGraph [app/]
        direction TB
        AppMainPy(main.py)
        ChatMod[chat/]
        ProductMod[products/]
        PolicyMod[policy/]
        IntentMod[intent/]
    end
    AppDir --> AppMainPy
    AppDir --> ChatMod
    AppDir --> ProductMod
    AppDir --> PolicyMod
    AppDir --> IntentMod

    ChatMod --> ChatHandlerPy(handler.py)
    ProductMod --> ProductManagerPy(manager.py)
    PolicyMod --> PolicyManagerPy(manager.py)
    IntentMod --> IntentClassifierPy(classifier.py)
    IntentMod --> IntentTrainerPy(trainer.py)

    CoreDir --> CoreCachePy(cache.py)
    ConfigDir --> ConfigSettingsPy(settings.py)
    ModelsDir --> TrainedIntentModel(intent_model/)
    ScriptsDir --> FindLargePy(find_large_files.py)

    subgraph data
        direction TB
        DataProducts(products.csv)
        DataIntent(intent_training_data.csv)
        DataPolicy(policy.json)
    end

    subgraph static
        direction TB
        StaticChatJS(chat.js)
        StaticStyleCSS(style.css)
    end

    subgraph templates
        direction TB
        TemplatesIndexHTML(index.html)
    end

    subgraph tests
        direction TB
        TestFiles(test_*.py)
    end

    subgraph docs
        direction TB
        DocFiles(*.md)
    end