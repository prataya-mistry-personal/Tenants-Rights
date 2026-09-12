# Data Sources Checklist (MVP Scope)

This document defines the curated, lightweight legal starter dataset for the **Tenant Rights RAG** MVP. The scope is deliberately constrained to prove retrieval accuracy and factual grounding without overburdening local storage or processing time.

Target collection timeframe: **1–2 hours**  
Target volume: **3 statutory instruments + ~20–30 landmark/relevant tenant dispute judgments**

---

## 1. Statutory Acts & Provisions (Legislation)

| Source Name | Jurisdiction / Level | Relevance to Tenant Disputes | Format / Target Sections |
| :--- | :--- | :--- | :--- |
| **Model Tenancy Act, 2021 (MTA)** | Central / Benchmark Guidance | Security deposits caps (max 2 months for residential), eviction procedure, maintenance responsibilities, notice periods (24h entry notice). | Full Act PDF / Cleaned text (~30-40 pages, 47 sections) |
| **Karnataka Rent Act, 1999** | State (Bengaluru Focus) | Grounds for eviction (Section 27), standard rent provisions, jurisdiction of Rent Court/Tribunal, protection against unlawful utility disconnection (Section 44). | Full Act PDF / Plain text (~50 sections) |
| **Delhi Rent Control Act, 1958** *(Secondary)* | State (Delhi NCR Focus) | Rent revision rules, protection against unlawful eviction (Section 14), landlord repairs obligations. | Selected key sections (Sections 14, 15, 45) |
| **Transfer of Property Act, 1882 (TPA)** | Central / Baseline Tenancy | Sections 105–116 (Lease definition, rights and liabilities of lessor/lessee, determination of lease, waiver of notice to quit). | Specific Sections 105 to 116 |

---

## 2. Case Law & Precedents (Indian Kanoon)

Source: [Indian Kanoon](https://indiankanoon.org)  
Domain: High Court of Karnataka, Delhi High Court, and Supreme Court of India judgments strictly covering landlord-tenant rental disputes.

### Search Query Filters & Targeted Disputes

| Dispute Category | Target Sub-topics | Target Judgments |
| :--- | :--- | :--- |
| **Security Deposit Retention** | Landlord refusing refund of deposit upon vacating, illegal deductions for wear-and-tear. | 5–8 judgments |
| **Illegal Eviction & Coercion** | Forceful eviction without court order, locking premises, harassment, self-help eviction. | 8–10 judgments |
| **Utility Disconnections** | Landlord cutting off electricity, water supply, or elevator access to force eviction. | 5–6 judgments |
| **Notice Period & Rent Escalation** | Unreasonable mid-lease rent hike, eviction without mandatory notice under lease agreement / TPA. | 5–6 judgments |

**Total Case Law Target:** ~25–30 high-relevance judgments.

---

## 3. Raw Data Storage Layout

```
data/raw/
├── statutes/
│   ├── model_tenancy_act_2021.txt
│   ├── karnataka_rent_act_1999.txt
│   ├── delhi_rent_control_act_1958_selected.txt
│   └── tpa_1882_sections_105_116.txt
└── cases/
    ├── security_deposit/
    ├── illegal_eviction/
    ├── utility_disconnection/
    └── notice_and_rent_hike/
```

---

## 4. Collection Feasibility & Next Actions

1. **Format**: Plain text / Markdown with standardized header metadata (`title`, `citation`, `court`, `year`, `jurisdiction`, `source_url`, `dispute_type`).
2. **Scraping / Ingestion**: Use standard Python `requests` + `beautifulsoup4` or curated markdown files to place in `data/raw/`.
3. **No Heavy Scraping**: Avoid scraping thousands of pages; maintain high signal-to-noise ratio for precise retrieval evaluation.
