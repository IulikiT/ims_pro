from odoo import fields, models

class IMSStandard(models.Model):
    _name = "ims.standard"
    _description = "IMS Standard"
    _order = "name, version"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, index=True)
    version = fields.Char(required=True)
    domain = fields.Selection([
        ("quality", "Quality"),
        ("environment", "Environment"),
        ("ohs", "Occupational Health & Safety"),
        ("information_security", "Information Security"),
        ("integrated", "Integrated IMS"),
        ("other", "Other"),
    ], default="integrated", required=True)
    clause_ids = fields.One2many("ims.standard.clause", "standard_id", string="Clauses")

class IMSStandardClause(models.Model):
    _name = "ims.standard.clause"
    _description = "IMS Standard Clause"
    _order = "standard_id, code"

    standard_id = fields.Many2one("ims.standard", required=True, ondelete="cascade")
    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True, translate=True)
    parent_id = fields.Many2one("ims.standard.clause", string="Parent Clause", ondelete="cascade")
    requirement = fields.Html()
