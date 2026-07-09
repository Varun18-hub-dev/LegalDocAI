"""
LegalDocAI - Legal Document Chunker
Splits legal text into meaningful chunks per Article/Section with metadata.
Unlike generic text splitting, this understands legal document structure.
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class LegalChunk:
    """A single chunk of legal text with metadata."""
    text: str
    metadata: dict = field(default_factory=dict)
    # metadata includes: source, category, article/section number, part, title, page_number


# ============================================================
# CONSTITUTION OF INDIA - Parser
# ============================================================

def chunk_constitution(full_text: str) -> list:
    """
    Parse Constitution of India into chunks per Article.
    Recognizes patterns like: "Article 14", "PART III", "Schedule I"
    """
    chunks = []
    
    # Skip Table of Contents
    actual_start = full_text.find("WE, THE PEOPLE OF INDIA")
    if actual_start != -1:
        preamble_pos = full_text.rfind("Preamble", 0, actual_start)
        if preamble_pos != -1:
            full_text = full_text[preamble_pos:]
        else:
            full_text = full_text[actual_start:]

    pattern = re.compile(
        r"^(?:"
        r"(PART\s+[IVXLC]+[A-Z]?)"
        r"|(SCHEDULE\s+[IVXLC]+)"
        r"|(\d{1,3})([A-Z]?)\.\s+"
        r")",
        re.MULTILINE | re.IGNORECASE
    )
    
    def is_article_title(line):
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

    matches = list(pattern.finditer(full_text))
    
    valid_splits = []
    current_article = 0
    
    for match in matches:
        gp_part = match.group(1)
        gp_sched = match.group(2)
        gp_num = match.group(3)
        gp_letter = match.group(4)
        
        # Get matching line
        start = match.start()
        line_start = full_text.rfind("\n", 0, start) + 1
        line_end = full_text.find("\n", start)
        if line_end == -1:
            line_end = len(full_text)
        line = full_text[line_start:line_end]
        
        if gp_part or gp_sched:
            valid_splits.append((match.start(), gp_part or gp_sched, "part" if gp_part else "schedule"))
        elif gp_num:
            val = int(gp_num)
            
            # Skip duplicates of the same article number
            if val == current_article and gp_letter == "":
                continue
                
            if current_article == 0 or (current_article <= val <= current_article + 5):
                if not is_article_title(line):
                    continue
                current_article = val
                label = f"{gp_num}{gp_letter or ''}"
                valid_splits.append((match.start(), label, "article"))

    # Now chunk based on valid splits
    if not valid_splits:
        return _fallback_chunk(full_text, "Constitution of India", "constitution")
        
    for i, split in enumerate(valid_splits):
        start = split[0]
        label = split[1]
        section_type = split[2]
        
        end = valid_splits[i + 1][0] if i + 1 < len(valid_splits) else len(full_text)
        section_text = full_text[start:end].strip()
        
        if len(section_text) < 20:
            continue
            
        title = section_text.split("\n")[0][:200]
        
        # Split large sections
        if len(section_text) > CHUNK_SIZE * 4:
            sub_chunks = _split_large_section(section_text)
            for j, sub_text in enumerate(sub_chunks):
                chunks.append(LegalChunk(
                    text=sub_text,
                    metadata={
                        "source": "Constitution of India",
                        "category": "constitution",
                        "section_type": section_type,
                        "article_number": label,
                        "title": title,
                        "sub_chunk": j + 1,
                        "total_sub_chunks": len(sub_chunks),
                    }
                ))
        else:
            chunks.append(LegalChunk(
                text=section_text,
                metadata={
                    "source": "Constitution of India",
                    "category": "constitution",
                    "section_type": section_type,
                    "article_number": label,
                    "title": title,
                }
            ))
            
    print(f"  📋 Constitution: {len(chunks)} chunks created")
    return chunks


# ============================================================
# BNS / BNSS / BSA - Parser (Section-based Acts)
# ============================================================

def chunk_act_by_sections(full_text: str, act_name: str, category: str) -> list:
    """
    Parse acts like BNS, BNSS, BSA into chunks per Section.
    Recognizes patterns like: "Section 303", "303.", "CHAPTER IV"
    """
    chunks = []

    # Pattern to find sections
    # Matches:
    # 1. "Section 303." or "Section 303"
    # 2. "303. " or "303.(1)" or "303.Whoever" at start of line / double newline
    # 3. "CHAPTER IV"
    section_pattern = re.compile(
        r"(?:^|\n\n)"
        r"((?:Section\s+\d+[A-Z]?\.?)"
        r"|(?:\b\d{1,4}\.(?=\s|[A-Za-z]|\())"
        r"|(?:CHAPTER\s+[IVXLC]+)"
        r")",
        re.MULTILINE | re.IGNORECASE
    )

    matches = list(section_pattern.finditer(full_text))

    if not matches:
        return _fallback_chunk(full_text, act_name, category)

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        section_text = full_text[start:end].strip()

        if len(section_text) < 20:
            continue

        # Extract section number
        section_match = re.search(r"(?:Section\s+)?(\d+[A-Z]?)", section_text, re.IGNORECASE)
        chapter_match = re.search(r"CHAPTER\s+([IVXLC]+)", section_text, re.IGNORECASE)

        section_num = ""
        section_type = "section"
        if section_match:
            section_num = section_match.group(1)
            # Filter out years or numbers > 600 (to prevent matching years as sections in footer/header)
            if section_num.isdigit() and int(section_num) > 600:
                continue
        elif chapter_match:
            section_num = chapter_match.group(1)
            section_type = "chapter"

        title = section_text.split("\n")[0][:200]

        # Split large sections
        if len(section_text) > CHUNK_SIZE * 4:
            sub_chunks = _split_large_section(section_text)
            for j, sub_text in enumerate(sub_chunks):
                chunks.append(LegalChunk(
                    text=sub_text,
                    metadata={
                        "source": act_name,
                        "category": category,
                        "section_type": section_type,
                        "section_number": section_num,
                        "title": title,
                        "sub_chunk": j + 1,
                        "total_sub_chunks": len(sub_chunks),
                    }
                ))
        else:
            chunks.append(LegalChunk(
                text=section_text,
                metadata={
                    "source": act_name,
                    "category": category,
                    "section_type": section_type,
                    "section_number": section_num,
                    "title": title,
                }
            ))

    print(f"  📋 {act_name}: {len(chunks)} chunks created")
    return chunks


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _split_large_section(text: str) -> list:
    """Split a large section into smaller sub-chunks with overlap."""
    words = text.split()
    sub_chunks = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_words = words[start:end]
        sub_chunks.append(" ".join(chunk_words))

        # Move forward with overlap
        start = end - CHUNK_OVERLAP

    return sub_chunks


def _fallback_chunk(full_text: str, source: str, category: str) -> list:
    """
    Fallback: If no Article/Section patterns found, split by character count.
    Uses LangChain-style recursive splitting.
    """
    chunks = []
    words = full_text.split()

    start = 0
    chunk_index = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_text = " ".join(words[start:end])

        chunks.append(LegalChunk(
            text=chunk_text,
            metadata={
                "source": source,
                "category": category,
                "section_type": "generic",
                "chunk_index": chunk_index,
            }
        ))

        start = end - CHUNK_OVERLAP
        chunk_index += 1

    print(f"  📋 {source}: {len(chunks)} chunks (fallback splitting)")
    return chunks


# ============================================================
# MAIN CHUNKING DISPATCHER
# ============================================================

def chunk_document(full_text: str, doc_key: str, source_config: dict) -> list:
    """
    Main function: routes to the right chunker based on document type.

    Args:
        full_text: Full extracted text from PDF
        doc_key: Key from DATA_SOURCES (e.g., "constitution", "bns")
        source_config: Config dict from DATA_SOURCES

    Returns:
        List of LegalChunk objects
    """
    category = source_config.get("category", "general")
    name = source_config.get("name", doc_key)

    print(f"\n  ✂️  Chunking: {name}")

    if doc_key == "constitution":
        return chunk_constitution(full_text)
    elif doc_key in ("bns", "bnss", "bsa"):
        return chunk_act_by_sections(full_text, name, category)
    else:
        return _fallback_chunk(full_text, name, category)


if __name__ == "__main__":
    # Quick test
    from app.config import PROCESSED_DATA_DIR, DATA_SOURCES

    for key, source in DATA_SOURCES.items():
        txt_file = PROCESSED_DATA_DIR / f"{Path(source['filename']).stem}.txt"
        if txt_file.exists():
            text = txt_file.read_text(encoding="utf-8")
            chunks = chunk_document(text, key, source)
            print(f"  Sample chunk: {chunks[0].text[:100]}...")
            print(f"  Metadata: {chunks[0].metadata}")
