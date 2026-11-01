"""The four condition prompt templates (ADR-130/131, prompt_templates.md).

Every condition shares SYSTEM_INSTRUCTION, the DOCUMENTS block's rendering function, and the
question line verbatim -- render_documents_block is the *same function* for all four
conditions, including no_retrieval, so the "identical shape, varying content only" guarantee is
structural (the code cannot diverge the shape between conditions without editing this one
function), not just a convention followed by hand in four separate template strings.
"""

from dataclasses import dataclass

SYSTEM_INSTRUCTION = (
    "You are a clinical evidence assistant. Answer the clinical question below as accurately and\n"
    "as currently as possible.\n"
    "\n"
    "If documents are provided, base your answer on them and cite the specific document ID(s) you\n"
    "relied on. If no documents are provided, answer from your own knowledge.\n"
    "\n"
    "If the evidence is insufficient, contradictory, or you are not confident in an answer, say so\n"
    "explicitly rather than guessing.\n"
    "\n"
    "Respond in exactly this format:\n"
    "ANSWER: <your answer, one or two sentences>\n"
    "CITED_DOCUMENT_IDS: <comma-separated document IDs you relied on, or NONE>\n"
    "CONFIDENCE: <low, medium, or high>"
)

RETRIEVAL_K = 5  # fixed, not tuned -- sits inside the k=3-to-10 range real RAG systems use
# (author's instruction, ADR-131); if k changed the outcome, that would be its own paper.

NO_DOCUMENTS_PLACEHOLDER_ID = "none"
NO_DOCUMENTS_PLACEHOLDER_TITLE = "No documents retrieved."


@dataclass(frozen=True)
class RenderedDocument:
    doc_id: str
    title: str
    text: str = ""


NO_DOCUMENTS = RenderedDocument(doc_id=NO_DOCUMENTS_PLACEHOLDER_ID, title=NO_DOCUMENTS_PLACEHOLDER_TITLE)


def render_documents_block(docs: list[RenderedDocument]) -> str:
    """The one function every condition's DOCUMENTS block goes through, no_retrieval included
    (called with `[NO_DOCUMENTS]`) -- this is what makes "same shape, different content" a
    structural guarantee rather than a convention four separate template strings could drift
    out of alignment with.
    """
    entries = []
    for d in docs:
        header = f"[{d.doc_id}] {d.title}"
        entries.append(f"{header}\n{d.text}" if d.text else header)
    return "DOCUMENTS:\n" + "\n\n".join(entries)


def render_prompt(documents: list[RenderedDocument], question: str) -> str:
    """Shared assembly order for every condition's each individual turn:
    SYSTEM_INSTRUCTION -> DOCUMENTS -> QUESTION. post_notice's turn 2 is the only condition that
    inserts anything between DOCUMENTS and QUESTION (the reconsideration instruction) --
    render_post_notice_turn2_prompt below, not this function.
    """
    return f"{SYSTEM_INSTRUCTION}\n\n{render_documents_block(documents)}\n\nQUESTION: {question}"


def render_no_retrieval_prompt(question: str) -> str:
    return render_prompt([NO_DOCUMENTS], question)


def render_retrieval_prompt(documents: list[RenderedDocument], question: str) -> str:
    """Used for both retrieval_naive and retrieval_with_notice -- the two conditions differ only
    in which documents are passed in (plain top-k vs. top-k with the notice guaranteed present),
    never in how the prompt is assembled. Document-selection logic (the notice-injection rule)
    lives in rag/pipeline.py, not here -- this function only renders whatever list it's given.
    """
    return render_prompt(documents, question)


def render_post_notice_turn2_prompt(notice_doc: RenderedDocument, prior_answer: str, question: str) -> str:
    """Turn 2 of post_notice: the notice, the model's own prior answer (reused from a cached
    no_retrieval response, see rag/pipeline.py's build_post_notice_turn2), and a re-ask. This is
    the one condition whose assembly is not SYSTEM_INSTRUCTION -> DOCUMENTS -> QUESTION with
    nothing in between -- documented explicitly in prompt_templates.md as the sole structural
    exception, required by M3's own two-turn definition (the project protocol).
    """
    documents_block = render_documents_block([notice_doc])
    reconsider = (
        f'Your previous answer to this question was: "{prior_answer}"\n\nGiven this notice, reconsider your answer.'
    )
    return f"{SYSTEM_INSTRUCTION}\n\n{documents_block}\n\n{reconsider}\n\nQUESTION: {question}"
