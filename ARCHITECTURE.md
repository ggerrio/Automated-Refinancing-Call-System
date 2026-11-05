# System Architecture & Data Flow

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GOOGLE SHEETS (Data Layer)                        │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Master Leads │  │ Qualified Leads│  │   Call Log   │  │  DNC Registry  │ │
│  │ (100/day src)│  │  (HOT/WARM)    │  │ (Lifecycle)  │  │  (Blacklist)   │ │
│  └──────┬───────┘  └───────┬────────┘  └───────┬──────┘  └───────┬────────┘ │
└───────┬─┼──────────────────┼───────────────────┼─────────────────┼──────────┘
        │ │                  │                   │                 │
┌───────▼─▼──────────────────▼───────────────────▼─────────────────▼──────────┐
│                              n8n (Orchestration Layer)                       │
│                                                                             │
│   ┌─────────────────────┐    ┌─────────────────────┐    ┌──────────────┐   │
│   │ 01 Daily Outbound   │───▶│ 02 Pipeline         │    │ 03 Events    │   │
│   │    Caller (09:00)   │    │    Production       │    │    Logger    │   │
│   │  • Read 100 leads   │    │  • Lead Scoring     │    │  • call_ended│   │
│   │  • Batch of 5       │    │  • Telegram alert   │    │  • Duration  │   │
│   └─────────────────────┘    └─────────────────────┘    └──────────────┘   │
│                                                                             │
│   ┌─────────────────────┐    ┌─────────────────────┐    ┌──────────────┐   │
│   │ 04 Daily Summary    │    │ 05 Error Notifier   │    │ 06 Calc & DNC│   │
│   │    Report (18:00)   │    │  (Global Safety Net)│    │   Webhook    │   │
│   │  • Connect rate     │    │  • Telegram alert   │    │  • Annuity   │   │
│   │  • Conversion rate  │    │  • Workflow trace   │    │  • Blacklist │   │
│   └─────────────────────┘    └─────────────────────┘    └──────────────┘   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Webhooks & Tool Calls
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Retell AI (Voice Layer)                             │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │              "Nicole" — Senior Mortgage Specialist                │     │
│   │   • Engine: GPT-4.1 Cascading | Voice: retell-Chloe (id-ID)     │     │
│   │   • Latency Optimization: <800ms response time                  │     │
│   │                                                                 │     │
│   │   1. Greeting ──▶ 2. Qualify Active KPR ──▶ 3. Discovery Plafon │     │
│   │        │                                           │            │     │
│   │        ▼ (Opt-out / DNC intent)                    ▼            │     │
│   │   Tool: flag_dnc_contact               Tool: calculate_savings  │     │
│   │        │                                           │            │     │
│   │        ▼                                           ▼            │     │
│   │   Blacklist & End Call                 Speak Real Savings Pitch │     │
│   │                                                    │            │     │
│   │                                                    ▼            │     │
│   │                                        Tool: qualify_lead       │     │
│   └─────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ Telegram Bot API
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TELEGRAM (Notification Layer)                          │
│                                                                             │
│   • Real-time HOT lead alerts (instant push to sales team)                  │
│   • Instant DNC compliance alerts (supervisor notification)                 │
│   • Daily 18:00 WIB executive KPI summary                                   │
│   • Instant system exception alerts                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Call Lifecycle & Tool Calling

### 1. In-Call Mortgage Savings Tool Call
When the customer mentions their remaining tenure and loan principal, Nicole triggers `calculate_mortgage_savings`:
```json
// Request from Retell to n8n Webhook / Python engine:
{
  "current_bank": "BCA",
  "remaining_tenure_years": 8,
  "loan_amount_idr": 600000000,
  "current_interest_rate": 10.75
}

// Response returned to Voice Agent:
{
  "status": "success",
  "current_monthly_installment": 9385641,
  "new_monthly_installment": 8062973,
  "monthly_savings": 1322668,
  "spoken_pitch": "Dengan memindahkan KPR ke rekanan Rumah123 berbunga 6.5 persen, cicilan Anda turun dari sekitar 9 koma 4 juta rupiah menjadi 8 koma 1 juta rupiah. Anda bisa menghemat sekitar 1 koma 3 juta rupiah setiap bulannya."
}
```

### 2. DNC Compliance Tool Call
If customer expresses hostility or requests removal:
```json
// Request:
{
  "phone_number": "6281318913092",
  "reason": "Customer shouted not interested and asked to delete number"
}

// Action:
// 1. Appends record to DNC Registry sheet.
// 2. Flags contact in Master Leads so scheduler ignores them in future batches.
// 3. Alerts supervisor in Telegram.
// 4. Returns polite apology and immediately hangs up.
```
