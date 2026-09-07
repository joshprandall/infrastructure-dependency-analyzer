# Fictional construction operations — office and field dependency model

Potential impact under declared hard dependencies. Not live monitoring, outage prediction, or proof of recovery. No redundancy, partial degradation, or conditional dependency modeling.

## Review findings

- **MISSING_OWNER / collaboration:** owner is not recorded.
- **RTO_ALIGNMENT_REVIEW / erp-app:** Dependency erp-db has a 8h recovery target versus 4h for this service.
- **RTO_ALIGNMENT_REVIEW / office-firewall:** Dependency office-internet has a 4h recovery target versus 2h for this service.

## Dependency concentration

Ranked by potentially affected business services, then downstream services. This is not a risk score or proof of a single point of failure.

| Service | Downstream services | Business services including selected root |
| --- | ---: | ---: |
| Core network | 9 | 4 |
| DNS service | 7 | 4 |
| Directory / identity | 6 | 4 |
| Office internet | 6 | 3 |
| Office firewall | 5 | 3 |
| ERP database | 4 | 3 |
| Construction ERP | 3 | 3 |
| Field cellular uplink | 3 | 2 |
| Field-to-office VPN | 2 | 2 |
| Project document storage | 1 | 1 |
| Office Microsoft 365 access | 1 | 1 |
| Office project coordination | 0 | 1 |
| Field dispatch | 0 | 1 |
| Estimating workflow | 0 | 1 |
| Payroll processing | 0 | 1 |
| Field time entry | 0 | 1 |

## Scenario: Office internet

Selected service is excluded from the downstream count. Paths run from unavailable prerequisite to dependent consumer.

- Office internet → Office firewall
- Office internet → Office firewall → Field-to-office VPN
- Office internet → Office firewall → Office Microsoft 365 access
- Office internet → Office firewall → Office Microsoft 365 access → Office project coordination
- Office internet → Office firewall → Field-to-office VPN → Field dispatch
- Office internet → Office firewall → Field-to-office VPN → Field time entry

### Prerequisite validation waves

These include healthy prerequisites. They are not outage diagnoses, restore instructions, or duration estimates.

1. Core network, Field cellular uplink, Office internet
2. DNS service, ERP database, Office firewall
3. Field-to-office VPN, Directory / identity, Office Microsoft 365 access
4. Office project coordination, Construction ERP
5. Field dispatch, Field time entry
