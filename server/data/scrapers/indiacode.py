import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.config import RAW_DATA_DIR

ACT_URLS = {
    "contract": {
        "name": "Indian Contract Act, 1872",
        "url": "https://www.indiacode.nic.in/bitstream/123456789/2187/1/A1872-9.pdf",
        "filename": "indian_contract_act_1872.pdf",
        "category": "civil_law"
    },
    "property": {
        "name": "Transfer of Property Act, 1882",
        "url": "https://www.indiacode.nic.in/bitstream/123456789/2338/1/A1882-04.pdf",
        "filename": "transfer_of_property_act_1882.pdf",
        "category": "property_law"
    },
    "specific_relief": {
        "name": "Specific Relief Act, 1963",
        "url": "https://www.indiacode.nic.in/bitstream/123456789/1572/1/196347.pdf",
        "filename": "specific_relief_act_1963.pdf",
        "category": "civil_law"
    }
}

def download_act(act_key):
    """Download an act PDF to data/raw/ directory."""
    act = ACT_URLS[act_key]
    dest_path = RAW_DATA_DIR / act["filename"]
    
    if dest_path.exists() and dest_path.stat().st_size > 50000:
        print(f"  📄 Act '{act['name']}' already exists locally.")
        return dest_path

    print(f"  📥 Downloading '{act['name']}' from: {act['url']}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(act["url"], headers=headers, timeout=30, stream=True)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"  ✅ Downloaded '{act['name']}' successfully.")
            return dest_path
        else:
            print(f"  ❌ Failed to download '{act['name']}'. Status code: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error downloading '{act['name']}': {e}")
        
    # Fallback: Create a mock Act PDF or text file for local testing
    print(f"  ⚠️  Creating mock text file for '{act['name']}' to allow pipeline testing.")
    mock_txt_path = dest_path.with_suffix(".txt")
    
    mock_act_contents = {
        "contract": """THE INDIAN CONTRACT ACT, 1872
        
        PART I. PRELIMINARY
        1. Short title.
        This Act may be called the Indian Contract Act, 1872.
        
        2. Interpretation-clause.
        In this Act, unless the context otherwise requires,-
        "agreement" means every promise and every set of promises, forming the consideration for each other.
        "contract" means an agreement enforceable by law.
        
        PART II. OF THE CONTRACTS
        CHAPTER I. OF THE COMMUNICATION, ACCEPTANCE AND REVOCATION OF PROPOSALS
        3. Communication, acceptance and revocation of proposals.
        The communication of proposals, acceptance of proposals, and revocation of proposals is complete...
        
        CHAPTER VI. OF THE CONSEQUENCES OF BREACH OF CONTRACT
        73. Compensation for loss or damage caused by breach of contract.
        When a contract has been broken, the party who suffers by such breach is entitled to receive, from the party who has broken the contract, compensation for any loss or damage caused to him thereby, which naturally arose in the usual course of things from such breach, or which the parties knew, when they made the contract, to be likely to result from the breach of it.
        Such compensation is not to be given for any remote and indirect loss or damage sustained by reason of the breach.
        
        74. Compensation for breach of contract where penalty stipulated for.
        When a contract has been broken, if a sum is named in the contract as the amount to be paid in case of such breach, or if the contract contains any other stipulation by way of penalty, the party complaining of the breach is entitled, whether or not actual damage or loss is proved to have been caused thereby, to receive from the party who has broken the contract reasonable compensation not exceeding the amount so named or, as the case may be, the penalty stipulated for.
        """,
        "specific_relief": """THE SPECIFIC RELIEF ACT, 1963
        
        PART I. PRELIMINARY
        1. Short title.
        This Act may be called the Specific Relief Act, 1963.
        
        PART II. SPECIFIC RELIEF
        CHAPTER I. RECOVERING POSSESSION OF PROPERTY
        5. Recovery of specific immovable property.
        A person entitled to the possession of specific immovable property may recover it in the manner provided by the Code of Civil Procedure, 1908.
        
        6. Suit by person dispossessed of immovable property.
        If any person is dispossessed without his consent of immovable property otherwise than in due course of law, he or any person claiming through him may, by suit, recover possession thereof, notwithstanding any other title that may be set up in such suit.
        No suit under this section shall be brought after the expiry of six months from the date of dispossession.
        
        CHAPTER VI. DECLARATORY DECREES
        34. Discretion of court as to declaration of status or right.
        Any person entitled to any legal character, or to any right as to any property, may institute a suit against any person denying, or interested to deny, his title to such character or right, and the court may in its discretion make therein a declaration that he is so entitled, and the plaintiff need not in such suit ask for any further relief.
        """
    }
    
    # Default fallback content if not in dict
    default_content = f"""THE {act['name'].upper()}
    
    PART I. PRELIMINARY
    1. Short title.
    This Act may be called the {act['name']}.
    """
    
    mock_content = mock_act_contents.get(act_key, default_content)
    mock_txt_path.write_text(mock_content, encoding="utf-8")
    print(f"  💾 Created mock text act at: {mock_txt_path}")
    return mock_txt_path

def download_all_acts():
    results = {}
    for key in ACT_URLS:
        results[key] = download_act(key)
    return results

if __name__ == "__main__":
    download_all_acts()
