from odoo import api, fields, models

class IMSGlobalSearch(models.TransientModel):
    _name = "ims.global.search"
    _description = "IMS Global Search"

    query = fields.Char(required=True)
    result_ids = fields.One2many("ims.global.search.result", "wizard_id", readonly=True)

    def action_search(self):
        self.ensure_one()
        self.result_ids.unlink()
        q = (self.query or "").strip()
        if not q:
            return

        commands = []
        specs = [
            ("ims.document", "Document", ["code", "name"]),
            ("ims.document.revision", "Document Revision", ["revision"]),
            ("ims.process", "Process", ["code", "name"]),
            ("ims.action", "IMS Action", ["reference", "name"]),
            ("ims.standard", "Standard", ["name", "version"]),
            ("ims.standard.clause", "Standard Clause", ["code", "name"]),
            ("ims.change", "Change Notice", ["name", "title"]),
            ("ims.risk.project", "Risk Project", ["code", "name"]),
            ("ims.risk.case", "Risk Case", ["name", "title"]),
            ("ims.nonconformity", "Nonconformity / Incident", ["name", "title"]),
            ("ims.complaint", "Customer Complaint", ["name", "title"]),
            ("ims.capa", "CAPA", ["name", "title"]),
            ("ims.audit", "Audit", ["name", "title"]),
            ("ims.audit.finding", "Audit Finding", ["name", "title"]),
            ("ims.review", "Management Review", ["name", "title"]),
            ("ims.objective", "Objective", ["name", "title"]),
            ("ims.compliance.requirement", "Compliance Requirement", ["name", "title"]),
            ("ims.supplier.scar", "Supplier SCAR", ["name", "title"]),
        ]

        for model_name, label, fields_to_search in specs:
            model = self.env[model_name]
            domain = []
            for fname in fields_to_search:
                term = [(fname, "ilike", q)]
                domain = term if not domain else ["|"] + domain + term
            for rec in model.search(domain, limit=50):
                display = rec.display_name
                if model_name == "ims.document":
                    display = "%s - %s" % (rec.code, rec.name)
                elif model_name == "ims.action":
                    display = "%s - %s" % (rec.reference, rec.name)
                commands.append((0, 0, {
                    "model_name": model_name,
                    "record_id": rec.id,
                    "record_type": label,
                    "result_name": display,
                }))

        self.result_ids = commands
        return {
            "type": "ir.actions.act_window",
            "res_model": "ims.global.search",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

class IMSGlobalSearchResult(models.TransientModel):
    _name = "ims.global.search.result"
    _description = "IMS Global Search Result"
    _order = "record_type, result_name, id"

    wizard_id = fields.Many2one("ims.global.search", ondelete="cascade")
    record_type = fields.Char(readonly=True)
    result_name = fields.Char(string="Result", readonly=True, required=True)
    model_name = fields.Char(readonly=True)
    record_id = fields.Integer(readonly=True)

    def action_open_record(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self.model_name,
            "res_id": self.record_id,
            "view_mode": "form",
            "target": "current",
        }
