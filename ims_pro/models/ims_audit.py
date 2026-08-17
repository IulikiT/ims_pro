from odoo import api, fields, models

class IMSAuditProgram(models.Model):
    _name = "ims.audit.program"
    _description = "IMS Audit Program"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "year desc, name"

    name = fields.Char(required=True)
    year = fields.Integer(required=True)
    audit_ids = fields.One2many("ims.audit", "program_id")
    state = fields.Selection([("draft","Draft"),("approved","Approved"),("active","Active"),("closed","Closed")], default="draft")

class IMSAudit(models.Model):
    _name = "ims.audit"
    _description = "IMS Audit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "planned_date desc, id desc"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    title = fields.Char(required=True, tracking=True)
    program_id = fields.Many2one("ims.audit.program")
    audit_type = fields.Selection([
        ("internal","Internal IMS"),
        ("external","External / Certification"),
        ("supplier","Supplier"),
        ("customer","Customer"),
        ("process","Process"),
        ("product","Product"),
        ("compliance","Compliance"),
        ("hse","HSE / Environmental"),
        ("infosec","Information Security"),
    ], default="internal")
    scope = fields.Html()
    criteria = fields.Html()
    planned_date = fields.Date()
    actual_date = fields.Date()
    lead_auditor_id = fields.Many2one("res.users")
    auditor_ids = fields.Many2many("res.users", "ims_audit_auditor_rel", string="Audit Team")
    standard_clause_ids = fields.Many2many("ims.standard.clause")
    process_ids = fields.Many2many("ims.process")
    plan_item_ids = fields.One2many("ims.audit.plan.item", "audit_id")
    finding_ids = fields.One2many("ims.audit.finding", "audit_id")
    conclusion = fields.Html()
    score = fields.Float()
    state = fields.Selection([("draft","Draft"),("planned","Planned"),("progress","In Progress"),("completed","Completed"),("closed","Closed")], default="draft", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name","New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.audit") or "New"
        return super().create(vals_list)

class IMSAuditPlanItem(models.Model):
    _name = "ims.audit.plan.item"
    _description = "IMS Audit Plan Item"
    _order = "planned_date, sequence"

    audit_id = fields.Many2one("ims.audit", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    process_id = fields.Many2one("ims.process", required=True)
    location = fields.Char()
    auditor_id = fields.Many2one("res.users")
    planned_date = fields.Date()
    actual_date = fields.Date()
    state = fields.Selection([("planned","Planned"),("progress","In Progress"),("done","Done"),("cancelled","Cancelled")], default="planned")
    comments = fields.Html()

class IMSAuditFinding(models.Model):
    _name = "ims.audit.finding"
    _description = "IMS Audit Finding"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    audit_id = fields.Many2one("ims.audit", required=True, ondelete="cascade")
    title = fields.Char(required=True)
    finding_type = fields.Selection([
        ("major","Major NC"),
        ("minor","Minor NC"),
        ("observation","Observation"),
        ("ofi","Opportunity for Improvement"),
        ("good","Good Practice"),
    ], required=True, default="observation")
    process_id = fields.Many2one("ims.process")
    clause_ids = fields.Many2many("ims.standard.clause")
    evidence = fields.Html()
    description = fields.Html(required=True)
    responsible_id = fields.Many2one("res.users")
    due_date = fields.Date()
    root_cause = fields.Html()
    corrective_action = fields.Html()
    effectiveness_result = fields.Selection([("effective","Effective"),("partial","Partially Effective"),("ineffective","Ineffective")])
    closeout_notes = fields.Html()
    state = fields.Selection([("open","Open"),("action","Action In Progress"),("followup","Follow-up"),("closed","Closed")], default="open")
    capa_ids = fields.Many2many("ims.capa")
    risk_case_ids = fields.Many2many("ims.risk.case")
    change_ids = fields.Many2many("ims.change")
    action_ids = fields.One2many("ims.action", "audit_finding_id")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name","New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.audit.finding") or "New"
        return super().create(vals_list)
