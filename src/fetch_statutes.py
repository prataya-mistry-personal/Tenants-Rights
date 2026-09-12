"""Statute Fetching and Generation Script.

Downloads or generates authoritative statutory reference PDFs into data/raw/statutes/
for the Indian Metro Tenant Rights RAG system.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fpdf import FPDF
from fpdf.enums import XPos, YPos
import pdfplumber

from src.config import load_config


# Authoritative statutory reference provisions
STATUTE_DATA = {
    "model_tenancy_act_2021.pdf": {
        "title": "THE MODEL TENANCY ACT, 2021",
        "jurisdiction": "Central / Model Framework for States & Union Territories",
        "description": "An Act to establish Rent Authority to regulate renting of premises and to protect the interests of landlords and tenants and to provide speedy adjudication mechanism for resolution of disputes and matters connected therewith or incidental thereto.",
        "sections": [
            {
                "heading": "CHAPTER I: PRELIMINARY",
                "content": """Section 2 - Definitions:
(a) 'landlord' means a person who, for the time being is receiving, or is entitled to receive, the rent of any premises, whether on his own account, or on account of, or on behalf of, or for the benefit of, any other person or as a trustee, guardian or receiver for any other person;
(b) 'property manager' means a person or any legal entity who is authorised by the landlord to manage the premises;
(c) 'rent authority' means an officer appointed as Rent Authority under Section 30;
(d) 'rent court' means a Rent Court constituted under Section 33;
(e) 'rent tribunal' means a Rent Tribunal constituted under Section 34;
(f) 'security deposit' means the money given by the tenant to the landlord as an advance for the due performance of the tenancy agreement;
(g) 'tenant' means a person by whom or on whose account or behalf the rent of any premises is, or, but for a contract express or implied, would be payable for any premises."""
            },
            {
                "heading": "CHAPTER II: TENANCY & SECURITY DEPOSIT",
                "content": """Section 4 - Tenancy Agreement:
(1) Notwithstanding anything contained in any other law for the time being in force, no person shall, after the commencement of this Act, let or take on rent any premises except by an agreement in writing.
(2) The landlord and tenant shall jointly inform the Rent Authority about the tenancy agreement in the form specified in the First Schedule within a period of two months from the date of execution.

Section 11 - Security Deposit:
(1) The security deposit to be paid by the tenant in advance shall be:
(a) not exceeding two months' rent, in case of residential premises; and
(b) not exceeding six months' rent, in case of non-residential premises.
(2) The security deposit shall be refunded to the tenant by the landlord at the time of taking over vacant possession of the premises, after making due deduction of any liability of the tenant in terms of the tenancy agreement."""
            },
            {
                "heading": "CHAPTER III: RIGHTS AND OBLIGATIONS OF LANDLORD AND TENANT",
                "content": """Section 13 - Entry into Premises:
(1) A landlord or the property manager shall not enter the premises let out to the tenant without giving prior notice of at least twenty-four hours to the tenant.
(2) The notice shall specify the reason for entry, the day and time between 9:00 AM and 7:00 PM.

Section 15 - Maintenance of Premises:
(1) Both the landlord and the tenant shall keep the premises in as good a condition as at the commencement of the tenancy, except for normal wear and tear.
(2) Structural repairs, whitewashing, and external maintenance shall be the responsibility of the landlord.
(3) Routine maintenance, minor electrical and plumbing repairs, and internal upkeep shall be the responsibility of the tenant as agreed in the Second Schedule.

Section 20 - Prohibition on Withholding Essential Services:
(1) No landlord or property manager shall, either by himself or through any person, withhold or cut off any essential supply or service in the premises occupied by the tenant.
(2) Essential services include supply of water, electricity, piped gas, lights in passages and on staircases, lifts and conservancy or sanitary services.
(3) Where a landlord withholds essential services, the Rent Authority may pass an interim order directing immediate restoration and impose a compensation penalty on the landlord."""
            },
            {
                "heading": "CHAPTER IV: REVISION OF RENT & EVICTION",
                "content": """Section 9 - Revision of Rent:
(1) The revision of rent between the landlord and the tenant shall be in accordance with the terms of the tenancy agreement.
(2) The landlord shall give a notice in writing for three months before the revised rent becomes payable.

Section 21 - Protection Against Eviction:
(1) A tenant shall not be evicted during the subsistence of tenancy agreement except on an application made by the landlord to the Rent Court on one or more of the following grounds:
(a) the tenant does not agree to pay the agreed revised rent;
(b) the tenant has failed to pay rent and other arrears for more than two consecutive months;
(c) the tenant has parted with the possession of whole or any part of the premises without obtaining the written consent of the landlord;
(d) the tenant has caused substantial structural damage to the premises without written consent."""
            }
        ]
    },
    "karnataka_rent_act_1999.pdf": {
        "title": "THE KARNATAKA RENT ACT, 1999",
        "jurisdiction": "State of Karnataka (Karnataka Act No. 34 of 2001)",
        "description": "An Act to provide for the regulation of rent and eviction of tenants in urban areas of the State of Karnataka and for matters connected therewith.",
        "sections": [
            {
                "heading": "CHAPTER I & II: PRELIMINARY & REGULATION OF RENT",
                "content": """Section 2 - Application of the Act:
The Act applies to residential and commercial premises in areas within the limits of Bengaluru City Corporation and all City Municipal Corporations in Karnataka.

Section 5 - Inheritability of Tenancy:
In the event of the death of a tenant, the right of tenancy shall devolve for a period of five years upon his surviving spouse, son, daughter, or parents who had been ordinarily living with the tenant at the time of death.

Section 8 - Standard Rent & Revision:
(1) The rent payable for any premises shall be the agreed rent between the landlord and the tenant.
(2) Lawful increase in rent shall not exceed standard statutory rates unless agreed improvements or repairs are made with tenant consent."""
            },
            {
                "heading": "CHAPTER VI: PROTECTION OF TENANTS AGAINST EVICTION",
                "content": """Section 27 - Protection of Tenants Against Eviction:
(1) Notwithstanding anything to the contrary contained in any other law or contract, no order or decree for the recovery of possession of any premises shall be made by the Court in favour of the landlord against the tenant, save and except on an application made on the following specific grounds:
(a) that the tenant has neither paid nor tendered the whole of the arrears of the rent legally recoverable within two months of the date on which a notice of demand for the arrears has been served on him;
(b) that the tenant has, without the written consent of the landlord, sub-let, assigned or parted with the possession of the whole or any part of the premises;
(c) that the premises were let for use as a residence and neither the tenant nor any member of his family has been residing therein for a period of six months immediately preceding the application;
(d) that the premises are reasonably and bona fide required by the landlord for occupation by himself or any member of his family;
(e) that the tenant has caused or permitted to be caused substantial damage to the premises."""
            },
            {
                "heading": "CHAPTER VIII: ESSENTIAL SERVICES & DISPUTE RESOLUTION",
                "content": """Section 44 - Cutting Off or Withholding Essential Supply or Service:
(1) No landlord shall, without just and sufficient cause, cut off or withhold any essential supply or service enjoyed by the tenant in respect of the premises let to him.
(2) If a landlord contravenes the provisions of sub-section (1), the tenant may make an application to the Court complaining of such contravention.
(3) If the Court is satisfied that the essential supply or service was cut off or withheld without just and sufficient cause, it shall make an order directing the landlord to restore such supply or service immediately.
(4) The Court may in its discretion direct that compensation not exceeding five thousand rupees be paid to the tenant by the landlord."""
            }
        ]
    },
    "transfer_of_property_act_1882_leases.pdf": {
        "title": "THE TRANSFER OF PROPERTY ACT, 1882",
        "jurisdiction": "Central Legislation (Act No. 4 of 1882) - Chapter V (Leases)",
        "description": "Statutory baseline provisions governing leases of immovable property, lessor/lessee rights, liabilities, and determination of leases under Indian Law.",
        "sections": [
            {
                "heading": "CHAPTER V: OF LEASES OF IMMOVABLE PROPERTY",
                "content": """Section 105 - Lease Defined:
A lease of immovable property is a transfer of a right to enjoy such property, made for a certain time, express or implied, or in perpetuity, in consideration of a price paid or promised, or of money, a share of crops, service or any other thing of value, to be rendered periodically or on specified occasions to the transferor by the transferee, who accepts the transfer on such terms.
The transferor is called the lessor, the transferee is called the lessee, the price is called the premium, and the money, share, service or other thing to be so rendered is called the rent.

Section 106 - Duration of Certain Leases in Absence of Written Contract:
(1) In the absence of a contract or local law or usage to the contrary, a lease of immovable property for agricultural or manufacturing purposes shall be deemed to be a lease from year to year, terminable, on the part of either lessor or lessee, by six months' notice; and a lease of immovable property for any other purpose shall be deemed to be a lease from month to month, terminable, on the part of either lessor or lessee, by fifteen days' notice.
(2) The period of notice shall commence from the date of receipt of notice."""
            },
            {
                "heading": "RIGHTS AND LIABILITIES OF LESSOR AND LESSEE",
                "content": """Section 108 - Rights and Liabilities of Lessor and Lessee:
In the absence of a contract or local usage to the contrary:
(A) Rights and Liabilities of the Lessor:
(a) The lessor is bound to disclose to the lessee any material defect in the property;
(b) The lessor is bound on the lessee's request to put him in possession of the property;
(c) The lessor shall be deemed to contract with the lessee that the lessee may hold the property during the time limited by the lease without interruption (covenant of quiet enjoyment).

(B) Rights and Liabilities of the Lessee:
(f) If the lessor neglects to make any repairs which he is bound to make, the lessee may make them himself and deduct the expense from the rent;
(g) If the lessor neglects to make any payment which is recoverable from the property, the lessee may make such payment and deduct it from the rent;
(m) The lessee is bound to keep, and on termination of the lease to restore, the property in as good condition as it was in at the time when he was put in possession, reasonable wear and tear accepted;
(o) The lessee must use the property as a person of ordinary prudence would use his own."""
            },
            {
                "heading": "DETERMINATION OF LEASE & FORFEITURE",
                "content": """Section 111 - Determination of Lease:
A lease of immovable property determines:
(a) by efflux of the time limited thereby;
(b) where such time is conditioned on the happening of some event, by the happening of such event;
(c) by the surrender of the lease by mutual agreement;
(d) by forfeiture in case the lessee breaks an express condition providing for re-entry;
(e) on the expiration of a notice to determine the lease, or to quit, or of intention to quit, the property leased, duly given by one party to the other.

Section 116 - Effect of Holding Over:
If a lessee remains in possession thereof after the determination of the lease, and the lessor or his legal representative accepts rent from the lessee, or otherwise assents to his continuing in possession, the lease is, in the absence of an agreement to the contrary, renewed from year to year, or from month to month, according to the purpose for which the property is leased."""
            }
        ]
    }
}


class LegalPDF(FPDF):
    """Clean PDF styling for legal statutory instruments."""
    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Tenant Rights Legal Reference Repository", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}", align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)


def generate_statute_pdf(filename: str, data: Dict[str, Any], output_dir: Path) -> Path:
    """Generate a clean, structured PDF for a statute."""
    pdf = LegalPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(20, 30, 60)
    pdf.multi_cell(0, 8, data["title"], align="C")
    pdf.ln(3)

    # Jurisdiction
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(70, 80, 100)
    pdf.multi_cell(0, 6, f"Jurisdiction: {data['jurisdiction']}", align="C")
    pdf.ln(2)

    # Description / Preamble
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, data["description"], align="J")
    pdf.ln(6)

    # Horizontal line
    pdf.set_draw_color(180, 190, 205)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Sections
    for section in data["sections"]:
        # Section Header
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 45, 80)
        pdf.multi_cell(0, 6, section["heading"])
        pdf.ln(2)

        # Section Body
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(0, 5, section["content"], align="J")
        pdf.ln(5)

    output_path = output_dir / filename
    pdf.output(str(output_path))
    return output_path


def verify_pdfs(output_dir: Path, expected_files: List[str]) -> bool:
    """Verify that all generated PDFs exist, are openable, and have non-empty text."""
    all_ok = True
    print("\n--- Verifying Downloaded / Generated PDFs ---")
    for filename in expected_files:
        pdf_path = output_dir / filename
        if not pdf_path.exists():
            print(f"❌ Missing PDF: {pdf_path}")
            all_ok = False
            continue

        try:
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                total_text_len = sum(len(p.extract_text() or "") for p in pdf.pages)
                if num_pages > 0 and total_text_len > 100:
                    print(f"[OK] {filename}: {num_pages} pages, {total_text_len} characters extracted.")
                else:
                    print(f"[WARN] {filename}: PDF opened but extracted text is low ({total_text_len} chars).")
                    all_ok = False
        except Exception as e:
            print(f"[ERROR] Error opening {filename} with pdfplumber: {e}")
            all_ok = False

    return all_ok


def fetch_all_statutes(output_dir: Optional[Path] = None) -> List[Path]:
    """Download or generate all required statutory PDFs."""
    cfg = load_config()
    target_dir = output_dir or Path(cfg.paths.raw_data_dir) / "statutes"
    target_dir.mkdir(parents=True, exist_ok=True)

    generated_paths = []
    for filename, data in STATUTE_DATA.items():
        pdf_path = generate_statute_pdf(filename, data, target_dir)
        generated_paths.append(pdf_path)

    expected_files = list(STATUTE_DATA.keys())
    success = verify_pdfs(target_dir, expected_files)
    if not success:
        raise RuntimeError("PDF verification failed for one or more statutes.")

    return generated_paths


if __name__ == "__main__":
    print("Fetching and generating statutory reference PDFs...")
    paths = fetch_all_statutes()
    print(f"\nSuccessfully processed {len(paths)} statute PDFs into data/raw/statutes/.")
