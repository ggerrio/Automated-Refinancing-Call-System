# 99Group Automated Refinancing Call System

An end-to-end automated voice outreach system that calls 100 mortgage (KPR) leads per day to offer refinancing ("Takeover KPR") with lower interest rates. Built with **Retell AI** for voice conversations and **n8n** for workflow orchestration, lead scoring, and reporting.

---

## What It Does

1. **Every weekday at 09:00 WIB**, the system reads a Google Sheets "Master Leads" list.
2. It filters leads marked **"Belum Ditelepon"** (Not Yet Called), limits to **100 per day**, and processes them in **batches of 5**.
3. Each lead receives an **outbound voice call** from "Nicole" — a Senior Mortgage Specialist AI agent from Rumah123 (99 Group Indonesia).
4. Nicole conducts a **natural Indonesian conversation** to qualify the lead:
   - Do you have an active KPR (mortgage)?
   - Which bank and how many years into the tenure?
   - Are you feeling the burden of rising interest rates?
   - Would you like a free simulation of how much you could save?
5. If the customer agrees, the call data is sent via webhook to **n8n** for:
   - **Lead Scoring** (HOT / WARM / COLD)
   - **Telegram notification** to the sales team
   - **Google Sheets logging** ("Qualified Leads" sheet)
6. **Every weekday at 18:00 WIB**, a daily summary report is auto-generated and sent to Telegram with connect rates, conversion rates, and lead breakdowns.
7. **All call lifecycle events** (started, ended, analyzed) are logged to a separate "Call Log" sheet for audit and analytics.
8. **Any workflow failure** triggers an instant Telegram alert to admins.

---

## Repository Structure

```
/
├── retell/
│   └── retell-voice-agent-nicole-refinance.json    # Retell AI voice agent config
├── n8n/
│   ├── 01-n8n-daily-outbound-caller.json           # Scheduler + lead batching
│   ├── 02-n8n-refinancing-pipeline-production.json # Lead scoring + notifications
│   ├── 03-n8n-call-events-logger.json              # Call lifecycle logging
│   ├── 04-n8n-daily-summary-report.json            # Daily KPI reporting
│   └── 05-n8n-error-notifier.json                  # Global error alerting
├── data/
│   └── sample-master-leads.csv                     # Sample lead data (8 records)
├── README.md
├── PROMPTS.md                                      # All AI prompts & model choices
└── ARCHITECTURE.md                                 # System architecture & data flow
```

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Voice AI | Retell AI | Outbound calls, natural conversation in Indonesian |
| Workflow Orchestration | n8n | Scheduling, data processing, integrations |
| Data Storage | Google Sheets | Master leads, qualified leads, call logs |
| Notifications | Telegram Bot | Real-time alerts & daily reports |
| Error Handling | n8n Error Trigger | Centralized failure alerting |

---

## Assessment Notes

- **Outbound caller is in DRY RUN mode** for assessment safety (no real API calls to Retell, no real phone numbers dialed). All downstream pipelines (scoring, logging, reporting) are fully functional and verified against simulated data.
- **Retell signature verification is disabled** in the n8n webhooks for assessment compatibility. This is clearly commented in the code and must be re-enabled before production.
- To go live, swap the "DRY RUN Caller" node with an HTTP Request to `POST /v2/create-phone-call` on the Retell API. All dynamic variables (`customer_name`, `lead_id`, `phone_number`) are already structured and ready.

---

## Author

Built for 99 Group / Rumah123 Refinancing Assessment.
