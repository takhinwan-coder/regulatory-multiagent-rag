# Project Blueprint: Multi-Agent RAG for Regulatory Policy Change Management

Use this as a working capstone draft. The initial pilot concerns HKMA prudential supervisory materials. The architecture combines document processing and embeddings, controlled version comparison, retrieval-grounded generation, and human review. Formal LLMOps and production deployment remain out of scope.

> **Overarching principle: Retrieve broadly; read precisely; draft conservatively; verify explicitly.**

## System workflow visual

The living [HKMA regulatory change workflow diagram](docs/hkma-regulatory-change-workflow.svg) presents the complete intended end-to-end flow, human decision gates, rework loops, release, and audit record. Update the SVG whenever the workflow changes.

The companion [HKMA RAG system workflow diagram](docs/hkma-rag-system-workflow.svg) presents the technical lifecycle behind that process: document ingestion, structure-aware chunking, embeddings and index creation, retrieval, grounded generation, human approval, and the evaluation loop.

## 1. Project summary

### Working title

**Multi-Agent RAG System for Regulatory Policy Change Management**

### Problem statement

Organizations must keep up with regulatory publications and understand what has changed, which policies or obligations may be affected, and where the supporting evidence appears. Reviewing lengthy documents manually is time-consuming. A language model used without reliable source retrieval can also produce unsupported or difficult-to-verify claims.

### Aim

Design and prototype a human-in-the-loop retrieval-augmented workflow that compares regulatory versions, finds relevant evidence, and presents reviewable potential policy impacts.

### Proposed objectives

1. Ingest a controlled set of regulatory PDFs, preserve document and page provenance, and index searchable text.
2. Retrieve relevant passages for a user question and generate an answer grounded in those passages.
3. Show citations that let a user verify each answer against the source document.
4. Compare selected regulatory document versions reproducibly and preserve the resulting change evidence.
5. Require a reviewer to confirm or supplement the affected-document scope before drafting is considered.
6. Extend the controlled workflow into specialized change, obligation, impact-mapping, drafting, and evidence-checking stages.
7. Document the system's boundaries, assumptions, and limitations.

### Research question (draft)

> How can a human-in-the-loop, citation-grounded RAG workflow help users identify and review potential policy impacts of changes to HKMA prudential regulatory materials?

Refine this question once the target jurisdiction, document collection, and intended user group are agreed.

## 2. Scope

### Current implementation

- Load local PDF files.
- Split extracted text into overlapping chunks while retaining source and page metadata.
- Create embeddings and store chunks in a persistent vector database.
- Retrieve relevant chunks for a question.
- Generate an answer using retrieved context, and display the source file and page citations.
- Provide a simple command-line query interface.
- Record regulatory source/version metadata at ingestion.
- Compare two selected PDF versions using a deterministic page-level text diff.
- Persist a human review decision that confirms or supplements the candidate document scope.

### Next: controlled hybrid retrieval and analysis workflow

- Parse provision structure and retain heading, provision, and parent-section relationships.
- Use metadata-filtered lexical and semantic retrieval, then rerank and expand to complete governing context.
- Identify candidate internal documents, but require the user to confirm, exclude, or supplement them before drafting.
- Pass source excerpts and citations between stages; make the final synthesis distinguish evidence from inference and uncertainty.

### Later: specialized multi-stage workflow

Use specialized stages only where their different tools, retrieval scopes, evidence standards, and outputs provide a control benefit:

1. source/version validation;
2. deterministic change extraction;
3. obligation analysis;
4. policy-impact mapping;
5. reviewer scope approval;
6. drafting options or controlled redlines;
7. evidence and consistency checking; and
8. human approval.

These stages should start as a sequential workflow with evidence-carrying hand-offs. They are not a justification for unbounded autonomous agents.

### Defer: LLMOps and formal evaluation

Do not build an experiment-tracking, monitoring, automated LLM-judge, or production evaluation pipeline in the first phase. Keep ordinary development checks (for example, verifying that ingestion works and that citations point to the retrieved pages); these are not a substitute for, or implementation of, the deferred LLMOps layer.

## 3. Core architecture

```text
PDF files
   │
   ▼
Load pages → attach source/version provenance → structure-aware chunking → create embeddings
                                              │
                                              ▼
                                      Persistent ChromaDB

Selected old/new sources → deterministic comparison → change report
                                              │
                                              ▼
Candidate internal documents → human review and scope decision
                                              │
                                              ▼
User question or approved task → metadata filter + lexical/vector search
                                      │
                                      ▼
                         Rerank + expand to parent/related provisions
                                      │
                                      ▼
                         Evidence-grounded answer or reviewable draft option
                                      │
                                      ▼
                         Human approval before a controlled amendment
```

The first version keeps the vector store local and uses OpenAI for embeddings and answer generation. The current repository contains the PDF ingestion, metadata-aware Chroma indexing, cited query path, deterministic PDF comparison, and CLI review-scope gate. It does not yet parse legal provisions structurally, provide hybrid retrieval, identify policy candidates automatically, generate drafts/redlines, or provide a web interface.

## 4. Component outline

| Component | Responsibility | Initial implementation |
|---|---|---|
| Document source | Hold the PDFs selected for the prototype | `data/pdfs/` |
| Ingestion | Load PDF pages, split text, preserve source/page metadata | `src/regulatory_rag/ingestion.py` |
| Embeddings and vector store | Embed chunks and persist/retrieve them | `src/regulatory_rag/vector_store.py` |
| Retrieval and answer generation | Retrieve passages, prompt the LLM, format source citations | `src/regulatory_rag/query.py` |
| Configuration | Read model, paths, and chunk/retrieval settings | `src/regulatory_rag/config.py`, `.env` |
| User interface | Trigger ingestion and ask questions | `src/regulatory_rag/cli.py` |
| Version comparison | Compare selected regulatory PDF versions reproducibly | `src/regulatory_rag/change_workflow.py` |
| Review scope | Record the reviewer-approved internal-document scope | `src/regulatory_rag/change_workflow.py`, `src/regulatory_rag/cli.py` |
| Source metadata | Validate document identity, authority, and version fields | `src/regulatory_rag/metadata.py` |
| Specialized workflow | Coordinate later change-analysis roles | To be designed after hybrid retrieval |
| LLMOps / formal evaluation | Track experiments and assess quality systematically | Explicitly deferred |

## 5. Initial functional requirements

- **Ingestion:** Process PDFs in the configured directory, including nested folders; fail clearly if the directory or documents are missing.
- **Provenance:** Associate each chunk with its source and page so retrieved evidence can be cited.
- **Indexing:** Persist embeddings locally so queries can reuse an ingested collection.
- **Retrieval:** Return a configurable number of relevant text chunks for a question.
- **Grounded response:** Instruct the model to answer from retrieved excerpts and say when evidence is insufficient.
- **Citations:** Display source filenames and human-readable page numbers alongside numbered citations.
- **Configuration:** Keep API credentials outside source control and allow paths and model settings to be configured.
- **Source metadata:** Validate source path, document identifier, title, jurisdiction, regulator, type, and version before adding available metadata to chunk records.
- **Version comparison:** Persist a deterministic report for two explicitly selected source PDFs.
- **Human review:** Persist the documents selected by a reviewer before a later drafting task may use them.

The current chunker remains character-based. Provision-aware hierarchical chunks and parent-section expansion are required before drafting or high-precision policy impact claims.

## 6. Suggested implementation roadmap

1. **Pilot corpus:** Select a small, permitted set of versioned HKMA prudential materials; complete the source metadata registry.
2. **Baseline validation:** Verify ingestion, citations, source metadata, PDF comparison, and reviewer scope records on the selected corpus.
3. **Structured ingestion:** Extract headings/provisions and create hierarchical chunks with parent/adjacent context.
4. **Hybrid retrieval:** Add metadata filtering, lexical retrieval, semantic retrieval, reranking, and context expansion.
5. **Policy-impact mapping:** Produce candidate internal documents/sections with evidence, then use the existing reviewer scope gate.
6. **Drafting workflow:** Generate evidence-linked amendment options only for approved documents and introduce an evidence-checking stage.
7. **Evaluation:** Hold out a later HKMA version; compare detected changes and proposed intent with that version without placing it in the retrieval corpus.
8. **Later work:** Define LLMOps and deployment separately.

## 7. Risks and design principles

- A citation is useful only if it points to the actual supporting passage; preserve page provenance and inspect citations during development.
- PDF extraction can omit tables, footnotes, or scanned content. Record corpus limitations and decide later whether OCR or table extraction is needed.
- Similarity search may miss relevant passages or retrieve adjacent but irrelevant material. Treat generated impact suggestions as candidates, not legal conclusions.
- Regulatory wording, effective dates, and document versions matter. Avoid comparing documents without establishing which versions and dates are being used.
- A page-level PDF diff is an extraction aid, not a reliable interpretation of tables, images, footnotes, or legal drafting intent.
- Long model context complements retrieval only after source versions and the full governing context have been selected.
- Do not allow a system to draft an amendment until a human has approved the internal-document scope.
- Do not place confidential or restricted documents in an external API unless their use is authorized.
- Keep a human reviewer in the loop for compliance or policy-impact decisions.

## 8. Decisions to fill in

- Target jurisdiction(s) and regulator(s): Hong Kong / Hong Kong Monetary Authority (HKMA)
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
