from app.models.context import QueryContext, Intent
from app.utils.logging import get_logger

log = get_logger("prompt_builder")

class PromptBuilder:
    """
    Generates tailored instruction prompts based on QueryContext intent,
    injecting retrieved contexts and metadata.
    """
    
    @staticmethod
    def build(context: QueryContext) -> str:
        """
        Public contract method to generate prompt templates based on intent.
        Saves result inside context.prompt and returns it.
        """
        context.start_stage("prompt_construction")
        try:
            log.info(f"Generating prompt for intent: {context.intent.value}")
            
            # Format context block
            context_str = PromptBuilder._format_context(context)
            
            # Select prompt template based on intent
            if context.intent == Intent.EXPLAIN_LAW:
                prompt = PromptBuilder._explain_law_prompt(context.question, context_str)
            elif context.intent == Intent.CASE_SEARCH:
                prompt = PromptBuilder._case_search_prompt(context.question, context_str)
            elif context.intent == Intent.LEGAL_RESEARCH:
                prompt = PromptBuilder._legal_research_prompt(context.question, context_str)
            elif context.intent == Intent.DOCUMENT_QA:
                prompt = PromptBuilder._document_qa_prompt(context.question, context_str)
            elif context.intent == Intent.DOCUMENT_SUMMARY:
                prompt = PromptBuilder._document_summary_prompt(context_str)
            elif context.intent == Intent.DOCUMENT_COMPARISON:
                prompt = PromptBuilder._document_comparison_prompt(context_str)
            elif context.intent == Intent.GENERAL_CHAT:
                prompt = PromptBuilder._general_chat_prompt(context.question)
            else:
                prompt = PromptBuilder._fallback_prompt(context.question, context_str)
                
            context.prompt = prompt
            return prompt
        finally:
            context.end_stage("prompt_construction")

    @staticmethod
    def _format_context(context: QueryContext) -> str:
        """Helper to format expanded node lists into a structured text context block."""
        blocks = []
        source_nodes = context.expanded_nodes if context.expanded_nodes else context.retrieved_nodes
        for idx, node in enumerate(source_nodes, 1):
            doc_id = node.get("document_id", "Unknown")
            node_type = node.get("node_type", "section").upper()
            node_num = node.get("node_number", "")
            title = node.get("title", "")
            text = node.get("text_content", "")
            
            # Build parent breadcrumb list if present
            breadcrumbs = " > ".join([f"{p.get('node_number', '')} {p.get('title', '')}".strip() for p in node.get("parents", [])])
            header = f"[{idx}] Source Document: {doc_id} | Location: {breadcrumbs} > {node_num} {title}".strip(" > ")
            
            block = f"--- CONTEXT REFERENCE {idx} ---\n{header}\n\nContent:\n{text}\n"
            
            # Add child nodes (subsections/clauses) if present
            if node.get("children"):
                children_text = []
                for child in node["children"]:
                    c_num = child.get("node_number", "")
                    c_text = child.get("text_content", "")
                    children_text.append(f"  {c_num}: {c_text}")
                block += "\nSub-elements:\n" + "\n".join(children_text) + "\n"
                
            # Add citations/references if present
            if node.get("outbound_references"):
                refs = [r["citation_text"] for r in node["outbound_references"]]
                block += f"\nCites/References: {', '.join(refs)}\n"
                
            blocks.append(block)
            
        return "\n\n".join(blocks) if blocks else "No retrieved context available."

    @staticmethod
    def _explain_law_prompt(question: str, context_str: str) -> str:
        return f"""You are a professional legal expert in Indian Law.
Your task is to explain the following statute, article, or rule based strictly on the retrieved context below.

=== RETRIEVED LEGAL CONTEXT ===
{context_str}
===============================

Instructions:
1. Base your answer ONLY on the provided legal context.
2. State when information is insufficient to answer the question; DO NOT make up answers or cite external laws not present in the context.
3. Keep the tone formal, logical, and highly structured.
4. Cite the exact Section, Article, or Rule number at the end of statements.
5. If the retrieved text indicates it was amended, mention that in your answer.

User Question: {question}
Answer:"""

    @staticmethod
    def _case_search_prompt(question: str, context_str: str) -> str:
        return f"""You are a legal researcher specializing in Indian Supreme Court and High Court judgments.
Your task is to analyze the case laws and judgments retrieved below to answer the user's question.

=== RETRIEVED JUDGMENTS ===
{context_str}
===========================

Instructions:
1. Identify the core facts, issues raised, ratio decidendi, and final holdings from the retrieved judgments.
2. Synthesize how these cases relate to the user's question.
3. Base your analysis ONLY on the cases provided. Do not assume or hallucinate case citations or holdings.
4. Clearly separate established facts of the cases from judicial interpretations and ratios.

User Question: {question}
Answer:"""

    @staticmethod
    def _legal_research_prompt(question: str, context_str: str) -> str:
        return f"""You are a senior advocate performing legal research.
Analyze the relationship between the retrieved statutes, rules, and judgments below to answer the user's question.

=== RETRIEVED STATUTES & CASE LAWS ===
{context_str}
======================================

Instructions:
1. Explain how the retrieved statutes/rules apply to the issue, and how the court judgments have interpreted or applied these laws.
2. Draw clear logical connections between different articles, sections, or rules cited in the context.
3. Be highly objective. If the retrieved legal documents contain conflicting views, state them clearly.
4. Ground every statement in a specific citation from the retrieved context.

User Question: {question}
Answer:"""

    @staticmethod
    def _document_qa_prompt(question: str, context_str: str) -> str:
        return f"""You are a contract analysis assistant.
Answer the user's question regarding their uploaded document using the retrieved text chunks below.

=== RETRIEVED DOCUMENT CHUNKS ===
{context_str}
==================================

Instructions:
1. Answer the question based ONLY on the provided text chunks.
2. You MUST cite the exact page numbers (e.g. "[Page X]") for every fact you extract.
3. If the retrieved text does not contain the answer, say "I cannot find this information in the document." Do not invent facts or obligations.

User Question: {question}
Answer:"""

    @staticmethod
    def _document_summary_prompt(context_str: str) -> str:
        return f"""You are an expert legal summarizer.
Provide a structured executive summary of the document text below.

=== DOCUMENT CHUNKS ===
{context_str}
========================

Instructions:
1. Highlight the following elements:
   - Purpose / Objective of the document.
   - Core parties involved.
   - Major obligations / covenants of each party.
   - Termination terms and consequences of breach.
   - Governing law and dispute resolution mechanism.
2. Be concise, bulleted, and structured.
3. Include page numbers where key clauses are located.

Summary:"""

    @staticmethod
    def _document_comparison_prompt(context_str: str) -> str:
        return f"""You are a legal contract auditor.
Compare the clauses of the two documents provided below.

=== RETRIEVED CLAUSES ===
{context_str}
=========================

Instructions:
1. Align similar clauses (e.g. Termination, Confidentiality, Indemnification).
2. Explicitly identify additions, removals, and modifications between the two versions.
3. Summarize the legal impact of these changes (e.g., "Version B shifts liability to Party A compared to Version A").
4. Present differences in a clear, comparative layout.

Comparison Report:"""

    @staticmethod
    def _general_chat_prompt(question: str) -> str:
        return f"""You are a helpful AI legal assistant.
Provide general information on the legal topic requested.

User Question: {question}

Instructions:
1. Note that you are an AI, and this is for informational purposes only, not formal legal counsel.
2. Keep the answer clear and easy to understand.
3. Since no specific law or case context was retrieved, explain general legal concepts associated with the question.
Answer:"""

    @staticmethod
    def _fallback_prompt(question: str, context_str: str) -> str:
        return f"""You are a legal assistant. Answer the question based on the retrieved context.

Context:
{context_str}

Question: {question}
Answer:"""
