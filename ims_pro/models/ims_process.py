from odoo import api, fields, models

class IMSProcess(models.Model):
    _name = "ims.process"
    _description = "IMS Process"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    active = fields.Boolean(default=True)
    code = fields.Char(required=True, index=True, tracking=True)
    name = fields.Char(required=True, translate=True, tracking=True)
    parent_id = fields.Many2one("ims.process", string="Parent Process", ondelete="restrict")
    child_ids = fields.One2many("ims.process", "parent_id", string="Subprocesses")
    owner_id = fields.Many2one("res.users", string="Process Owner", tracking=True)
    department_id = fields.Many2one("hr.department", tracking=True)
    description = fields.Html()
    standard_clause_ids = fields.Many2many("ims.standard.clause", string="Applicable Clauses")
    action_ids = fields.One2many("ims.action", "process_id", string="IMS Actions")
    action_count = fields.Integer(compute="_compute_action_count")

    @api.depends("action_ids")
    def _compute_action_count(self):
        for rec in self:
            rec.action_count = len(rec.action_ids)
    _code_uniq = models.Constraint("UNIQUE(code)", "IMS process code must be unique.")
