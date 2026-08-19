# IMS Pro – Integrated Management System for Odoo 19
Publisher: Promotive IT System SRL
Version: 19.0.1.0.0

## Visual/Product rebuild
This build replaces the technical prototype user experience with a process-oriented IMS workspace.

### Homepage
- OWL client-action dashboard
- KPI cards
- Risk heatmap
- My IMS work queue
- Module tiles
- Next Audit / Management Review snapshot
- Global IMS Search shortcut

### Document Management
- Document Control and active-only Document Library
- Configurable folder tree
- Revisions, approval, release, archive
- Controlled PDF
- Header/footer template
- Visual kanban cards

### Risk
- Risk projects
- OHS hazards
- Environmental aspects
- Quality/enterprise risks
- Initial / residual risk
- 5x5 heatmap
- Controls and reviews

### Improvement
- Universal Q / OHS / ENV Nonconformities & Incidents
- CAPA with structured tabs
- Customer Complaints
- Change Control

### Assurance & Management
- Audit program / plan / findings
- Management Review / 15 review inputs
- Objectives & KPI
- Legal & Compliance Register

### Showcase dataset
Generic demonstration data includes:
- 30 IMS processes
- controlled-document tree and active documents
- Q/OHS/ENV risk projects and cases
- NC/incident examples
- CAPA examples
- customer complaints
- changes and impact records
- audits, plan items and findings
- management review template and review records
- objectives and compliance requirements
- My IMS actions

No real company or person names are embedded in the commercial product or demo dataset.


## 19.0.1.0.1
- Fixed Odoo.sh installation failure caused by `menu_ims_root` referencing `action_ims_dashboard_client` before the client action was loaded.
- Dashboard action now loads before the IMS Pro root menu.

## QA gate for every release

Before a package is promoted to Odoo.sh Development, IMS Pro is expected to pass:

1. Python compilation and XML/QWeb well-formedness.
2. Manifest/load-order and internal XML-ID reference validation.
3. JavaScript syntax validation for backend assets.
4. Security ACL/group consistency checks.
5. Regression checks for known Odoo 19 compatibility issues.
6. Odoo TransactionCase smoke tests in `tests/test_ims_core.py` on an actual Odoo 19 database.
7. Odoo.sh Development install/upgrade with demo data, followed by browser/UI review.

The local package validation does not replace the final Odoo.sh runtime gate because Enterprise-only dependencies (notably `documents`) and the exact Odoo.sh stack must be tested in the target environment.
