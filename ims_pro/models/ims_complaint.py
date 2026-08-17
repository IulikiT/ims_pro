from odoo import api, fields, models

class IMSComplaint(models.Model):
    _name = "ims.complaint"
    _description = "IMS Customer Complaint"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "received_date desc, id desc"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    title = fields.Char(required=True, tracking=True)
    customer_id = fields.Many2one("res.partner", required=True, domain=[("customer_rank",">",0)], tracking=True)
    contact_name = fields.Char()
    contact_email = fields.Char()
    contact_phone = fields.Char()
    category = fields.Selection([
        ("defect","Defective Product / Service"),
        ("transit","Damaged in Transit"),
        ("documentation","Documentation"),
        ("delivery","Delivery"),
        ("communication","Communication"),
        ("other","Other"),
    ], default="defect")
    severity = fields.Selection([("low","Low"),("medium","Medium"),("high","High"),("critical","Critical")], default="medium")
    received_date = fields.Date(default=fields.Date.context_today, tracking=True)
    due_date = fields.Date()
    originated_by_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    assigned_to_id = fields.Many2one("res.users")
    description = fields.Html(required=True)
    investigation = fields.Html()
    customer_response = fields.Html()
    decision = fields.Selection([("accepted","Accepted"),("partial","Partially Accepted"),("rejected","Rejected"),("unconfirmed","Not Confirmed")])
    state = fields.Selection([
        ("new","New"),
        ("acknowledged","Acknowledged"),
        ("investigation","Under Investigation"),
        ("action","Action Required"),
        ("response","Customer Response"),
        ("followup","Effectiveness / Follow-up"),
        ("closed","Closed"),
    ], default="new", tracking=True)
    reference = fields.Char(string="Customer PO / Internal Order / Other Reference")
    nonconformity_ids = fields.One2many("ims.nonconformity", "complaint_id")
    capa_ids = fields.Many2many("ims.capa")
    risk_case_ids = fields.Many2many("ims.risk.case")
    history_ids = fields.One2many("ims.complaint.history", "complaint_id")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name","New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.complaint") or "New"
        return super().create(vals_list)

class IMSComplaintHistory(models.Model):
    _name = "ims.complaint.history"
    _description = "IMS Complaint Timeline"
    _order = "event_datetime desc"

    complaint_id = fields.Many2one("ims.complaint", required=True, ondelete="cascade")
    event_datetime = fields.Datetime(default=fields.Datetime.now)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    event_type = fields.Selection([("communication","Communication"),("investigation","Investigation"),("decision","Decision"),("action","Action"),("other","Other")], default="other")
    notes = fields.Html(required=True)
