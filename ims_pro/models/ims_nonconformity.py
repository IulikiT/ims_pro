from odoo import api, fields, models
from odoo.exceptions import ValidationError

class IMSNonconformity(models.Model):
    _name = "ims.nonconformity"
    _description = "IMS Nonconformity / Incident"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_detected desc, id desc"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    title = fields.Char(required=True, tracking=True)
    domain = fields.Selection([
        ("quality","Quality"),
        ("ohs","OH&S"),
        ("environment","Environment"),
        ("integrated","Integrated IMS"),
    ], required=True, default="quality", tracking=True)
    nc_type = fields.Selection([
        ("product","Product"),
        ("process","Process"),
        ("service","Service"),
        ("supplier","Supplier"),
        ("transport","Transport"),
        ("documentation","Documentation"),
        ("accident","Accident"),
        ("incident","Incident"),
        ("near_miss","Near Miss"),
        ("unsafe_act","Unsafe Act"),
        ("unsafe_condition","Unsafe Condition"),
        ("environmental_incident","Environmental Incident"),
        ("spill","Spill / Release"),
        ("waste","Waste Nonconformity"),
        ("emission","Emission"),
        ("resource","Resource / Energy"),
        ("other","Other"),
    ], default="process", tracking=True)
    source = fields.Selection([
        ("incoming","Incoming Inspection"),
        ("production","Production"),
        ("in_process","In-process Control"),
        ("final","Final Inspection"),
        ("warehouse","Warehouse"),
        ("delivery","Delivery / Transport"),
        ("customer","Customer Complaint"),
        ("audit","Audit"),
        ("supplier","Supplier"),
        ("maintenance","Maintenance"),
        ("ohs","OH&S"),
        ("environment","Environment"),
        ("other","Other"),
    ], default="production")
    severity = fields.Selection([("minor","Minor"),("major","Major"),("critical","Critical")], default="minor", tracking=True)
    process_id = fields.Many2one("ims.process")
    department_id = fields.Many2one("hr.department")
    date_detected = fields.Date(default=fields.Date.context_today, tracking=True)
    originated_by_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    assigned_to_id = fields.Many2one("res.users")
    due_date = fields.Date()
    description = fields.Html(required=True)
    immediate_action = fields.Html()
    investigation = fields.Html()
    root_cause = fields.Html()
    root_cause_method = fields.Selection([("5why","5 Why"),("ishikawa","Ishikawa"),("8d","8D"),("5w2h","5W2H"),("other","Other")])
    disposition = fields.Selection([
        ("accept","Accept As-Is"),
        ("rework","Rework"),
        ("repair","Repair"),
        ("reinspect","Re-inspect"),
        ("sort","100% Sort / Inspection"),
        ("return_supplier","Return to Supplier"),
        ("scrap","Scrap"),
        ("replace","Replace"),
        ("concession","Customer Concession"),
        ("quarantine","Quarantine / Hold"),
        ("other","Other"),
    ])
    disposition_notes = fields.Html()
    verification_notes = fields.Html()
    closure_notes = fields.Html()
    state = fields.Selection([
        ("draft","Draft"),
        ("open","Open"),
        ("containment","Containment"),
        ("investigation","Investigation"),
        ("disposition","Disposition"),
        ("implementation","Implementation"),
        ("verification","Verification"),
        ("closed","Closed"),
        ("cancelled","Cancelled"),
    ], default="draft", tracking=True)
    complaint_id = fields.Many2one("ims.complaint", ondelete="set null")
    capa_ids = fields.One2many("ims.capa", "nonconformity_id")
    risk_case_ids = fields.Many2many("ims.risk.case")
    action_ids = fields.One2many("ims.action", "nonconformity_id")
    partner_id = fields.Many2one("res.partner", string="Customer / Supplier")
    reference = fields.Char(string="Order / Lot / Serial / Other Reference")
    material_cost = fields.Monetary(currency_field="currency_id")
    labor_cost = fields.Monetary(currency_field="currency_id")
    external_cost = fields.Monetary(currency_field="currency_id")
    total_cost = fields.Monetary(compute="_compute_total_cost", store=True, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)

    @api.depends("material_cost","labor_cost","external_cost")
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.material_cost + rec.labor_cost + rec.external_cost

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name","New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.nonconformity") or "New"
        return super().create(vals_list)

    def action_close(self):
        for rec in self:
            if rec.action_ids.filtered(lambda a: a.state not in ("done","cancelled")):
                raise ValidationError("Close all related IMS actions before closing the nonconformity.")
            rec.state = "closed"
