from odoo import api, fields, models

class IMSReviewTemplate(models.Model):
    _name = "ims.review.template"
    _description = "IMS Management Review Template"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    item_template_ids = fields.One2many("ims.review.item.template", "template_id")

class IMSReviewItemTemplate(models.Model):
    _name = "ims.review.item.template"
    _description = "IMS Review Item Template"
    _order = "sequence, id"

    template_id = fields.Many2one("ims.review.template", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    data_source = fields.Selection([("manual","Manual"),("ims","IMS Module"),("odoo","Odoo"),("mixed","Mixed")], default="mixed")

class IMSReview(models.Model):
    _name = "ims.review"
    _description = "IMS Management Review"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "review_date desc, id desc"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    title = fields.Char(required=True)
    template_id = fields.Many2one("ims.review.template")
    review_type = fields.Selection([("integrated","Integrated IMS"),("quality","Quality"),("environment","Environment"),("ohs","OH&S"),("infosec","Information Security"),("custom","Custom")], default="integrated")
    standard_ids = fields.Many2many("ims.standard")
    period_from = fields.Date(required=True)
    period_to = fields.Date(required=True)
    review_date = fields.Date(required=True)
    closeout_due_date = fields.Date()
    chairperson_id = fields.Many2one("res.users")
    coordinator_id = fields.Many2one("res.users")
    participant_ids = fields.Many2many("res.users", "ims_review_participant_rel")
    item_ids = fields.One2many("ims.review.item", "review_id")
    objective_ids = fields.One2many("ims.objective", "review_id")
    action_ids = fields.One2many("ims.action", "review_id")
    evidence_reviewed = fields.Html()
    closeout_notes = fields.Html()
    state = fields.Selection([("draft","Draft"),("planned","Planned"),("progress","In Progress"),("actions","Actions Pending"),("closed","Closed")], default="draft", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name","New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.review") or "New"
        return super().create(vals_list)

    def action_generate_items(self):
        for rec in self:
            if not rec.template_id:
                continue
            rec.item_ids.unlink()
            vals = []
            for item in rec.template_id.item_template_ids:
                vals.append((0,0,{"sequence":item.sequence,"name":item.name,"data_source":item.data_source}))
            rec.item_ids = vals

class IMSReviewItem(models.Model):
    _name = "ims.review.item"
    _description = "IMS Management Review Item"
    _order = "sequence, id"

    review_id = fields.Many2one("ims.review", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    data_source = fields.Selection([("manual","Manual"),("ims","IMS Module"),("odoo","Odoo"),("mixed","Mixed")], default="mixed")
    process_ids = fields.Many2many("ims.process")
    input_data = fields.Html(string="Input / Evidence")
    analysis = fields.Html()
    trend = fields.Selection([("improving","Improving"),("stable","Stable"),("deteriorating","Deteriorating"),("insufficient","Insufficient Data")])
    conclusion = fields.Selection([("effective","Effective"),("partial","Partially Effective"),("ineffective","Ineffective"),("na","Not Applicable")])
    output_decision = fields.Html(string="Output / Decision")
    action_required = fields.Boolean()
