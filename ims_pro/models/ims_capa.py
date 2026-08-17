from odoo import api, fields, models
from odoo.exceptions import ValidationError

class IMSCAPA(models.Model):
    _name = "ims.capa"
    _description = "IMS Corrective and Preventive Action"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "origination_date desc, id desc"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    title = fields.Char(required=True, tracking=True)
    capa_type = fields.Selection([("internal","Internal"),("external","External")], default="internal")
    domain = fields.Selection([("quality","Quality"),("ohs","OH&S"),("environment","Environment"),("integrated","Integrated IMS"),("infosec","Information Security")], default="quality")
    process_id = fields.Many2one("ims.process")
    origination_date = fields.Date(default=fields.Date.context_today)
    originated_by_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    assigned_to_id = fields.Many2one("res.users")
    due_date = fields.Date()
    followup_due_date = fields.Date()
    description = fields.Html(required=True)
    containment = fields.Html()
    investigation = fields.Html()
    root_cause = fields.Html()
    root_cause_method = fields.Selection([("5why","5 Why"),("ishikawa","Ishikawa"),("8d","8D"),("5w2h","5W2H"),("other","Other")])
    systemic_effects = fields.Html(string="Effects on Similar Products / Processes / Sites")
    corrective_action = fields.Html()
    preventive_action = fields.Html()
    implementation_verification = fields.Html()
    effectiveness_criteria = fields.Html()
    effectiveness_result = fields.Selection([("effective","Effective"),("partial","Partially Effective"),("ineffective","Ineffective")])
    effectiveness_notes = fields.Html()
    qms_update_required = fields.Boolean(string="IMS / Document Update Required")
    risk_update_required = fields.Boolean()
    state = fields.Selection([
        ("draft","Draft"),
        ("open","Open"),
        ("investigation","Investigation"),
        ("actions","Actions"),
        ("implementation","Implementation"),
        ("followup","Follow-up / Effectiveness"),
        ("closed","Closed"),
        ("reopened","Reopened"),
    ], default="draft", tracking=True)
    nonconformity_id = fields.Many2one("ims.nonconformity", ondelete="set null")
    complaint_ids = fields.Many2many("ims.complaint")
    risk_case_ids = fields.Many2many("ims.risk.case")
    change_ids = fields.Many2many("ims.change")
    action_ids = fields.One2many("ims.action", "capa_id")
    recurrence = fields.Boolean()
    cost = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name","New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.capa") or "New"
        return super().create(vals_list)

    def action_close(self):
        for rec in self:
            if rec.effectiveness_result not in ("effective","partial"):
                raise ValidationError("Effectiveness must be verified before CAPA closure.")
            if rec.action_ids.filtered(lambda a: a.state not in ("done","cancelled")):
                raise ValidationError("Close all related IMS actions before CAPA closure.")
            rec.state = "closed"
