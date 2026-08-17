from odoo import api, fields, models
from odoo.exceptions import ValidationError

class IMSSupplierSCAR(models.Model):
    _name = "ims.supplier.scar"
    _description = "IMS Supplier Corrective Action Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, id desc"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    title = fields.Char(required=True, tracking=True)
    supplier_id = fields.Many2one("res.partner", required=True, domain=[("supplier_rank", ">", 0)], tracking=True)
    request_date = fields.Date(default=fields.Date.context_today)
    due_date = fields.Date()
    responsible_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    source_nonconformity_id = fields.Many2one("ims.nonconformity", ondelete="set null")
    description = fields.Html(required=True)
    containment_required = fields.Html()
    supplier_root_cause = fields.Html()
    supplier_action_plan = fields.Html()
    verification = fields.Html()
    effectiveness_result = fields.Selection([("effective","Effective"),("partial","Partially Effective"),("ineffective","Ineffective")])
    state = fields.Selection([
        ("draft","Draft"),("sent","Sent to Supplier"),("response","Supplier Response"),
        ("implementation","Implementation"),("verification","Verification"),("closed","Closed")
    ], default="draft", tracking=True)
    action_ids = fields.Many2many("ims.action")
    capa_ids = fields.Many2many("ims.capa")
    risk_case_ids = fields.Many2many("ims.risk.case")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name","New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.supplier.scar") or "New"
        return super().create(vals_list)

    def action_close(self):
        for rec in self:
            if rec.effectiveness_result not in ("effective","partial"):
                raise ValidationError("Verify effectiveness before closing the SCAR.")
            rec.state = "closed"
