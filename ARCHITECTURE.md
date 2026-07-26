# System Architecture & Data Flow

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GOOGLE SHEETS (Data Layer)                        │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────┐                   │
│  │ Master Leads │  │ Qualified Leads│  │   Call Log     │                   │
│  │  (Source)    │  │  (Hot/Warm)    │  │ (All Events)   │                   │
│  └──────┬───────┘  └───────┬────────┘  └───────┬────────┘                   │
└───────┬─┼──────────────────┼───────────────────┼──────────────────────────┘
        │ │                  │                   │
        │ │                  │                   │
┌───────▼─▼──────────────────▼───────────────────▼──────────────────────────┐
│                              n8n (Orchestration Layer)                       │
│                                                                             │
│   ┌─────────────────────┐    ┌─────────────────────┐    ┌──────────────┐   │
│   │ 01 Daily Outbound   │───▶│ 02 Pipeline         │    │ 03 Events    │   │
│   │    Caller (09:00)   │    │    Production       │    │    Logger    │   │
│   │  • Read 100 leads   │    │  • Lead Scoring     │    │  • call_ended│   │
│   │  • Batch of 5       │    │  • Telegram alert   │    │  • call_started│  │
│   │  • DRY RUN (assess) │    │  • Sheets append    │    │  • Duration  │   │
│   └─────────────────────┘    └─────────────────────┘    └──────────────┘   │
│                                                                             │
│   ┌─────────────────────┐    ┌─────────────────────┐                       │
│   │ 04 Daily Summary    │    │ 05 Error Notifier   │                       │
│   │    Report (18:00)   │    │  (Global Safety Net)│                       │
│   │  • Connect rate     │    │  • Telegram alert   │                       │
│   │  • Conversion rate  │    │  • Workflow name    │                       │
│   │  • Hot/Warm/Cold    │    │  • Error message    │                       │
│   └─────────────────────┘    └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        │ HTTP Request
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Retell AI (Voice Layer)                             │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │              "Nicole" — Senior Mortgage Specialist                │     │
│   │                                                                 │     │
│   │   1. Greeting ──▶ 2. Ask Name ──▶ 3. Qualify KPR               │     │
│   │        │                │                │                      │     │
│   │        ▼                ▼                ▼                      │     │
│   │   4. Ask Bank &    5. Pitch Takeover   6. Check Consent        │     │
│   │      Tenure              │                │                      │     │
│   │        │                 │                │                      │     │
│   │        ▼                 ▼                ▼                      │     │
│   │   7. Extract Data  8. Trigger Webhook  9. Confirm & End        │     │
│   │                                                                 │     │
│   │   Dynamic Variables: customer_name, lead_id, phone_number      │     │
│   │   Tool: qualify_refinance_lead ──▶ n8n Pipeline                 │     │
│   └─────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        │ Webhook
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TELEGRAM (Notification Layer)                          │
│                                                                             │
│   • Real-time HOT lead alerts (instant upon qualification)                  │
│   • Daily summary report (18:00 WIB)                                        │
│   • Error alerts (immediate upon any workflow failure)                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Flow: One Lead's Journey

### Step 1: Morning Batch (09:00 WIB)
- **Trigger**: n8n Schedule Trigger fires every weekday at 09:00.
- **Action**: Read "Master Leads" sheet.
- **Filter**: Only rows where `Status` = "Belum Ditelepon" (or blank).
- **Limit**: Cap at 100 leads.
- **Batch**: Split into batches of 5 for throttling.

### Step 2: Outbound Call Initiation
- **Action**: Each batch item is processed through the caller node.
- **Assessment Mode**: DRY RUN simulates the call by generating a fake `call_id` and logging the intent.
- **Production Mode**: HTTP Request to Retell API `POST /v2/create-phone-call` with payload:
  ```json
  {
    "agent_id": "<agent-id>",
    "to_number": "6281318913092",
    "retell_llm_dynamic_variables": {
      "customer_name": "Gerrio",
      "lead_id": "LEAD-001",
      "phone_number": "6281318913092"
    }
  }
  ```

### Step 3: Voice Conversation (Retell Agent)
Nicole executes the conversation flow:

| Step | Node | What Happens | Data Captured |
|---|---|---|---|
| 1 | Greeting | "Halo, selamat sore Bapak Gerrio..." | — |
| 2 | Check Interest | "Apakah ada waktu 1 menit?" | Engagement signal |
| 3 | Ask Name (if needed) | "Boleh saya tahu ini dengan Bapak siapa?" | `customer_name_captured` |
| 4 | Qualify KPR | "Apakah sedang memiliki cicilan KPR aktif?" | `has_existing_kpr` |
| 5 | Ask Bank & Tenure | "Bank apa dan sudah berapa tahun?" | `current_bank`, `kpr_tenure_years` |
| 6 | Pitch Takeover | "Potong bunga 2-3%, hemat jutaan per bulan..." | — |
| 7 | Check Consent | "Berminat dihitungkan simulasinya?" | `interest_in_takeover` |
| 8 | Trigger Webhook | Call `qualify_refinance_lead` | All params sent to n8n |
| 9 | Confirmation | "Tim Spesialis akan menghubungi via WhatsApp." | — |
| 10 | End Call | Polite closure | — |

### Step 4: Lead Processing (n8n Pipeline)
Webhook received at `/webhook/refinance-webhook`:

1. **Signature Check** (disabled for assessment → enabled for production).
2. **Normalization**: Parse payload, handle `args_at_root` structure from Retell.
3. **Lead Scoring**:
   ```
   hasKpr=true + interested=true   → HOT_LEAD   → Route to Specialist
   hasKpr=true + interested=false  → WARM_LEAD  → Send Edu WA
   hasKpr=false                    → COLD_LEAD  → Log only
   ```
4. **Fast Response**: Return HTTP 200 to Retell to prevent timeout.
5. **Filter**: Only non-COLD leads proceed.
6. **Telegram Alert**: Send formatted HTML message to group.
7. **Sheets Append**: Write to "Qualified Leads" sheet.

### Step 5: Lifecycle Logging (Parallel)
Simultaneously, Retell sends call events to `/webhook/refinance-call-events`:
- `call_started` → acknowledged but not logged (to avoid duplication).
- `call_ended` → logged to "Call Log" sheet with duration, status, disconnection reason.
- `call_analyzed` → reserved for future sentiment analysis.

### Step 6: End-of-Day Reporting (18:00 WIB)
- **Read**: "Call Log" + "Qualified Leads" sheets.
- **Compute**: Total called, connected, no-answer, connect rate, hot/warm/cold breakdown, conversion rate.
- **Send**: Formatted summary to Telegram.

### Step 7: Error Handling (Anytime)
- If any workflow fails → Error Notifier triggers → Telegram alert with workflow name, failed node, error message, timestamp.

---

## Data Model

### Master Leads (Input)
| Column | Type | Description |
|---|---|---|
| Lead ID | String | Unique identifier |
| Nama | String | Customer name |
| No HP | String | Phone number (62 format) |
| Status | String | "Belum Ditelepon" / "Sudah Ditelepon" |
| Last Called At | ISO Timestamp | Last attempt |
| Call ID | String | Retell call ID |

### Qualified Leads (Output)
| Column | Type | Description |
|---|---|---|
| Lead ID | String | From Master Leads |
| Phone Number | String | From Master Leads |
| Customer Name | String | From voice capture |
| Has Active KPR | Boolean | From qualification |
| Current Bank | String | e.g., BCA, Mandiri |
| Tenure Years | Number | Years into mortgage |
| Interested Takeover | Boolean | Consent flag |
| Lead Score | String | HOT LEAD / WARM LEAD / COLD LEAD |
| Next Action | String | Human-readable action |
| Processed At | ISO Timestamp | When scored |

### Call Log (Audit)
| Column | Type | Description |
|---|---|---|
| Call ID | String | Retell unique call ID |
| Lead ID | String | Linked to Master Leads |
| Phone Number | String | Dialed number |
| Call Status | String | ended / completed / busy / no_answer |
| Disconnection Reason | String | Why the call ended |
| Duration (s) | Number | Call length in seconds |
| Started At | ISO Timestamp | Call start |
| Ended At | ISO Timestamp | Call end |

---

## Key Design Decisions

1. **Google Sheets over Database**: Chosen for rapid prototyping and easy stakeholder access. In production, this would migrate to PostgreSQL or a CRM.

2. **Separate Webhooks**: `refinance-webhook` (tool/function calls) and `refinance-call-events` (lifecycle) are separated to isolate concerns and prevent one failure from blocking the other.

3. **Batch Processing**: Batch of 5 prevents rate limiting and gives the system breathing room between calls.

4. **DRY RUN Mode**: Encapsulates the outbound caller in a swappable module. The rest of the system (scoring, logging, reporting) is fully operational and tested against simulated data.

5. **Cascading Model**: GPT-4.1 with fallback ensures voice conversations don't fail silently if the primary model is unavailable.
