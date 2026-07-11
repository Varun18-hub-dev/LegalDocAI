import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.config import RAW_DATA_DIR

MOCK_JUDGMENTS = [
    {
        "case_name": "Kesavananda Bharati v. State of Kerala",
        "citation": "(1973) 4 SCC 225",
        "bench": "13-judge Bench",
        "judges": ["S.M. Sikri", "J.M. Shelat", "K.S. Hegde", "A.N. Grover", "B. Jaganmohan Reddy", "D.G. Palekar", "H.R. Khanna", "A.K. Mukherjee", "Y.V. Chandrachud", "A.N. Ray", "K.K. Mathew", "M.H. Beg", "S.N. Dwivedi"],
        "decision_date": "1973-04-24",
        "acts": ["Constitution of India"],
        "sections": [],
        "articles": ["Article 368", "Article 13", "Article 14", "Article 19", "Article 31"],
        "keywords": ["basic structure doctrine", "constitutional amendment", "judicial review", "parliamentary sovereignty"],
        "facts": "The petitioner, head of the Edneer Mutt in Kerala, challenged the Kerala land reform acts under Article 26 of the Constitution, which guarantees the right to manage religiously owned property. During the pendency of the petition, Parliament passed the 24th, 25th, and 29th Constitutional Amendments, which curtailed the right to property and limited the scope of judicial review under Article 368.",
        "issues": "Whether Parliament's power to amend the Constitution under Article 368 is unlimited, and whether Parliament can amend or destroy the fundamental rights or the essential features of the Constitution.",
        "arguments": "The petitioner argued that Parliament has a limited power of amendment and cannot destroy the identity of the Constitution or its fundamental rights. The respondent argued that Article 368 grants absolute, unlimited power to amend any part of the Constitution, including fundamental rights.",
        "ratio_decidendi": "By a 7:6 majority, the Supreme Court held that while Parliament has wide powers to amend the Constitution, including the Fundamental Rights, it cannot amend or alter the 'Basic Structure' or essential features of the Constitution. The basic structure includes elements like democracy, republicanism, federalism, secularism, separation of powers, and judicial review.",
        "obiter_dicta": "The Constitution is a social document and must adapt to changing times, but the power to amend is not a power to destroy. The basic structure is the anchor of the Indian democracy.",
        "final_decision": "The 24th Amendment was upheld, but the second part of Article 31C (which barred judicial review) was declared unconstitutional. The Basic Structure Doctrine was established.",
        "relied_upon_cases": ["Sajjan Singh v. State of Rajasthan", "Golaknath v. State of Punjab"],
        "overruled_cases": ["Golaknath v. State of Punjab (partially)"],
        "distinguished_cases": []
    },
    {
        "case_name": "Maneka Gandhi v. Union of India",
        "citation": "(1978) 1 SCC 248",
        "bench": "7-judge Bench",
        "judges": ["M. Hameedullah Beg", "Y.V. Chandrachud", "P.N. Bhagwati", "V.R. Krishna Iyer", "N.L. Untwalia", "P.S. Kailasam", "S. Murtaza Fazal Ali"],
        "decision_date": "1978-01-25",
        "acts": ["Passport Act 1967", "Constitution of India"],
        "sections": ["Section 10(3)(c)"],
        "articles": ["Article 21", "Article 14", "Article 19"],
        "keywords": ["right to personal liberty", "due process of law", "natural justice", "passport impoundment"],
        "facts": "Maneka Gandhi's passport was impounded by the Regional Passport Office under Section 10(3)(c) of the Passport Act, 1967, 'in the interest of the general public'. She was not given any reasons for the impoundment, nor was she given a hearing before the decision was made. She challenged the passport office's order as a violation of her fundamental rights.",
        "issues": "Whether the right to go abroad is part of 'personal liberty' under Article 21, and whether Section 10(3)(c) of the Passport Act is violative of Article 14, 19, and 21 due to lack of fair procedure.",
        "arguments": "The petitioner argued that personal liberty includes the right to travel abroad and that any procedure restricting it must be fair, just, and reasonable, incorporating the principles of natural justice. The respondent argued that Article 21 only requires 'procedure established by law', which does not necessarily include audi alteram partem.",
        "ratio_decidendi": "The Supreme Court held that 'procedure established by law' under Article 21 cannot be arbitrary, unfair, or oppressive. It must be a 'right, just, and fair' procedure, which implicitly incorporates the American concept of procedural due process. The court expanded Article 21 by holding that it is linked to Article 14 and Article 19, and any law depriving personal liberty must pass the test of all three articles.",
        "obiter_dicta": "Natural justice is a great humanizing principle intended to invest law with fairness and prevent miscarriage of justice. Life is not merely physical existence; it includes the right to live with human dignity.",
        "final_decision": "The petition was disposed of after the Government agreed to give the petitioner a hearing and reconsider the passport impoundment.",
        "relied_upon_cases": ["Satwant Singh Sawhney v. Assistant Passport Officer"],
        "overruled_cases": ["A.K. Gopalan v. State of Madras"],
        "distinguished_cases": []
    }
]

def load_or_create_sc_judgments():
    """Retrieve SC judgments or save mock data locally for indexing."""
    dest_path = RAW_DATA_DIR / "supreme_court_judgments.json"
    
    # Save the mock judgments to raw folder
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(MOCK_JUDGMENTS, f, indent=4)
        
    print(f"  ✅ Supreme Court judgments saved at: {dest_path}")
    return dest_path

if __name__ == "__main__":
    load_or_create_sc_judgments()
