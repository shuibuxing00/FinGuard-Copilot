# AML Rules — Examples & Analyst Frontend Display

## Rules Table

| Rule Name | Condition | Action on Trigger |
|-----------|-----------|-------------------|
| **High-Frequency Burst** | `time_velocity >= 3` AND `amount > 500` | Increase `risk_score` by 25; set `anomaly_type` = `short_time_high_freq`; alert review |
| **New Device High Value** | `device_new = true` AND `amount >= 3000` | Set `anomaly_type` = `new_device`; increase `risk_score` (+30 cap 100); alert review |
| **Location Mismatch** | `location_consistency = 0` | Set `anomaly_type` = `location_mismatch`; increase `risk_score` by 20; flag geo review |
| **Amount Peak Outlier** | `amount > user_p95_baseline * 5` | Set `anomaly_type` = `amount_peak`; increase `risk_score` by 15; enhanced due diligence |
| **Compound Risk Escalation** | `time_velocity >= 3` AND `location_consistency = 0` | Force `risk_score >= 80`; merge explanations; immediate auditor alert |

## How to Display for Analyst Role

1. **Placement** — Collapsible “Active Rules” card above the transaction table; expanded by default during onboarding.
2. **Visible columns** — Rule Name, Condition (plain English), Action. Hide rule IDs and backend SQL.
3. **Visual cues**
   - Velocity rules → amber badge
   - Location rules → red pin icon
   - Device rules → blue device icon
4. **Interaction** — Hovering a rule row highlights matching transactions (outline + scroll into view).
5. **Permissions** — Analyst: read-only. Auditor: view + acknowledge. Admin: edit rules (separate screen).

JSON source: `frontend/mock/aml-rules.json`
