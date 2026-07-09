import re
import sys
import uuid
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.models.database import insert_document, insert_hierarchy_node, insert_document_version, get_db_conn, insert_cross_reference
from scripts.chunker import chunk_constitution, chunk_act_by_sections

def parse_act_to_db(doc_id, title, full_text, category, year=None, source_url=None):
    """
    Parse Act or Rule into hierarchy and save to SQLite.
    Returns the list of created node dicts.
    """
    doc_type = "Central Act"
    if "rule" in doc_id or "rule" in title.lower():
        doc_type = "Rule"

    # 1. Insert the document meta record
    insert_document(
        doc_id=doc_id,
        document_type=doc_type,
        title=title,
        short_title=title,
        year=year,
        source_url=source_url,
        is_current=1,
        metadata_dict={"category": category}
    )

    # 2. Extract Parts, Chapters, and Sections/Rules
    # We split by Part, Chapter, Section/Article/Rule
    pattern = re.compile(
        r"^[ \t]*(?:"
        r"(PART\s+[IVXLC]+[A-Z]?\b)"
        r"|(CHAPTER\s+[IVXLC]+\b)"
        r"|((?:Section|Rule\s+)?\d+[A-Z]?\b\.?)"
        r")",
        re.MULTILINE | re.IGNORECASE
    )
    
    matches = list(pattern.finditer(full_text))
    
    if not matches:
        # Fallback: single node
        node_id = f"{doc_id}_full"
        insert_hierarchy_node(
            node_id=node_id,
            document_id=doc_id,
            node_type="full_text",
            node_number="Full",
            title=title,
            text_content=full_text,
            index_order=0
        )
        insert_document_version(node_id, "Original", full_text)
        return

    # Scan and build tree
    parent_part_id = None
    parent_chap_id = None
    
    # We need to filter article/section/rule nodes
    current_article = 0
    
    def is_constitution_article_title(line):
        line_text = line.strip()
        m = re.match(r"^\d+[A-Z]?\.\s*(.*)$", line_text)
        if not m:
            return False
        content = m.group(1).strip()
        clause_keywords = ["shall", "may", "no person", "every person", "deprived", "except in", "referred to", "specified in"]
        for kw in clause_keywords:
            if re.search(r"\b" + kw + r"\b", content, re.IGNORECASE):
                return False
        if content.endswith(".") and len(content.split()) > 10:
            return False
        return True

    valid_splits = []
    
    for i, match in enumerate(matches):
        gp_part = match.group(1)
        gp_chap = match.group(2)
        gp_sec = match.group(3)
        
        # Get line text
        start = match.start()
        line_start = full_text.rfind("\n", 0, start) + 1
        line_end = full_text.find("\n", start)
        if line_end == -1:
            line_end = len(full_text)
        line = full_text[line_start:line_end].strip()
        
        if gp_part:
            valid_splits.append((start, "part", gp_part, line))
        elif gp_chap:
            valid_splits.append((start, "chapter", gp_chap, line))
        elif gp_sec:
            # Clean section/rule number
            num_match = re.search(r"(\d+[A-Z]?)\b", gp_sec, re.IGNORECASE)
            if not num_match:
                continue
            sec_num = num_match.group(1)
            
            # Determine type and label prefix
            if doc_id == "constitution":
                node_type = "article"
                prefix = "Article"
            elif doc_type == "Rule":
                node_type = "rule"
                prefix = "Rule"
            else:
                node_type = "section"
                prefix = "Section"
                
            node_label = f"{prefix} {sec_num}"
            
            if sec_num.isdigit():
                val = int(sec_num)
                if node_type == "article":
                    # Sequential check to filter out sub-clauses in Constitution
                    if val == current_article:
                        continue
                    if current_article == 0 or (current_article <= val <= current_article + 5):
                        if not is_constitution_article_title(line):
                            continue
                        current_article = val
                        valid_splits.append((start, node_type, node_label, line))
                else:
                    # Limit Act sections to prevent matching years
                    if val > 600:
                        continue
                    valid_splits.append((start, node_type, node_label, line))
            else:
                valid_splits.append((start, node_type, node_label, line))

    # Parse segments
    for idx, split in enumerate(valid_splits):
        start = split[0]
        node_type = split[1]
        node_num = split[2]
        line_text = split[3]
        
        end = valid_splits[idx + 1][0] if idx + 1 < len(valid_splits) else len(full_text)
        segment_text = full_text[start:end].strip()
        
        # Remove numbers from title
        title = line_text
        for pattern_to_remove in [r"^PART\s+[IVXLC]+\.?", r"^CHAPTER\s+[IVXLC]+\.?", r"^(?:Section|Rule)\s+\d+[A-Z]?\.?", r"^\d+[A-Z]?\.\s*"]:
            title = re.sub(pattern_to_remove, "", title, flags=re.IGNORECASE).strip()
            
        # Create a unique node ID
        safe_num = node_num.replace(" ", "_").replace(".", "")
        node_id = f"{doc_id}_{safe_num}_{idx}"
        
        # Determine parent
        parent_id = None
        if node_type == "part":
            parent_part_id = node_id
            parent_chap_id = None  # Reset chapter parent
        elif node_type == "chapter":
            parent_id = parent_part_id
            parent_chap_id = node_id
        elif node_type in ("section", "article", "rule"):
            parent_id = parent_chap_id or parent_part_id
            
        # Insert node
        insert_hierarchy_node(
            node_id=node_id,
            document_id=doc_id,
            node_type=node_type,
            node_number=node_num,
            title=title,
            text_content=segment_text,
            parent_node_id=parent_id,
            index_order=idx
        )
        
        # Insert version record
        insert_document_version(node_id, "Original", segment_text)
        
        # Optional: Further parse the section text for Subsections/Explanations
        if node_type in ("section", "article", "rule") and len(segment_text) > 100:
            parse_section_subelements(node_id, doc_id, segment_text, idx)
            
    print(f"  🏛️  Parsed '{title[:30]}...' into SQLite hierarchy.")

def parse_section_subelements(section_node_id, doc_id, section_text, parent_order):
    """
    Sub-parse a section or rule text into sub-sections/sub-rules, provisos, explanations, and clauses.
    They are stored in document_hierarchy with parent_node_id set properly to build a tree.
    """
    lines = section_text.split("\n")
    sub_element_idx = 1
    
    is_rule = "rule" in doc_id or "rule" in section_node_id.lower()
    child_node_type = "sub_rule" if is_rule else "subsection"
    
    current_element_type = None
    current_element_num = None
    current_element_text = []
    
    active_parent_id = section_node_id
    
    def save_current_subelement():
        nonlocal sub_element_idx, active_parent_id
        if not current_element_text:
            return
        sub_text = "\n".join(current_element_text).strip()
        if len(sub_text) < 15:
            return
            
        sub_node_id = f"{section_node_id}_{current_element_type}_{sub_element_idx}"
        
        # Nested parent for clauses
        node_parent = section_node_id
        if current_element_type == "clause" and active_parent_id != section_node_id:
            node_parent = active_parent_id
            
        insert_hierarchy_node(
            node_id=sub_node_id,
            document_id=doc_id,
            node_type=current_element_type,
            node_number=current_element_num or str(sub_element_idx),
            title=f"{current_element_type.capitalize()} {current_element_num or sub_element_idx}",
            text_content=sub_text,
            parent_node_id=node_parent,
            index_order=parent_order * 100 + sub_element_idx
        )
        insert_document_version(sub_node_id, "Original", sub_text)
        
        if current_element_type in ("subsection", "sub_rule"):
            active_parent_id = sub_node_id
            
        sub_element_idx += 1
        current_element_text.clear()

    for line in lines[1:]: # skip first line (which is heading)
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # Check for Subsection / Sub-rule (e.g. "(1) Whoever...")
        subsec_match = re.match(r"^\((\d+)\)\s+(.*)$", line_stripped)
        # Check for Clause (e.g. "(a) the intermediary...")
        clause_match = re.match(r"^\(([a-z])\)\s+(.*)$", line_stripped)
        # Check for Explanation
        expl_match = re.match(r"^(Explanation\s*(?:[IVXLC]+)?\.-?)\s*(.*)$", line_stripped, re.IGNORECASE)
        # Check for Proviso
        proviso_match = re.match(r"^(Provided\s+that)\s*(.*)$", line_stripped, re.IGNORECASE)
        # Check for Illustration
        illus_match = re.match(r"^(Illustration\s*(?:[a-z])?\.-?)\s*(.*)$", line_stripped, re.IGNORECASE)
        
        if subsec_match:
            save_current_subelement()
            current_element_type = child_node_type
            current_element_num = f"({subsec_match.group(1)})"
            current_element_text.append(line_stripped)
        elif clause_match:
            save_current_subelement()
            current_element_type = "clause"
            current_element_num = f"({clause_match.group(1)})"
            current_element_text.append(line_stripped)
        elif expl_match:
            save_current_subelement()
            current_element_type = "explanation"
            current_element_num = expl_match.group(1)
            current_element_text.append(line_stripped)
        elif proviso_match:
            save_current_subelement()
            current_element_type = "proviso"
            current_element_num = "Proviso"
            current_element_text.append(line_stripped)
        elif illus_match:
            save_current_subelement()
            current_element_type = "illustration"
            current_element_num = illus_match.group(1)
            current_element_text.append(line_stripped)
        else:
            if current_element_type:
                current_element_text.append(line_stripped)
                
    save_current_subelement()

def parse_judgment_to_db(judgment):
    """
    Parse a structured Judgment record and insert it into SQLite.
    Splits the judgment into logical parts: Facts, Issues, Arguments, Ratio Decidendi.
    """
    doc_id = judgment["citation"].lower().replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")
    
    # 1. Insert document metadata
    insert_document(
        doc_id=doc_id,
        document_type="Judgment",
        title=judgment["case_name"],
        short_title=judgment["case_name"],
        year=int(judgment["decision_date"].split("-")[0]),
        source_url=None,
        publication_date=judgment["decision_date"],
        effective_date=judgment["decision_date"],
        is_current=1,
        metadata_dict={
            "court": "Supreme Court",
            "bench": judgment["bench"],
            "judges": judgment["judges"],
            "acts": judgment["acts"],
            "sections": judgment["sections"],
            "articles": judgment["articles"],
            "keywords": judgment["keywords"]
        }
    )
    
    # 2. Insert sections of judgment as hierarchy nodes
    sections_to_insert = [
        ("facts", "Facts of the Case", judgment["facts"]),
        ("issues", "Issues Raised", judgment["issues"]),
        ("arguments", "Arguments Advanced", judgment["arguments"]),
        ("ratio", "Ratio Decidendi", judgment["ratio_decidendi"]),
        ("obiter", "Obiter Dicta", judgment["obiter_dicta"]),
        ("holding", "Final Decision", judgment["final_decision"])
    ]
    
    for idx, (node_type, title, text) in enumerate(sections_to_insert):
        node_id = f"{doc_id}_{node_type}"
        insert_hierarchy_node(
            node_id=node_id,
            document_id=doc_id,
            node_type=node_type,
            node_number=node_type.upper(),
            title=title,
            text_content=text,
            parent_node_id=None,
            index_order=idx
        )
        insert_document_version(node_id, "Original", text)
        
    print(f"  ⚖️  Parsed Supreme Court Judgment: {judgment['case_name']}")

def parse_notification_to_db(notification):
    """
    Parse a structured Notification record and insert it into SQLite.
    Creates links to affected Acts and Sections.
    """
    doc_id = notification["id"]
    
    # 1. Insert document metadata
    insert_document(
        doc_id=doc_id,
        document_type="Notification",
        title=notification["title"],
        short_title=notification["number"],
        year=int(notification["date"].split("-")[0]),
        source_url=notification.get("source_url"),
        publication_date=notification["date"],
        effective_date=notification["effective_date"],
        is_current=1,
        metadata_dict={
            "number": notification["number"],
            "ministry": notification["ministry"],
            "affected_act": notification["affected_act"],
            "affected_rules": notification.get("affected_rules", []),
            "affected_sections": notification.get("affected_sections", [])
        }
    )
    
    # 2. Insert the notification text as a hierarchy node
    node_id = f"{doc_id}_content"
    insert_hierarchy_node(
        node_id=node_id,
        document_id=doc_id,
        node_type="notification_text",
        node_number=notification["number"],
        title=notification["title"],
        text_content=notification["content"],
        parent_node_id=None,
        index_order=0
    )
    insert_document_version(node_id, "Original", notification["content"])
    
    # 3. Create links to affected Act/Sections in cross_references
    with get_db_conn() as conn:
        for doc_name in [notification["affected_act"]] + notification.get("affected_rules", []):
            cursor = conn.execute("""
            SELECT id FROM documents 
            WHERE title LIKE ? OR id = ? OR short_title LIKE ?
            """, (f"%{doc_name}%", doc_name, f"%{doc_name}%"))
            row = cursor.fetchone()
            if row:
                tgt_doc_id = row["id"]
                for sec in notification.get("affected_sections", []):
                    # Check hierarchy node match (e.g. "Rule 3" or "Section 73")
                    sec_cursor = conn.execute("""
                    SELECT id FROM document_hierarchy 
                    WHERE document_id = ? AND (node_number LIKE ? OR title LIKE ?)
                    LIMIT 1
                    """, (tgt_doc_id, f"%{sec}%", f"%{sec}%"))
                    sec_row = sec_cursor.fetchone()
                    
                    tgt_node_id = sec_row["id"] if sec_row else None
                    insert_cross_reference(
                        source_node_id=node_id,
                        citation_text=f"{sec} of {doc_name}",
                        target_node_id=tgt_node_id,
                        reference_type="amends"
                    )
                    
    print(f"  📢 Parsed Government Notification: {notification['title']}")
