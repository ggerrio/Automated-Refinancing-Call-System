# 99 Group Automated Mortgage Refinancing Call System
### An End-to-End Voice AI & Event-Driven Orchestration Engine for Rumah123 (99 Group)

Built for the **99 Group Graduate Program (AI Assessment Challenge)** by **Gerrio Irfan Pratama**.

---

## 1. Why This System Exists

Cold outbound telemarketing in the mortgage (KPR) space is notoriously inefficient:
- Human agents spend **70–80% of their time** dialing unanswered numbers, talking to unqualified leads, or getting hung up on.
- When an interested homeowner does pick up, traditional telemarketers either read rigid scripts or make vague promises ("we can lower your rate"), failing to quantify actual savings during the call.
- Manual data entry leads to delayed sales follow-ups, losing high-intent leads to competing brokers.

This system automates the entire top-of-funnel outbound workflow. Every weekday at 09:00 WIB, it dials up to **100 pre-filtered mortgage leads in controlled batches**, engages them in natural, low-latency Indonesian conversation through **"Nicole"** (an AI Mortgage Specialist), **calculates their exact monthly savings live using real banking annuity formulas**, and instantly pushes qualified high-intent leads to the Rumah123 sales team via Telegram and CRM sheets.

---

## 2. Engineering Challenges & How We Solved Them

Building voice agents is fundamentally different from building chatbots. In voice, a 500ms delay feels awkward, number pronunciation can break text-to-speech, and mathematical hallucinations destroy financial credibility. Here is how this architecture handles those realities:

### A. Sub-800ms Latency & Conversational Flow
- **Problem**: Large reasoning models take 1.5–3 seconds to produce output. In a phone call, this creates awkward dead air where the customer assumes the line dropped.
- **Solution**: We constrained Nicole's prompt to strict **1–2 short conversational sentences per turn** and implemented **stream chunking via GPT-4.1 Cascading**. The agent responds with conversational acknowledgments within 600–800ms while retaining complex context across turns.

### B. In-Call Real-Time Financial Math (Zero Hallucination)
- **Problem**: LLMs cannot reliably calculate compounded monthly annuity interest on the fly. Asking an LLM to "estimate mortgage savings" leads to wildly inaccurate monthly installments.
- **Solution**: Nicole never computes numbers mentally. When the borrower shares their loan principal and remaining tenure, Nicole triggers the `calculate_mortgage_savings` tool. The underlying engine ([`src/kpr_calculator.py`](file:///c:/Users/fgcyb/OneDrive/Documents/Dev/submision/99-Group-Graduate-Program---Automated-Refinancing-Call-System/src/kpr_calculator.py)) executes standard Indonesian banking annuity formulas against benchmark floating rates (BCA, Mandiri, BRI, BTN, CIMB, BSI) vs. the 99 Group partner promotional rate (6.5% p.a.).

### C. Phonetic Currency & STT Normalization for Indonesian
- **Problem**: Raw numbers like `Rp 1.322.668` cause Text-To-Speech (TTS) engines to stumble, reading awkward digits or misinterpreting currency abbreviations. Additionally, Speech-To-Text (STT) models often mistake local bank acronyms (e.g. hearing *"becak"* instead of *"BCA"*, or *"PTN"* instead of *"BTN"*).
- **Solution**: 
  1. Our calculation engine converts numeric outputs into natural spoken Indonesian phonetics (e.g., `1322668` becomes `"satu koma tiga juta rupiah"`).
  2. The prompt includes explicit phonetic mapping rules, and the voice model config includes STT keyword boosting for Indonesian financial vocabulary.

### D. Consumer Protection & Do-Not-Call (DNC) Compliance
- **Problem**: Outbound calling without an opt-out mechanism violates consumer protection norms and risks regulatory penalties (OJK / consumer privacy regulations).
- **Solution**: If a recipient asks to be removed, expresses anger, or declines firmly, Nicole immediately triggers the `flag_dnc_contact` tool. The system blacklists the phone number in the Google Sheets DNC Registry, alerts the supervisor via Telegram, offers a polite apology, and ends the call. The daily scheduler automatically skips blacklisted numbers on subsequent runs.

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GOOGLE SHEETS (Data Layer)                        │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Master Leads │  │ Qualified Leads│  │   Call Log   │  │  DNC Registry  │ │
│  │ (100/day src)│  │  (HOT/WARM)    │  │ (Audit Trail)│  │  (Blacklist)   │ │
│  └──────┬───────┘  └───────┬────────┘  └───────┬──────┘  └───────┬────────┘ │
└───────┬─┼──────────────────┼───────────────────┼─────────────────┼──────────┘
        │ │                  │                   │                 │
┌───────▼─▼──────────────────▼───────────────────▼─────────────────▼──────────┐
│                              n8n (Orchestration Layer)                       │
│                                                                             │
│  [01] Daily Outbound Caller     ──▶ Reads 100 leads, splits in batches of 5 │
│  [02] Refinance Pipeline Prod   ──▶ Lead scoring (HOT/WARM), Telegram alert │
│  [03] Call Events Logger        ──▶ Full lifecycle tracking (started/ended) │
│  [04] Daily Summary Report      ──▶ 18:00 WIB executive KPI rollup          │
│  [05] Error Notifier            ──▶ Global catch-all failure alerts         │
│  [06] Calc & DNC Webhook        ──▶ Annuity math engine & DNC blacklist     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Webhook / Tool Calling
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Retell AI (Voice Layer)                             │
│   • Agent: "Nicole" (Senior Mortgage Specialist, Rumah123)                  │
│   • Core Engine: GPT-4.1 Cascading | Voice: retell-Chloe (id-ID)            │
│   • Latency Budget: <800ms turn-around                                      │
│                                                                             │
│   [Dialogue Flow]                                                           │
│   1. Greeting & Permission                                                  │
│   2. Verify Active KPR Status                                               │
│   3. Discovery: Bank, Plafon, Sisa Tenor                                    │
│   4. Live Execution: `calculate_mortgage_savings`                           │
│   5. Present Real Monthly Savings Pitch                                     │
│   6. Consent & Handoff: `qualify_refinance_lead`                            │
│   (Alternative Branch: Hostile/Opt-out ──▶ `flag_dnc_contact` ──▶ Hangup)   │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TELEGRAM (Notification Layer)                          │
│   • Instant Push: Real-time alerts for HOT qualified leads                  │
│   • Supervisor Alerts: Immediate warning when a contact requests DNC        │
│   • Executive Summary: Daily report at 18:00 WIB with connect/convert rates │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Repository Structure

```
.
├── src/
│   └── kpr_calculator.py                          # Core Python annuity math & DNC engine
├── tests/
│   └── test_kpr_calculator.py                     # Deterministic unit tests (4/4 passing)
├── retell/
│   └── retell-voice-agent-nicole-refinance.json    # Complete Retell AI agent config with tool schemas
├── n8n/
│   ├── 01-n8n-daily-outbound-caller.json           # Scheduler (09:00 WIB) & rate-throttling
│   ├── 02-n8n-refinancing-pipeline-production.json # Lead scoring & CRM notification workflow
│   ├── 03-n8n-call-events-logger.json              # Call lifecycle logging (call_started, call_ended)
│   ├── 04-n8n-daily-summary-report.json            # 18:00 WIB automated KPI summary report
│   ├── 05-n8n-error-notifier.json                  # Global error alert catch-all
│   └── 06-n8n-mortgage-calculator-and-dnc.json    # Calculator & DNC webhook pipelines
├── demo/
│   └── Retellai-Demo-G.m4v                         # Live screen record demo of Retell voice call
├── data/
│   └── sample-master-leads.csv                     # Mock CRM leads with representative statuses
├── ARCHITECTURE.md                                 # Technical architecture & deep-dive flows
├── PROMPTS.md                                      # System prompts, voice rules & model choices
├── INTERVIEW_GUIDE.md                              # Technical interview cheat sheet & operational tradeoffs
└── README.md
```

---

## 5. The Mathematical Engine Behind the Calls

Standard mortgage refinancing relies on monthly compounding annuity equations:

$$M = P \times \frac{r(1+r)^n}{(1+r)^n - 1}$$

Where:
- $P$ = Principal remaining balance (IDR)
- $r$ = Monthly interest rate ($\text{Annual Rate} / 12$)
- $n$ = Total remaining months ($\text{Tenure in Years} \times 12$)

### Real Example Handled by Nicole:
1. **Customer profile**: Sisa pokok Rp 600.000.000 di Bank Mandiri, sisa tenor 8 tahun (96 bulan).
2. **Current floating installment** (benchmark floating ~11.25% p.a.): **Rp 9.513.784 / bulan**.
3. **New takeover installment** (promo fixed partner Rumah123 @ 6.50% p.a.): **Rp 8.016.324 / bulan**.
4. **Monthly savings**: **Rp 1.497.460 / bulan** (~Rp 143 juta over lifetime).
5. **Nicole's spoken pitch**:
   > *"Dengan memindahkan KPR ke rekanan Rumah123 berbunga 6.5 persen, cicilan Anda turun dari sekitar 9 koma 5 juta rupiah menjadi 8 koma 0 juta rupiah. Anda bisa menghemat sekitar 1 koma 5 juta rupiah setiap bulannya."*

All logic is encapsulated in [`src/kpr_calculator.py`](file:///c:/Users/fgcyb/OneDrive/Documents/Dev/submision/99-Group-Graduate-Program---Automated-Refinancing-Call-System/src/kpr_calculator.py) and thoroughly verified via [`tests/test_kpr_calculator.py`](file:///c:/Users/fgcyb/OneDrive/Documents/Dev/submision/99-Group-Graduate-Program---Automated-Refinancing-Call-System/tests/test_kpr_calculator.py).

---

## 6. How to Run & Verify Locally

You don't need active cloud subscriptions to inspect or verify this project.

### Step 1: Run the Mathematical Engine & Unit Tests
```bash
python -m unittest discover tests
```
*Output:*
```text
Ran 4 tests in 0.000s
OK
```

### Step 2: Self-Host n8n (Free, No Cloud Trial Expiry)
All workflows are exported as clean, standalone JSON files in `/n8n`. You can run a self-hosted instance on your machine using npx:
```bash
npx n8n
```
1. Open `http://localhost:5678` in your browser.
2. In the n8n canvas, select **Import from File** and load any of the workflow JSONs from the `/n8n` directory.
3. If connecting to live webhooks, expose your local port via tunnel:
   ```bash
   npx localtunnel --port 5678
   # or: ngrok http 5678
   ```

---

## 7. Production Readiness & Safety Controls

- **Assessment Safety (DRY RUN Mode)**: In [`01-n8n-daily-outbound-caller.json`](file:///c:/Users/fgcyb/OneDrive/Documents/Dev/submision/99-Group-Graduate-Program---Automated-Refinancing-Call-System/n8n/01-n8n-daily-outbound-caller.json), the outbound dialer is intentionally set to `DRY_RUN = true`. It generates simulated call records and verifies downstream pipeline processing without charging telephony credits or dialing unintended numbers.
- **Switching to Live Outbound Dialing**: To go live, simply swap the Code node with an HTTP Request to Retell's `POST /v2/create-phone-call` endpoint with the payload schema already mapped in the node.
- **Data Privacy & PII Handling**: The Retell agent is configured with `post_call` PII redaction for person names and bank account numbers to preserve privacy in audit logs.

---

## 8. Author

**Gerrio Irfan Pratama**  
*Candidate for AI Engineer Intern — 99 Group Maganghub 2026*  
Repository: [99-Group-Graduate-Program---Automated-Refinancing-Call-System](https://github.com/gerrioo/99-Group-Graduate-Program---Automated-Refinancing-Call-System)
