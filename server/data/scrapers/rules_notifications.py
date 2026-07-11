import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.config import RAW_DATA_DIR

def create_mock_rules_and_notifications():
    # 1. Create mock IT Rules 2021 text file
    rules_text = """INFORMATION TECHNOLOGY (INTERMEDIARY GUIDELINES AND DIGITAL MEDIA ETHICS CODE) RULES, 2021

PART I. PRELIMINARY
1. Short title and commencement.
(1) These rules may be called the Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021.
(2) They shall come into force on the date of their publication in the Official Gazette.

PART II. DUE DILIGENCE BY INTERMEDIARIES AND GRIEVANCE REDRESSAL MECHANISM
3. Due diligence to be observed by intermediary.
(1) The intermediary shall observe the following due diligence while discharging its duties, namely:-
(a) the intermediary shall prominently publish on its website, client application or both, the rules and regulations, privacy policy and user agreement for access-or usage of its computer resource by any person;
(b) the intermediary shall inform its users not to host, display, upload, modify, publish, transmit, store, update or share any information that belongs to another person.
(2) The intermediary shall, within twenty-four hours from the receipt of a complaint, take all reasonable steps to remove or disable access to such content.
Explanation.- For the purposes of this clause, "complaint" means any information received by the intermediary indicating a violation of these rules.
"""
    rules_path = RAW_DATA_DIR / "it_rules_2021.txt"
    rules_path.write_text(rules_text.strip(), encoding="utf-8")
    print(f"  💾 Created mock Rules file at: {rules_path}")

    # 2. Create mock IT Notification 2023 JSON file
    notification_data = {
        "id": "it_notification_2023",
        "document_type": "Notification",
        "title": "Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Amendment Rules, 2023",
        "number": "G.S.R. 275(E)",
        "date": "2023-04-06",
        "effective_date": "2023-04-06",
        "ministry": "Ministry of Electronics and Information Technology",
        "affected_act": "Information Technology Act, 2000",
        "affected_rules": ["it_rules_2021"],
        "affected_sections": ["Rule 3"],
        "content": "In the Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021, in rule 3, in sub-rule (1), in clause (b), after sub-clause (x), the following sub-clause shall be inserted, namely:- (xi) the intermediary shall make reasonable efforts to prevent the publishing of factually incorrect or misleading information concerning any business of the Central Government.",
        "source_url": "https://egazette.gov.in/WriteReadData/2023/244975.pdf"
    }
    
    notification_path = RAW_DATA_DIR / "it_notification_2023.json"
    with open(notification_path, "w", encoding="utf-8") as f:
        json.dump(notification_data, f, indent=4)
    print(f"  💾 Created mock Notification file at: {notification_path}")

if __name__ == "__main__":
    create_mock_rules_and_notifications()
