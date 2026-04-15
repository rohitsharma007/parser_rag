# Java Selenium Parser — Tree-sitter RAG Pipeline

A production-ready **AST-based parser** for Java Selenium test files, exposed via a FastAPI REST API with Swagger UI.  
Built for use as a **standalone module**, a **REST service**, or a **RAG ingestion component**.

---

## Table of Contents

1. [What This Project Does](#1-what-this-project-does)
2. [Project Structure](#2-project-structure)
3. [What is Tree-sitter?](#3-what-is-tree-sitter)
4. [How Tree-sitter Works Internally](#4-how-tree-sitter-works-internally)
5. [Why Tree-sitter Instead of Regex or Python AST](#5-why-tree-sitter-instead-of-regex-or-python-ast)
6. [How parser.py Traverses the AST](#6-how-parserpy-traverses-the-ast)
7. [Role in Embedding and RAG Pipelines](#7-role-in-embedding-and-rag-pipelines)
8. [Integrating parser.py with Any Ingestion File](#8-integrating-parserpy-with-any-ingestion-file)
9. [Libraries Reference](#9-libraries-reference)
10. [Installation](#10-installation)
11. [Running the API](#11-running-the-api)
12. [API Endpoints](#12-api-endpoints)
13. [Sample JSON Output](#13-sample-json-output)

---

## 1. What This Project Does

This project parses Java Selenium test source files using a **real language grammar** (not regex) and extracts structured metadata:

- Class names and class-level annotations (`@RunWith`, `@Suite`, etc.)
- Method names, full source code, and method-level annotations (`@Test`, `@Before`, `@After`, etc.)
- Comments immediately preceding each method (line comments and block comments)
- Selenium API calls detected inside each method body (`driver.get()`, `findElement()`, `click()`, `sendKeys()`, etc.)

All output is returned as structured JSON, making it directly consumable by vector databases, embedding models, or LLM-based pipelines.

---

## 2. Project Structure

```
parser_rag/
├── parser.py          # Core Tree-sitter parser — importable as a module
├── main.py            # FastAPI REST API wrapping parser.py
├── requirements.txt   # All dependencies
└── samples/           # Built-in Java Selenium test files for testing
    ├── LoginTest.java
    ├── SearchTest.java
    └── CheckoutTest.java
```

---

## 3. What is Tree-sitter?

[Tree-sitter](https://tree-sitter.github.io/tree-sitter/) is an **incremental parsing library** originally built for the Atom editor, now used by Neovim, GitHub, VS Code, and many others for syntax highlighting and code navigation.

### Core idea

Tree-sitter generates **language parsers from formal grammars**. Each grammar is a precise mathematical description of what valid code looks like in a language. When you feed source code to the parser, it produces a **Concrete Syntax Tree (CST)** — a tree where every single token (keyword, identifier, bracket, semicolon) has a corresponding node with an exact byte range in the original source.

### Key properties

| Property | What it means |
|---|---|
| **Grammar-driven** | Understands the actual structure of the language, not just character patterns |
| **Incremental** | Can re-parse only the part of the file that changed (used in editors) |
| **Error-tolerant** | Produces a partial tree even on syntactically invalid code |
| **Language-agnostic** | Same Python API works for Java, Python, JS, Go, Rust, C, etc. |
| **Byte-precise** | Every node knows its exact `start_byte` and `end_byte` in the source |

---

## 4. How Tree-sitter Works Internally

### Step 1 — Grammar definition

A Tree-sitter grammar is written in JavaScript and describes the language using a PEG-like (Parsing Expression Grammar) syntax. For Java, it defines rules like:

```
class_declaration:
  modifiers?          ← @RunWith(...) public etc.
  "class"
  identifier          ← the class name
  superclass?
  interfaces?
  class_body          ← { ... }

method_declaration:
  modifiers?
  type_identifier
  identifier          ← method name
  formal_parameters
  block               ← { method body }
```

### Step 2 — Parser generation

The grammar is compiled into a **C parser** (`tree-sitter-java` ships this pre-compiled). The Python package `tree-sitter` provides bindings to call this C parser from Python.

### Step 3 — Parsing in Python

```python
from tree_sitter import Language, Parser
import tree_sitter_java as tsjava

lang   = Language(tsjava.language())   # load the compiled Java grammar
parser = Parser(lang)

source = b'public class LoginTest { @Test public void test() {} }'
tree   = parser.parse(source)
root   = tree.root_node
```

`root` is now a `Node` object that is the root of the CST.

### Step 4 — The Concrete Syntax Tree

For the source above, Tree-sitter produces:

```
program
└── class_declaration
    ├── modifiers
    │   └── "public"
    ├── "class"
    ├── identifier        "LoginTest"
    └── class_body
        ├── "{"
        ├── method_declaration
        │   ├── modifiers
        │   │   ├── marker_annotation   "@Test"
        │   │   └── "public"
        │   ├── void_type
        │   ├── identifier              "test"
        │   ├── formal_parameters       "()"
        │   └── block                   "{}"
        └── "}"
```

### Step 5 — Node navigation

Every `Node` exposes:

```python
node.type          # e.g. "class_declaration", "method_declaration"
node.is_named      # True for meaningful nodes, False for punctuation
node.children      # list of all child nodes (named + anonymous)
node.parent        # parent node
node.prev_sibling  # previous sibling at the same level
node.next_sibling  # next sibling
node.start_byte    # byte offset where this node starts
node.end_byte      # byte offset where this node ends
node.child_by_field_name("name")  # get a specifically labelled child
source[node.start_byte:node.end_byte]  # extract the original source text
```

---

## 5. Why Tree-sitter Instead of Regex or Python AST

### Regex — why it fails for code

Regex matches flat character sequences. Java code is deeply nested and context-sensitive:

```java
// A regex looking for @Test would also match this comment: @Test
// A regex looking for method names can't distinguish overloaded methods
// A regex can't tell you that a method is inside a class, not a nested class
```

Regex has no concept of scope, nesting, or language structure. It produces false positives and misses edge cases constantly.

### Python's `ast` module — why it doesn't help here

Python's `ast` module parses **Python** source code only. It cannot parse Java.

### `javalang` / `plyj` — why they're insufficient

Older Java parsers for Python (like `javalang`) are regex/hand-written parsers that:
- Do not support modern Java syntax (records, sealed classes, text blocks)
- Crash or silently skip malformed code instead of producing partial results
- Return data structures you cannot extend without forking the library

### Tree-sitter — why it wins

| Concern | Tree-sitter |
|---|---|
| Modern Java syntax | Fully supported — grammar is maintained by the community |
| Malformed code | Produces a partial tree with `ERROR` nodes, never crashes |
| Byte-precise ranges | Every node → exact slice of the original source string |
| Multi-language | Same API works for any language with a grammar |
| Speed | C parser — parses large files in milliseconds |
| Comment access | Comments are first-class nodes in the CST |

---

## 6. How parser.py Traverses the AST

### Full traversal pipeline

```
Java source bytes
       │
       ▼
  tree_sitter Parser.parse(source)
       │
       ▼
  root_node  (type: "program")
       │
       ├── for each child of type "class_declaration"
       │         │
       │         ├── extract class name       ← first "identifier" child
       │         ├── extract annotations      ← "modifiers" → marker/normal_annotation nodes
       │         └── class_body children
       │                   │
       │                   ├── for each "method_declaration"
       │                   │         │
       │                   │         ├── method name        ← "identifier" child
       │                   │         ├── annotations        ← "modifiers" child
       │                   │         ├── full source        ← source[start_byte:end_byte]
       │                   │         ├── preceding comments ← walk prev_sibling ←
       │                   │         └── selenium actions   ← DFS for method_invocation nodes
       │                   │
       │                   └── (other node types skipped)
       │
       ▼
  ParseResult → .to_dict() → JSON
```

### Comment extraction — why it's non-obvious

Comments in Tree-sitter are **sibling nodes**, not children of the declaration they document. To collect comments above a method, you walk `prev_sibling` backwards and stop at the first non-comment node:

```
class_body
  ├── line_comment      "// Sets up the browser"    ← prev_sibling of setUp
  ├── method_declaration  setUp()
  ├── block_comment     "/* Tests login flow */"     ← prev_sibling of testLogin
  ├── method_declaration  testLogin()
  └── method_declaration  tearDown()                 ← no preceding comment sibling
```

```python
sibling = method_node.prev_sibling
while sibling and sibling.type in ("line_comment", "block_comment"):
    comments.append(source[sibling.start_byte:sibling.end_byte])
    sibling = sibling.prev_sibling
comments.reverse()   # restore source order
```

### Selenium action detection — chained calls

Selenium code often chains method calls:

```java
driver.findElement(By.id("username")).sendKeys("admin");
```

Tree-sitter models this as **nested** `method_invocation` nodes:

```
method_invocation  [sendKeys]
└── object: method_invocation  [findElement]
    └── object: identifier  "driver"
```

`parser.py` uses **byte-range containment** to deduplicate: if a `method_invocation` node's byte range is fully inside another collected node's range, it is suppressed. Only the outermost call (the full chain) is reported.

---

## 7. Role in Embedding and RAG Pipelines

### The problem with naive chunking

Traditional RAG pipelines split documents by character count or newlines:

```
chunk 1: "import org.junit.*;\nimport org.openqa..."
chunk 2: "public void testLogin() {\n  driver.get..."
chunk 3: "driver.findElement(By.id(\"username\"))..."
```

This destroys semantic boundaries. A method gets split mid-body. Its annotation (`@Test`) lands in a different chunk from its code. Retrieval quality degrades badly.

### AST-based chunking — what this parser enables

Each method extracted by `parser.py` is a **semantically complete unit**:

```json
{
  "name": "testSuccessfulLogin",
  "annotations": ["@Test"],
  "code": "@Test\npublic void testSuccessfulLogin() {\n    driver.get(...);\n    ...\n}",
  "comments": "// Tests successful login with valid credentials",
  "selenium_actions": ["driver.get(...)", "driver.findElement(...).sendKeys(...)", "..."]
}
```

When you embed this as a single vector:

- The embedding captures **what the method does** (Selenium actions + code)
- The embedding captures **what kind of test it is** (annotations like `@Test`, `@Before`)
- The embedding captures **intent** (from the comment/docstring)
- The class name provides **organizational context**

This produces far more accurate retrieval than arbitrary text chunks.

### Embedding strategy recommendation

```
One vector per method:
  text = f"Class: {class_name}\nAnnotations: {annotations}\n{comments}\n{code}"

Metadata stored alongside the vector:
  - file path
  - class name
  - method name
  - annotations list
  - selenium_actions list (filterable)
```

This lets you do both **semantic search** ("find tests that verify login") and **metadata filtering** ("only @Test methods", "only methods using findElement").

---

## 8. Integrating parser.py with Any Ingestion File

`parser.py` is designed to be imported as a plain Python module. The `JavaSeleniumParser` class has two public methods:

```python
parser.parse_file("LoginTest.java")          # reads from disk
parser.parse_source(java_code_string)        # parses from a string or bytes
# Both return a ParseResult with a .to_dict() method
```

### Direct usage

```python
import sys
sys.path.insert(0, "/path/to/parser_rag")
from parser import JavaSeleniumParser

parser = JavaSeleniumParser()
result = parser.parse_file("tests/LoginTest.java")

for cls in result.classes:
    for method in cls.methods:
        print(method.name, method.annotations, method.selenium_actions)
```

### With LangChain

```python
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import sys
sys.path.insert(0, "/path/to/parser_rag")
from parser import JavaSeleniumParser

java_parser = JavaSeleniumParser()

def java_file_to_documents(file_path: str) -> list[Document]:
    result = java_parser.parse_file(file_path)
    documents = []
    for cls in result.classes:
        for method in cls.methods:
            # Build a rich text representation for embedding
            text = (
                f"File: {result.file}\n"
                f"Class: {cls.name}\n"
                f"Annotations: {' '.join(method.annotations)}\n"
                f"Comment: {method.comments}\n"
                f"Selenium actions: {', '.join(method.selenium_actions)}\n"
                f"Code:\n{method.code}"
            )
            doc = Document(
                page_content=text,
                metadata={
                    "file": result.file,
                    "class": cls.name,
                    "method": method.name,
                    "annotations": method.annotations,
                    "selenium_actions": method.selenium_actions,
                }
            )
            documents.append(doc)
    return documents

# Ingest
docs = java_file_to_documents("tests/LoginTest.java")
vectorstore = FAISS.from_documents(docs, OpenAIEmbeddings())
vectorstore.save_local("java_index")

# Retrieve
results = vectorstore.similarity_search("how does login test work?", k=3)
```

### With LlamaIndex

```python
from llama_index.core import Document, VectorStoreIndex
import sys
sys.path.insert(0, "/path/to/parser_rag")
from parser import JavaSeleniumParser

java_parser = JavaSeleniumParser()

def parse_to_llama_docs(file_path: str) -> list[Document]:
    result = java_parser.parse_file(file_path)
    docs = []
    for cls in result.classes:
        for method in cls.methods:
            text = f"{method.comments}\n{method.code}"
            docs.append(Document(
                text=text,
                metadata={
                    "class_name": cls.name,
                    "method_name": method.name,
                    "annotations": ", ".join(method.annotations),
                    "selenium_actions": method.selenium_actions,
                    "source_file": result.file,
                }
            ))
    return docs

docs = parse_to_llama_docs("LoginTest.java")
index = VectorStoreIndex.from_documents(docs)
query_engine = index.as_query_engine()
response = query_engine.query("Which test verifies login with invalid credentials?")
```

### With sentence-transformers (local embeddings, no API key)

```python
from sentence_transformers import SentenceTransformer
import numpy as np
import sys
sys.path.insert(0, "/path/to/parser_rag")
from parser import JavaSeleniumParser

model = SentenceTransformer("all-MiniLM-L6-v2")
java_parser = JavaSeleniumParser()

result = java_parser.parse_file("LoginTest.java")

chunks = []
vectors = []

for cls in result.classes:
    for method in cls.methods:
        text = f"{method.comments}\n{method.code}"
        chunks.append({"meta": {"class": cls.name, "method": method.name}, "text": text})
        vectors.append(model.encode(text))

vectors = np.array(vectors)

# Query
query_vec = model.encode("test that verifies login fails with wrong password")
scores = np.dot(vectors, query_vec) / (np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_vec))
best = chunks[np.argmax(scores)]
print(best["meta"], best["text"][:200])
```

### With a bulk directory ingestion loop

```python
import pathlib, json, sys
sys.path.insert(0, "/path/to/parser_rag")
from parser import JavaSeleniumParser

java_parser = JavaSeleniumParser()
all_methods = []

for java_file in pathlib.Path("tests/").rglob("*.java"):
    result = java_parser.parse_file(java_file)
    for cls in result.classes:
        for method in cls.methods:
            all_methods.append({
                "file": result.file,
                "class": cls.name,
                "method": method.name,
                "annotations": method.annotations,
                "comments": method.comments,
                "code": method.code,
                "selenium_actions": method.selenium_actions,
            })

# Save as JSONL for downstream embedding pipeline
with open("methods.jsonl", "w") as f:
    for m in all_methods:
        f.write(json.dumps(m) + "\n")
```

---

## 9. Libraries Reference

### Core parsing

| Library | Version | Role |
|---|---|---|
| `tree-sitter` | ≥ 0.21.0 | The core parsing engine. Provides the `Language`, `Parser`, and `Node` classes. The C parser is called via Python bindings. |
| `tree-sitter-java` | ≥ 0.21.0 | Pre-compiled Java grammar for Tree-sitter. Exposes `language()` which returns a pointer to the C grammar, passed to `Language(...)` to activate it. |

**How they connect:**

```python
import tree_sitter_java as tsjava
from tree_sitter import Language, Parser

lang   = Language(tsjava.language())   # binds the Java grammar to the engine
parser = Parser(lang)                  # creates a stateful parser instance
tree   = parser.parse(b"public class X {}")
```

### API layer

| Library | Version | Role |
|---|---|---|
| `fastapi` | ≥ 0.111.0 | Web framework. Handles routing, request validation, OpenAPI schema generation, and Swagger UI. |
| `uvicorn[standard]` | ≥ 0.29.0 | ASGI server that runs the FastAPI application. The `[standard]` extra adds `uvloop` (faster async event loop) and `httptools` (faster HTTP parsing). |
| `python-multipart` | ≥ 0.0.9 | Required by FastAPI to parse `multipart/form-data` requests — needed for `UploadFile` and `Form` fields. Without it, file uploads fail with a 400 error. |
| `pydantic` | ≥ 2.0 (via FastAPI) | Data validation and JSON schema generation. All request and response models in `main.py` are Pydantic `BaseModel` subclasses. FastAPI uses these to auto-generate the Swagger schema. |

### Standard library (no install needed)

| Module | Used for |
|---|---|
| `dataclasses` | `MethodInfo`, `ClassInfo`, `ParseResult` data containers in `parser.py` |
| `json` | Serialising parse output to JSON in the CLI mode |
| `argparse` | CLI argument parsing (`python parser.py <file> --pretty`) |
| `pathlib` | Cross-platform file path handling |
| `logging` | Structured log output to stderr (keeps stdout clean for JSON) |
| `sys` | `sys.path` manipulation, `sys.exit` in CLI mode |
| `time` | `time.perf_counter()` for request latency measurement in `main.py` |

---

## 10. Installation

```bash
# Clone the repo
git clone https://github.com/rohitsharma007/parser_rag.git
cd parser_rag

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
.venv\Scripts\activate          # Windows

# Install all dependencies
pip install -r requirements.txt
```

### requirements.txt

```
tree-sitter>=0.21.0
tree-sitter-java>=0.21.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
python-multipart>=0.0.9
```

---

## 11. Running the API

```bash
uvicorn main:app --reload
```

| URL | What you get |
|---|---|
| http://127.0.0.1:8000/docs | Swagger UI — interactive API explorer |
| http://127.0.0.1:8000/redoc | ReDoc — clean documentation view |
| http://127.0.0.1:8000/health | Health check JSON |

### CLI mode (no server needed)

```bash
# Parse a file, print compact JSON
python parser.py samples/LoginTest.java

# Parse a file, pretty-print JSON
python parser.py samples/LoginTest.java --pretty

# Parse a file and save output to a file
python parser.py samples/LoginTest.java --output result.json --pretty
```

---

## 12. API Endpoints

### `GET /health`
Returns `{"status": "ok", "parser_ready": true}`. Use this to verify the service is up.

### `GET /samples`
Lists the names of built-in samples: `LoginTest`, `SearchTest`, `CheckoutTest`.

### `GET /parse/sample/{name}`
Parses a built-in sample instantly — no file upload needed. Good first test after startup.

```
GET /parse/sample/LoginTest
GET /parse/sample/SearchTest
GET /parse/sample/CheckoutTest
```

### `POST /parse`
Accepts **one of**:

| Field | Type | Description |
|---|---|---|
| `file` | `UploadFile` | A `.java` file uploaded via multipart form |
| `code` | `string` (Form) | Raw Java source pasted as a text field |

Both inputs are supported from the Swagger UI under `/docs`.

---

## 13. Sample JSON Output

Running `GET /parse/sample/LoginTest` returns:

```json
{
  "file": "LoginTest.java",
  "classes": [
    {
      "class_name": "LoginTest",
      "annotations": ["@RunWith(JUnit4.class)"],
      "methods": [
        {
          "name": "setUp",
          "annotations": ["@Before"],
          "code": "@Before\npublic void setUp() {\n    driver = new ChromeDriver();\n    ...\n}",
          "comments": "",
          "selenium_actions": ["driver.manage().timeouts().implicitlyWait(10, TimeUnit.SECONDS)"]
        },
        {
          "name": "testSuccessfulLogin",
          "annotations": ["@Test"],
          "code": "@Test\npublic void testSuccessfulLogin() {\n    driver.get(\"https://example.com/login\");\n    ...\n}",
          "comments": "// Tests successful login with valid credentials",
          "selenium_actions": [
            "driver.get(\"https://example.com/login\")",
            "driver.findElement(By.id(\"username\")).sendKeys(\"admin\")",
            "driver.findElement(By.id(\"password\")).sendKeys(\"password123\")",
            "driver.findElement(By.id(\"loginBtn\")).click()",
            "driver.getTitle()"
          ]
        },
        {
          "name": "tearDown",
          "annotations": ["@After"],
          "code": "@After\npublic void tearDown() {\n    if (driver != null) {\n        driver.quit();\n    }\n}",
          "comments": "",
          "selenium_actions": ["driver.quit()"]
        }
      ]
    }
  ],
  "parse_time_ms": 3.42
}
```

---

## Architecture at a Glance

```
                     ┌─────────────────────────────┐
                     │        parser.py             │
                     │                              │
  .java file ───────►│  tree-sitter Parser          │
      OR             │    └─ Java grammar (.so)     │
  raw Java string    │         │                    │
                     │         ▼                    │
                     │    Concrete Syntax Tree      │
                     │         │                    │
                     │    AST traversal             │
                     │    ├── class names           │
                     │    ├── method names          │
                     │    ├── annotations           │
                     │    ├── comments              │──► ParseResult.to_dict()
                     │    └── selenium actions      │         │
                     └─────────────────────────────┘         │
                                                              │
              ┌───────────────────────────────────────────────┤
              │                                               │
              ▼                                               ▼
        main.py                                     ingestion.py
        FastAPI REST API                            (your pipeline)
        └── POST /parse                             └── LangChain Document
        └── GET /parse/sample/{name}               └── LlamaIndex Document
        └── Swagger UI /docs                        └── JSONL for FAISS/Pinecone
```
