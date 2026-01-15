# Multi-Document Chat (GenAI Project)

This repository contains a **GenAI-based multi-document chat application** built using modern Python tooling, Retrieval-Augmented Generation (RAG), and best engineering practices. It supports document ingestion, retrieval, evaluation, and scalable deployment.

---

## 🚀 Tech Stack & Tooling

* **Python**
* **UV** – Ultra-fast Python package manager
* **RAG (Retrieval-Augmented Generation)**
* **AWS (S3, CloudWatch)**
* **Jupyter Notebooks** for experimentation
* **Confident AI** for RAG evaluations

---

## 📦 UV Package Manager

**UV** is a modern Python package manager used to install dependencies, manage environments, and run Python projects.

### Why UV?

* Serves the same purpose as `pip`, but is **~10x faster**
* Written in **Rust**, leveraging highly optimized low-level code
* Provides reproducible builds using lock files

### Dependency Files

* **`pyproject.toml`**
  Manages high-level (direct) project dependencies.

* **`uv.lock`**
  Locks all resolved dependencies, including **nested/transitive dependencies**, ensuring consistency across environments.

---

## 📁 Project Structure

```text
.
├── data/
│   └── (Uploaded files, processed data, artifacts – ideal for S3 storage)
│
├── templates/
│   └── Frontend templates
│
├── static/
│   └── CSS and static assets
│
├── notebook/
│   ├── RAG.ipynb
│   └── evaluations.ipynb
│
├── tests/
│   └── Unit tests
│
├── multi_doc_chat/
│   ├── config/
│   │   └── config.yaml
│   │
│   ├── exception/
│   │   └── custom_exception.py
│   │
│   ├── logger/
│   │   └── custom_logger.py
│   │
│   ├── prompts/
│   │   └── Prompt templates
│   │
│   ├── utils/
│   │   ├── config_loader.py
│   │   ├── model_loader.py
│   │   ├── file_io.py
│   │   └── document_ops.py
│   │
│   └── src/
│       ├── document_ingestion/
│       │   └── data_ingestion.py
│       └── document_chat/
│           └── retrieval.py
│
├── requirements.txt
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 🧠 Core Components

### `config/`

Contains all application-level configuration files.

### `exception/`

Custom exception handling to standardize error reporting.

### `logger/`

Centralized logging system:

* Automatically configured for **AWS CloudWatch**
* Ensures consistent logging across the application

### `prompts/`

Stores all prompt templates used by the LLM.

### `utils/`

Reusable helper functions:

* **`config_loader.py`** – Loads `config.yaml` into a dictionary
* **`model_loader.py`** – Loads LLMs and embedding models
* **`file_io.py`** – Handles session IDs, directory creation, file uploads
* **`document_ops.py`** – Loads documents and extracts content

### `src/`

Core business logic:

* **Document ingestion**
* **Retrieval**
* **Chat orchestration**

---

## 📘 Learning Path (Recommended Study Order)

To understand the project end-to-end, follow this order:

1. `notebook/RAG.ipynb`
2. `multi_doc_chat/logger/custom_logger.py`
3. `multi_doc_chat/exception/custom_exception.py`
4. `multi_doc_chat/config/config.yaml`
5. Utilities:

   * `utils/config_loader.py`
   * `utils/model_loader.py`
   * `utils/file_io.py`
   * `utils/document_ops.py`
6. `src/document_ingestion/data_ingestion.py`
7. `src/document_chat/retrieval.py`
8. `notebook/evaluations.ipynb`
9. Confident AI for RAG evaluations

---

## 📊 RAG Evaluation

* Uses **Confident AI** to evaluate:

  * Retrieval accuracy
  * Answer faithfulness
  * Context relevance
* Evaluation workflows are documented in `notebook/evaluations.ipynb`

---

## ➕ Adding a New Dependency

Follow these steps to add a new Python package:

1. Add the package to `requirements.txt`
2. Run:

   ```bash
   uv add -r requirements.txt
   ```
3. Sync dependencies:

   ```bash
   uv sync
   ```

   This updates and locks dependencies in `uv.lock`

---

## 🧪 Testing

All unit tests are located in the `tests/` directory.

Run tests using your preferred test runner (e.g., `pytest`).

---

## 📌 Notes

* The `data/` directory is designed to be cloud-friendly and works well with **AWS S3**
* Logging is production-ready and CloudWatch-compatible
* The architecture is modular and scalable for larger GenAI applications

---

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.
Please follow standard Python best practices and ensure tests pass before submitting changes.
