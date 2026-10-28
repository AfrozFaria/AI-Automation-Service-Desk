# Claims Intake Automation Guide
## What it does
The automation reads incoming claim emails, extracts key fields, verifies the policy and routes the claim.
## What it never does
It never approves or rejects a claim and never sends emails by itself. Every reply is reviewed by a claims handler.
## Routing queues
Standard queue, senior review (over EUR 5,000, high urgency or above the coverage limit), fraud review (name mismatch or possible duplicate), policy issue, request more info and manual review.
## When a claim goes to manual review
Emails containing instructions aimed at the system, or where extraction fails, go to manual review.
## Reporting problems
If a claim is misrouted, tell the AI Support Desk with the claim file name.