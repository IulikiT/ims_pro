from odoo import api, fields, models

class IMSComplianceRequirement(models.Model):
    _name = "ims.compliance.requirement"
    _description = "IMS Legal / Compliance Requirement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "review_date, title"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    title = fields.Char(required=True)
    authority = fields.Char()
    document_number = fields.Char()
    version_date = fields.Date()
    effective_date = fields.Date()
    domain = fields.Selection([("quality","Quality"),("ohs","OH&S"),("environment","Environment"),("infosec","Information Security"),("general","General")], default="general")
    applicability = fields.Html()
    obligation = fields.Html()
    responsible_id = fields.Many2one("res.users")
    process_ids = fields.Many2many("ims.process")
    evidence = fields.Html()
    compliance_status = fields.Selection([("not_evaluated","Not Evaluated"),("compliant","Compliant"),("partial","Partially Compliant"),("noncompliant","Noncompliant"),("na","Not Applicable")], default="not_evaluated")
    review_date = fields.Date()
    state = fields.Selection([("active","Active"),("superseded","Superseded"),("archived","Archived")], default="active")
    action_ids = fields.Many2many("ims.action")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name","New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.compliance") or "New"
        return super().create(vals_list)
