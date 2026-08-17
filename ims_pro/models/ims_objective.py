from odoo import api, fields, models

class IMSObjective(models.Model):
    _name = "ims.objective"
    _description = "IMS Objective / Target"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "due_date, id desc"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    title = fields.Char(required=True)
    domain = fields.Selection([("quality","Quality"),("ohs","OH&S"),("environment","Environment"),("infosec","Information Security"),("integrated","Integrated IMS")], default="integrated")
    process_id = fields.Many2one("ims.process")
    owner_id = fields.Many2one("res.users", required=True)
    baseline = fields.Char()
    target = fields.Char(required=True)
    measurement_unit = fields.Char()
    actual_value = fields.Char()
    progress = fields.Float()
    date_start = fields.Date(default=fields.Date.context_today)
    due_date = fields.Date(required=True)
    resources = fields.Html()
    methods = fields.Html()
    evaluation = fields.Html()
    state = fields.Selection([("draft","Draft"),("approved","Approved"),("progress","In Progress"),("achieved","Achieved"),("partial","Partially Achieved"),("not_achieved","Not Achieved"),("closed","Closed")], default="draft")
    review_id = fields.Many2one("ims.review", ondelete="set null")
    action_ids = fields.One2many("ims.action", "objective_id")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name","New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.objective") or "New"
        return super().create(vals_list)
