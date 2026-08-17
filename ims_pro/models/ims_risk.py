from odoo import api, fields, models
from odoo.exceptions import ValidationError

class IMSRiskMatrix(models.Model):
    _name = "ims.risk.matrix"
    _description = "IMS Risk Matrix"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    domain = fields.Selection([
        ("quality","Quality"),
        ("ohs","OH&S"),
        ("environment","Environment"),
        ("infosec","Information Security"),
        ("enterprise","Enterprise / General"),
    ], default="enterprise", required=True)
    probability_ids = fields.One2many("ims.risk.scale", "matrix_id", domain=[("scale_type","=","probability")])
    severity_ids = fields.One2many("ims.risk.scale", "matrix_id", domain=[("scale_type","=","severity")])
    level_ids = fields.One2many("ims.risk.level", "matrix_id")

class IMSRiskScale(models.Model):
    _name = "ims.risk.scale"
    _description = "IMS Risk Scale"
    _order = "scale_type, score"

    matrix_id = fields.Many2one("ims.risk.matrix", required=True, ondelete="cascade")
    scale_type = fields.Selection([("probability","Probability"),("severity","Severity")], required=True)
    name = fields.Char(required=True)
    score = fields.Integer(required=True)
    description = fields.Text()

class IMSRiskLevel(models.Model):
    _name = "ims.risk.level"
    _description = "IMS Risk Level"
    _order = "min_score"

    matrix_id = fields.Many2one("ims.risk.matrix", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    min_score = fields.Integer(required=True)
    max_score = fields.Integer(required=True)
    requires_treatment = fields.Boolean(default=True)
    requires_management_acceptance = fields.Boolean()

class IMSRiskProject(models.Model):
    _name = "ims.risk.project"
    _description = "IMS Risk Project"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    code = fields.Char(default="New", copy=False, readonly=True, index=True)
    name = fields.Char(required=True, tracking=True)
    domain = fields.Selection([
        ("quality","Quality / Business Risks"),
        ("ohs","OH&S Hazards"),
        ("environment","Environmental Aspects"),
        ("infosec","Information Security"),
        ("enterprise","Enterprise / General"),
    ], default="enterprise", required=True, tracking=True)
    process_id = fields.Many2one("ims.process", tracking=True)
    department_id = fields.Many2one("hr.department")
    owner_id = fields.Many2one("res.users", default=lambda self: self.env.user, tracking=True)
    matrix_id = fields.Many2one("ims.risk.matrix", required=True)
    review_frequency_months = fields.Integer(default=12)
    next_review_date = fields.Date()
    state = fields.Selection([("draft","Draft"),("active","Active"),("review","Under Review"),("archived","Archived")], default="draft", tracking=True)
    description = fields.Html()
    hazard_ids = fields.One2many("ims.risk.hazard", "project_id")
    standard_clause_ids = fields.Many2many("ims.standard.clause")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "New") == "New":
                vals["code"] = self.env["ir.sequence"].next_by_code("ims.risk.project") or "New"
        return super().create(vals_list)

class IMSRiskHazard(models.Model):
    _name = "ims.risk.hazard"
    _description = "IMS Hazard / Aspect / Source"
    _order = "sequence, name"

    project_id = fields.Many2one("ims.risk.project", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    category = fields.Char()
    source = fields.Char()
    activity = fields.Char()
    location = fields.Char()
    condition = fields.Selection([("normal","Normal"),("abnormal","Abnormal"),("emergency","Emergency")])
    directness = fields.Selection([("direct","Direct"),("indirect","Indirect")])
    persons_exposed = fields.Char()
    existing_controls = fields.Html()
    case_ids = fields.One2many("ims.risk.case", "hazard_id")

class IMSRiskCase(models.Model):
    _name = "ims.risk.case"
    _description = "IMS Risk / Opportunity Case"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(default="New", copy=False, readonly=True, index=True)
    title = fields.Char(required=True, tracking=True)
    hazard_id = fields.Many2one("ims.risk.hazard", required=True, ondelete="cascade")
    project_id = fields.Many2one(related="hazard_id.project_id", store=True)
    event = fields.Html(string="Hazardous Event / Aspect")
    consequence = fields.Html(string="Harm / Consequence / Impact")
    opportunity = fields.Boolean()
    initial_probability_id = fields.Many2one("ims.risk.scale", domain=[("scale_type","=","probability")])
    initial_severity_id = fields.Many2one("ims.risk.scale", domain=[("scale_type","=","severity")])
    initial_score = fields.Integer(compute="_compute_scores", store=True)
    initial_level = fields.Char(compute="_compute_scores", store=True)
    residual_probability_id = fields.Many2one("ims.risk.scale", domain=[("scale_type","=","probability")])
    residual_severity_id = fields.Many2one("ims.risk.scale", domain=[("scale_type","=","severity")])
    residual_score = fields.Integer(compute="_compute_scores", store=True)
    residual_level = fields.Char(compute="_compute_scores", store=True)
    acceptance_justification = fields.Html()
    contingency_response = fields.Html()
    responsible_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    due_date = fields.Date()
    review_date = fields.Date()
    state = fields.Selection([
        ("identified","Identified"),
        ("assessed","Assessed"),
        ("treatment","Treatment Required"),
        ("progress","Actions In Progress"),
        ("residual","Residual Assessment"),
        ("accepted","Accepted"),
        ("monitoring","Monitoring"),
        ("closed","Closed"),
        ("reopened","Reopened"),
    ], default="identified", tracking=True)
    control_ids = fields.Many2many("ims.risk.control", string="Controls / Risk Reduction Actions")
    action_ids = fields.One2many("ims.action", "risk_case_id")
    review_ids = fields.One2many("ims.risk.review", "risk_case_id")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("ims.risk.case") or "New"
        return super().create(vals_list)

    def _level_for_score(self, score):
        self.ensure_one()
        matrix = self.project_id.matrix_id
        lvl = matrix.level_ids.filtered(lambda l: l.min_score <= score <= l.max_score)[:1]
        return lvl.name if lvl else ""

    @api.depends("initial_probability_id.score","initial_severity_id.score","residual_probability_id.score","residual_severity_id.score","project_id.matrix_id.level_ids")
    def _compute_scores(self):
        for rec in self:
            rec.initial_score = (rec.initial_probability_id.score or 0) * (rec.initial_severity_id.score or 0)
            rec.residual_score = (rec.residual_probability_id.score or 0) * (rec.residual_severity_id.score or 0)
            rec.initial_level = rec._level_for_score(rec.initial_score) if rec.initial_score else ""
            rec.residual_level = rec._level_for_score(rec.residual_score) if rec.residual_score else ""

class IMSRiskControl(models.Model):
    _name = "ims.risk.control"
    _description = "IMS Risk Control"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True)
    category = fields.Selection([
        ("elimination","Elimination"),
        ("substitution","Substitution"),
        ("engineering","Engineering"),
        ("administrative","Administrative"),
        ("ppe","PPE"),
        ("environmental","Environmental Control"),
        ("technical","Technical / ISMS"),
        ("other","Other"),
    ], default="administrative")
    description = fields.Html()
    responsible_id = fields.Many2one("res.users")
    due_date = fields.Date()
    state = fields.Selection([("planned","Planned"),("progress","In Progress"),("implemented","Implemented"),("validated","Validated"),("ineffective","Ineffective")], default="planned")
    evidence = fields.Html()
    validation_result = fields.Selection([("effective","Effective"),("partial","Partially Effective"),("ineffective","Ineffective")])
    validation_notes = fields.Html()
    risk_case_ids = fields.Many2many("ims.risk.case", string="Controlled Risks")

class IMSRiskReview(models.Model):
    _name = "ims.risk.review"
    _description = "IMS Risk Review"
    _order = "review_date desc"

    risk_case_id = fields.Many2one("ims.risk.case", required=True, ondelete="cascade")
    reviewed_by_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    review_date = fields.Date(default=fields.Date.context_today)
    comments = fields.Html()
    next_review_date = fields.Date()
