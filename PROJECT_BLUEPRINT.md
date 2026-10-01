# Project Blueprint: Multi-Agent RAG for Regulatory Policy Change Management

Use this as a working capstone draft. The first implementation is intentionally a small, single-agent RAG system; the multi-agent workflow is a later project milestone. The architecture follows the core infrastructure pattern described for this project: document processing and embeddings, vector retrieval, LLM-grounded generation, and a user-facing interface. The separate LLMOps/evaluation layer is deferred.

## 1. Project summary

### Working title

**Multi-Agent RAG System for Regulatory Policy Change Management**

### Problem statement

Organizations must keep up with regulatory publications and understand what has changed, which policies or obligations may be affected, and where the supporting evidence appears. Reviewing lengthy documents manually is time-consuming. A language model used without reliable source retrieval can also produce unsupported or difficult-to-verify claims.

### Aim

Design and prototype a retrieval-augmented system that finds relevant passages in regulatory documents and presents evidence-backed answers, with a path to multi-agent change analysis.

### Proposed objectives

1. Ingest a controlled set of regulatory PDFs, preserve document and page provenance, and index searchable text.
2. Retrieve relevant passages for a user question and generate an answer grounded in those passages.
3. Show citations that let a user verify each answer against the source document.
4. Extend the baseline into a coordinated multi-agent workflow for comparing regulatory changes and identifying potential policy impacts.
5. Document the system's boundaries, assumptions, and limitations.

### Research question (draft)

> How can a citation-grounded RAG workflow help users identify and explain potential policy impacts of regulatory changes?

Refine this question once the target jurisdiction, document collection, and intended user group are agreed.

## 2. Scope

### Build first: core RAG

- Load local PDF files.
- Split extracted text into overlapping chunks while retaining source and page metadata.
- Create embeddings and store chunks in a persistent vector database.
- Retrieve relevant chunks for a question.
- Generate an answer using retrieved context, and display the source file and page citations.
- Provide a simple command-line query interface.

### Add after the core works: multi-agent regulatory workflow

- Represent a regulatory change as a comparison between an earlier and newer source.
- Use separately scoped agent roles, for example: change extraction, obligation analysis, policy-impact mapping, and evidence checking.
- Pass source excerpts and citations between steps; make the final synthesis distinguish evidence from inference and uncertainty.
- Keep a human reviewer responsible for accepting or rejecting suggested impacts.

These are proposed roles, not agents that the current code already implements. Start by proving the ingestion, retrieval, and citation path before splitting work across agents.

### Defer: LLMOps and formal evaluation

Do not build an experiment-tracking, monitoring, automated LLM-judge, or production evaluation pipeline in the first phase. Keep ordinary development checks (for example, verifying that ingestion works and that citations point to the retrieved pages); these are not a substitute for, or implementation of, the deferred LLMOps layer.

## 3. Core architecture

```text
PDF files
   │
   ▼
Load pages → split into chunks → attach provenance → create embeddings
                                              │
                                              ▼
                                      Persistent ChromaDB

User question → embed/search → retrieve relevant chunks
                                      │
                                      ▼
                         Prompt with question + evidence
                                      │
                                      ▼
                         LLM-grounded answer + citations
                                      │
                                      ▼
                              CLI / future UI
```

The first version keeps the vector store local and uses OpenAI for embeddings and answer generation. The current repository already contains the PDF ingestion, chunking, ChromaDB, query, and CLI foundation. It does not yet compare document versions, orchestrate agents, or provide a web interface.

## 4. Component outline

| Component | Responsibility | Initial implementation |
|---|---|---|
| Document source | Hold the PDFs selected for the prototype | `data/pdfs/` |
| Ingestion | Load PDF pages, split text, preserve source/page metadata | `src/regulatory_rag/ingestion.py` |
| Embeddings and vector store | Embed chunks and persist/retrieve them | `src/regulatory_rag/vector_store.py` |
| Retrieval and answer generation | Retrieve passages, prompt the LLM, format source citations | `src/regulatory_rag/query.py` |
| Configuration | Read model, paths, and chunk/retrieval settings | `src/regulatory_rag/config.py`, `.env` |
| User interface | Trigger ingestion and ask questions | `src/regulatory_rag/cli.py` |
| Agent orchestration | Coordinate future change-analysis roles | To be designed after baseline |
| LLMOps / formal evaluation | Track experiments and assess quality systematically | Explicitly deferred |

## 5. Initial functional requirements

- **Ingestion:** Process PDFs in the configured directory, including nested folders; fail clearly if the directory or documents are missing.
- **Provenance:** Associate each chunk with its source and page so retrieved evidence can be cited.
- **Indexing:** Persist embeddings locally so queries can reuse an ingested collection.
- **Retrieval:** Return a configurable number of relevant text chunks for a question.
- **Grounded response:** Instruct the model to answer from retrieved excerpts and say when evidence is insufficient.
- **Citations:** Display source filenames and human-readable page numbers alongside numbered citations.
- **Configuration:** Keep API credentials outside source control and allow paths and model settings to be configured.

For a later regulatory-focused iteration, consider capturing jurisdiction, regulator, publication date, effective date, document version, and superseded-document relationships. These fields require a defined metadata source and are not guaranteed by the current prototype.

## 6. Suggested implementation roadmap

1. **Baseline and data selection:** Choose a small, permitted PDF corpus; record its source, jurisdiction, and version. Run the existing `ingest` and `ask` commands.
2. **Core RAG walkthrough:** Verify that a question retrieves useful passages, answers stay within the evidence, and source/page citations resolve to the PDFs.
3. **Regulatory metadata:** Decide which metadata is necessary and add it consistently to document chunks and citations.
4. **Change-analysis workflow:** Add a way to select two versions of a regulatory document and identify candidate additions, removals, or amendments.
5. **Multi-agent workflow:** Define each role's input, output, evidence requirements, and hand-off; begin with the smallest useful set of agents.
6. **User review and presentation:** Present proposed impacts and evidence clearly, with an explicit review/confirmation step. Keep the CLI until a UI is justified.
7. **Later work:** Define evaluation questions and a LLMOps approach as a separate phase, outside the current scope.

## 7. Risks and design principles

- A citation is useful only if it points to the actual supporting passage; preserve page provenance and inspect citations during development.
- PDF extraction can omit tables, footnotes, or scanned content. Record corpus limitations and decide later whether OCR or table extraction is needed.
- Similarity search may miss relevant passages or retrieve adjacent but irrelevant material. Treat generated impact suggestions as candidates, not legal conclusions.
- Regulatory wording, effective dates, and document versions matter. Avoid comparing documents without establishing which versions and dates are being used.
- Do not place confidential or restricted documents in an external API unless their use is authorized.
- Keep a human reviewer in the loop for compliance or policy-impact decisions.

## 8. Decisions to fill in

- Target jurisdiction(s) and regulator(s):
- Intended user / organization:
- Initial document corpus and permission to use it:
- How will the previous and current versions of a regulation be identified?
- What does “policy impact” mean for the intended user?
- What outputs should an impact report contain?
- Which development environment and deployment target are required?
- What evaluation method will be considered in a future phase?

## 9. Running the current baseline

See [README.md](README.md) for Windows/VS Code setup. In short, install the package, configure `OPENAI_API_KEY` in `.env`, place PDFs in `data/pdfs/`, then run:

```powershell
python -m regulatory_rag.cli ingest
python -m regulatory_rag.cli ask "What are the main reporting obligations?"
```

The commands exercise the existing single-agent RAG baseline; they do not run a multi-agent change analysis or LLMOps evaluation.
