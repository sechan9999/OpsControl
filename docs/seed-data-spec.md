# OpsControl Seed Data Specification

## Purpose

This contract defines the deterministic MVP demonstration fixture. It enables repeatable product demos, regression tests, and visual QA without production credentials.

## File

Future fixture path: `data/savannah_storm.jsonl`

Each non-empty line is one JSON object:

```json
{
  "id": "seed-001",
  "channel": "edi",
  "raw": "STATUS: CNTR MSKU7401229 SHPMT OPS-40021-A HELD PORT OF SAVANNAH REASON WX SEVERE RAIN EST DELAY 14HRS"
}
```

Required fields: `id`, `channel`, and `raw`.

Allowed channels: `edi`, `email`, `sms`, `webhook`.

## Scenario requirements

| Requirement | Count or behavior |
| --- | --- |
| Total input lines | 32 |
| Unique normalized messages | 29 |
| Exact duplicates | 3 |
| Malformed input | 1 |
| Primary disruption | Port of Savannah weather event |
| Priority escalation | `OPS-40045-A`, temperature-sensitive pharma |
| Priority impact | Missed delivery window and $25,000 risk |
| Review cases | At least 2 |
| Approval-ready cases | At least 10 |

## Message mix

- 16 EDI-style status updates with shipment references and delay estimates.
- 8 broker or carrier emails with natural-language context.
- 4 concise SMS-style driver or reefer alerts.
- 3 exact duplicates of earlier messages, including one EDI and one email payload.
- 1 malformed message containing no usable operational facts.

## Required edge cases

### Duplicate delivery

At least three messages must be byte-for-byte duplicates of earlier records. The ingest result must record them as duplicates and must not create new exception records.

### Malformed feed

The malformed line should resemble a corrupted transport feed, for example:

```text
@@@#ERR 0x004452 FEED RESYNC ]]]]] NO PAYLOAD {{{{
```

Expected outcome: a visible `needs_human_review` record with no investigation trace.

### Missing reference

At least one natural-language message must describe a customs hold without a shipment reference. Expected outcome: investigation is bounded and the record routes to `needs_human_review` because confidence is below threshold.

### Pharma escalation

Include a message equivalent to:

```text
Escalation: OPS-40045-A is temperature-sensitive pharma with a hard delivery window Thursday 08:00-12:00. Current Savannah hold puts arrival at Thursday 15:40. Client contract has a $25k OTIF penalty clause. Need options today.
```

Expected outcome: severity 5, red tier, missed window, $25,000 affected value, ready for approval, and top position in the open queue.

## Replay assertions

A fresh replay must produce:

- `ingested == 29`
- `duplicates == 3`
- review queue size of at least 2
- approval-ready queue size of at least 10
- the pharma escalation as the highest-risk open record
- every investigation with `rounds_used <= 5`

A second replay without reset must create no new exception records and increase the duplicate counter by 32.

## Privacy and safety

All seed data must be fictional. Do not include customer names, real tracking numbers, email addresses, phone numbers, credentials, or other personal information.