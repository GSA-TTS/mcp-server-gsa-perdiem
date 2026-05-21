1. Single-city lodging lookup
"What is the per diem lodging rate for Pensacola, FL in November 2025?"
---

2. M&IE tier math
"My travel destination has a $79 M&IE rate in FY2026. How much can I claim for dinner, and what is my allowance on the first day of travel?"
---

3. ZIP code lookup
"What is the daily meal allowance for ZIP code 94102 in FY2026?"
---

4. State browsing + comparison
"Which city in Nevada has the highest lodging rate in January 2026?"
Expected: Las Vegas (or similar — you can verify against the state list). Tests perdiem_get_rates_by_state, pagination, and whether the agent can sort/compare across results.
---

5. Multi-step: cheapest month
"I have flexibility on when I travel to San Francisco in FY2026. Which months have the lowest lodging rate, and how much would I save compared to the most expensive months?"

Expected: April–August at $270 vs. January–March at $333 — a $63/night difference. Tests whether the agent synthesizes across all 12 months in a single city response.