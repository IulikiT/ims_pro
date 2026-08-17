from odoo import api, fields, models
from odoo.exceptions import ValidationError

class IMSChange(models.Model):
    _name = "ims.change"
    _description = "IMS Change Notice"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    title = fields.Char(required=True, tracking=True)
    description = fields.Html(required=True)
    justification = fields.Html()
    process_id = fields.Many2one("ims.process", tracking=True)
    requested_by_id = fields.Many2one("res.users", default=lambda self: self.env.user, tracking=True)
    owner_id = fields.Many2one("res.users", string="Change Owner", tracking=True)
    request_date = fields.Date(default=fields.Date.context_today, tracking=True)
    due_date = fields.Date(tracking=True)
    effective_date = fields.Date(readonly=True, tracking=True)
    priority = fields.Selection([("low","Low"),("normal","Normal"),("high","High"),("critical","Critical")], default="normal", tracking=True)
    state = fields.Selection([
        ("draft","Draft"),
        ("impact","Impact Assessment"),
        ("submitted","Submitted"),
        ("approved","Approved"),
        ("implementation","Implementation"),
        ("verification","Verification"),
        ("ready","Ready to Close"),
        ("closed","Closed"),
        ("rejected","Rejected"),
        ("cancelled","Cancelled"),
    ], default="draft", required=True, tracking=True)
    impact_ids = fields.One2many("ims.change.impact", "change_id")
    document_line_ids = fields.One2many("ims.change.document", "change_id")
    action_ids = fields.One2many("ims.action", "change_id")
    verification_notes = fields.Html()
    closure_notes = fields.Html()
    standard_clause_ids = fields.Many2many("ims.standard.clause")
    related_change_ids = fields.Many2many("ims.change", "ims_change_rel", "src_id", "dst_id", string="Related Changes")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.change") or "New"
        return super().create(vals_list)

    def action_start_impact(self):
        self.write({"state":"impact"})
    def action_submit(self):
        self.write({"state":"submitted"})
    def action_approve(self):
        self.write({"state":"approved"})
    def action_start_implementation(self):
        self.write({"state":"implementation"})
    def action_start_verification(self):
        self.write({"state":"verification"})
    def action_ready_close(self):
        self.write({"state":"ready"})
    def action_close(self):
        for rec in self:
            open_actions = rec.action_ids.filtered(lambda a: a.state not in ("done","cancelled"))
            if open_actions:
                raise ValidationError("Close all IMS actions before closing the Change Notice.")
            rec.write({"state":"closed","effective_date":fields.Date.context_today(self)})

class IMSChangeImpact(models.Model):
    _name = "ims.change.impact"
    _description = "IMS Change Impact"
    _order = "sequence, id"

    change_id = fields.Many2one("ims.change", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    category = fields.Selection([
        ("documents","Documents"),
        ("processes","Processes"),
        ("products","Products / Services"),
        ("equipment","Equipment / Tooling"),
        ("quality","Quality"),
        ("inventory","Inventory"),
        ("purchase","Purchase / Suppliers"),
        ("manufacturing","Manufacturing"),
        ("training","Training / Competence"),
        ("risk","Risks & Opportunities"),
        ("environment","Environment"),
        ("ohs","OH&S"),
        ("infosec","Information Security"),
        ("legal","Legal / Regulatory"),
        ("customer","Customers"),
        ("project","Projects"),
        ("other","Other"),
    ], required=True)
    affected = fields.Boolean(default=True)
    assessment = fields.Html()
    action_required = fields.Boolean()
    completed = fields.Boolean()
    evidence = fields.Html()

class IMSChangeDocument(models.Model):
    _name = "ims.change.document"
    _description = "IMS Change Affected Document"

    change_id = fields.Many2one("ims.change", required=True, ondelete="cascade")
    document_id = fields.Many2one("ims.document", required=True)
    current_revision_id = fields.Many2one(related="document_id.current_revision_id", readonly=True)
    new_revision_id = fields.Many2one("ims.document.revision")
    change_notes = fields.Html()
    release_on_close = fields.Boolean(default=False)
