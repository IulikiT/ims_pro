from odoo import api, fields, models

class IMSAction(models.Model):
    _name = "ims.action"
    _description = "IMS Action"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "due_date, priority desc, id desc"

    name = fields.Char(required=True, tracking=True)
    reference = fields.Char(default="New", copy=False, readonly=True, index=True)
    source_type = fields.Selection([
        ("general", "General IMS"),
        ("document", "Document"),
        ("risk", "Risk"),
        ("nonconformity", "Nonconformity / Incident"),
        ("capa", "CAPA"),
        ("audit", "Audit"),
        ("review", "Management Review"),
        ("compliance", "Compliance"),
        ("objective", "Objective"),
    ], default="general", required=True, tracking=True)
    process_id = fields.Many2one("ims.process", tracking=True)
    responsible_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user, tracking=True)
    due_date = fields.Date(tracking=True)
    completed_date = fields.Date(readonly=True)
    priority = fields.Selection([("0","Normal"),("1","High"),("2","Critical")], default="0", tracking=True)
    state = fields.Selection([
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("waiting", "Waiting"),
        ("done", "Closed"),
        ("cancelled", "Cancelled"),
    ], default="open", required=True, tracking=True)
    description = fields.Html()
    change_id = fields.Many2one("ims.change", ondelete="set null")
    risk_case_id = fields.Many2one("ims.risk.case", ondelete="set null")
    nonconformity_id = fields.Many2one("ims.nonconformity", ondelete="set null")
    capa_id = fields.Many2one("ims.capa", ondelete="set null")
    audit_finding_id = fields.Many2one("ims.audit.finding", ondelete="set null")
    review_id = fields.Many2one("ims.review", ondelete="set null")
    objective_id = fields.Many2one("ims.objective", ondelete="set null")
    evidence = fields.Html()
    is_overdue = fields.Boolean(compute="_compute_is_overdue", search="_search_is_overdue")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("reference", "New") == "New":
                vals["reference"] = self.env["ir.sequence"].next_by_code("ims.action") or "New"
        return super().create(vals_list)

    @api.depends("due_date", "state")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_overdue = bool(rec.due_date and rec.due_date < today and rec.state not in ("done","cancelled"))

    def _search_is_overdue(self, operator, value):
        today = fields.Date.context_today(self)
        domain = [("due_date", "<", today), ("state", "not in", ("done","cancelled"))]
        return domain if value else ["!"] + domain

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_close(self):
        self.write({"state": "done", "completed_date": fields.Date.context_today(self)})

    def action_reopen(self):
        self.write({"state": "open", "completed_date": False})
