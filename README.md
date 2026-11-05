# 99 Group Automated Refinancing Call System

An end-to-end automated voice outreach and intelligence system that contacts 100 mortgage (KPR) leads per day to offer refinancing ("Takeover KPR") with lower interest rates. Engineered with **Retell AI** (Voice Layer & Tool Calling), **n8n** (Event Orchestration & Webhooks), **Python Financial Logic** (Annuity Calculation Engine), and **Telegram / Google Sheets** (Real-time CRM & Notification Layer).

---

## What Sets This Apart (Engineering Highlights)

1. **In-Call Real-Time Mortgage Savings Calculator**: Rather than generic pitch scripts, the AI agent calls `calculate_mortgage_savings` live during the phone call. It computes exact monthly annuity savings comparing current bank floating rates (BCA, Mandiri, BRI, BTN, CIMB, BSI) against 99 Group partner rates (6.5% p.a.) and translates output into speech-friendly Indonesian words.
2. **Do-Not-Call (DNC) Compliance Engine**: Detects customer opt-out or hostility intents ("hapus nomor saya", "jangan telepon lagi"), calls `flag_dnc_contact`, auto-blacklists the number, and notifies supervisors via Telegram to comply with consumer protection regulations.
3. **Sub-800ms Latency & Barge-In Optimization**: Prompts are constrained to 1–2 short conversational sentences per turn with custom phonetic normalizations for Indonesian bank acronyms (e.g., STT hearing "becak" -> mapped to "BCA", "PTN" -> mapped to "BTN").
4. **Deterministic Testing**: Includes Python unit tests (`tests/test_kpr_calculator.py`) verifying mathematical precision of annuity formulas and natural speech formatting.

---

## Repository Structure

```
/
├── src/
│   └── kpr_calculator.py                          # Core Python mortgage annuity & DNC engine
├── tests/
│   └── test_kpr_calculator.py                     # Deterministic unit tests (4/4 passing)
├── retell/
│   └── retell-voice-agent-nicole-refinance.json    # Retell AI agent config with tool calling schemas
├── n8n/
│   ├── 01-n8n-daily-outbound-caller.json           # Scheduler + lead batching (100 leads/day)
│   ├── 02-n8n-refinancing-pipeline-production.json # Lead scoring + instant Telegram alerts
│   ├── 03-n8n-call-events-logger.json              # Call lifecycle audit logging
│   ├── 04-n8n-daily-summary-report.json            # 18:00 WIB daily KPI summary report
│   ├── 05-n8n-error-notifier.json                  # Global failure alerting
│   └── 06-n8n-mortgage-calculator-and-dnc.json    # Live annuity calculator & DNC webhooks
├── data/
│   └── sample-master-leads.csv                     # Sample lead data (8 records)
├── README.md
├── PROMPTS.md                                      # AI prompts, model choices & latency rules
└── ARCHITECTURE.md                                 # Full system architecture & data flow
```

---

## Tech Stack

| Layer | Tool / Tech | Purpose |
|---|---|---|
| **Voice AI Agent** | Retell AI (`GPT-4.1 Cascading` + `retell-Chloe`) | Sub-800ms conversational turn-taking, tool calling, Indonesian voice synthesis |
| **Calculation Engine** | Python / n8n Code Node | Standard banking annuity formulas & speech-friendly numeric converter |
| **Workflow Orchestration** | n8n (Webhooks & Schedulers) | Batch caller scheduling, lead scoring, CRM sync, DNC blacklisting |
| **Data Storage** | Google Sheets | Master Leads, Qualified Leads, Call Event Logs, DNC Registry |
| **Notifications** | Telegram Bot API | Instant HOT lead alerts, supervisor DNC alerts, and daily KPI summaries |
| **Test Suite** | Python `unittest` | Regression & accuracy tests for financial formulas |

---

## Quick Start & Verification

### Running the Python Engine & Tests
```bash
python -m unittest discover tests
```

### Self-Hosting n8n (No Cloud Account Required)
To import and test all 6 n8n workflows locally without paying for n8n cloud:
```bash
npx n8n
```
Workflows can be imported directly from the `/n8n` directory via the n8n UI canvas.

---

## Assessment Notes

- **Outbound caller is set to DRY RUN mode** for assessment safety (no real phone numbers dialed unexpectedly). All downstream pipelines (scoring, calculation, DNC flagging, logging, reporting) are verified and production-ready.
- To execute live calls, toggle the DRY RUN mode to Retell API `POST /v2/create-phone-call`.

---

## Author

Gerrio Irfan Pratama | 99 Group Graduate Program 2026
