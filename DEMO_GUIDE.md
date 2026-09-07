# A three-minute demonstration

Open `examples/interactive-report.html`. No Python installation is needed to demonstrate this saved report.

## 1. Frame the problem — 20 seconds

“This is a fictional construction-office and jobsite model. The question is: if one IT service becomes unavailable, which business workflows should we investigate and which owners should be involved?”

## 2. Show office connectivity — 45 seconds

Select **Office internet**. Six downstream services and three business workflows are shown. Point to dispatch, field time entry, and office coordination. Expand one path to show why it appears.

“The impact list comes from recorded dependencies. I would validate those links with the actual application and business owners. I would also check cellular alternatives, cached access, and manual workarounds before treating this as a confirmed outage.”

## 3. Show recovery judgment — 45 seconds

Select **ERP database**. Review the dependent ERP application, payroll, dispatch, and time entry. Point to the recovery-target finding.

“The database target is eight hours while the application target is four. That is a planning question: do the objectives need to change, or does the recovery design need improvement? This model does not assume that declared targets equal demonstrated recovery capability.”

## 4. Show communication and ownership — 30 seconds

Point to the missing owner finding. Show the prerequisite validation waves.

“The technical chain helps structure the response, but ownership and communication matter too. I would assign an incident lead, validate the recovery prerequisites, and keep affected teams informed with known facts.”

## 5. Show engineering discipline — 30 seconds

Open `tests/test_analyzer.py` or the GitHub Actions results once published.

“The tests cover directionality, cycles, duplicate paths, invalid inventories, and the distinction between affected services and healthy prerequisites. It runs locally without credentials or changing systems.”

## Before presenting

- Run the project and explain at least the chain, diamond, and cycle tests.
- Be able to explain **RTO** (recovery-time objective) versus **RPO** (acceptable data-loss window).
- Explain why a prerequisite’s RTO greater than a consumer’s RTO is a review finding, not proof of an outage.
- Explain why this is not a real single-point-of-failure assessment: redundancy is not modeled.
- Describe the actual development and review process accurately if asked.
- Do not claim these are employer systems, client results, or production deployments.

## Useful follow-up questions

- Which workflows have the greatest operational urgency during an outage?
- Which systems support job cost, payroll, dispatch, plans, and field communications?
- Which vendors own the application, hosting, network, and backup responsibilities?
- When was recovery last tested, and what was actually measured?
- What work can crews continue when connectivity is unavailable?
