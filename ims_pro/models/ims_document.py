from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class IMSDocumentFolder(models.Model):
    _name = "ims.document.folder"
    _description = "IMS Document Folder"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    parent_id = fields.Many2one("ims.document.folder", ondelete="cascade")
    child_ids = fields.One2many("ims.document.folder", "parent_id")
    active = fields.Boolean(default=True)
    complete_name = fields.Char(compute="_compute_complete_name", store=True, recursive=True)

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for rec in self:
            rec.complete_name = "%s / %s" % (rec.parent_id.complete_name, rec.name) if rec.parent_id else rec.name

    def name_get(self):
        return [(rec.id, rec.complete_name) for rec in self]


class IMSDocumentTemplate(models.Model):
    _name = "ims.document.template"
    _description = "IMS Document Header/Footer Template"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    header_html = fields.Html(string="Header")
    footer_html = fields.Html(string="Footer")
    first_page_header_html = fields.Html(string="First Page Header")
    show_document_code = fields.Boolean(default=True)
    show_revision = fields.Boolean(default=True)
    show_effective_date = fields.Boolean(default=True)
    show_page_number = fields.Boolean(default=True)


class IMSDocumentCategory(models.Model):
    _name = "ims.document.category"
    _description = "IMS Document Category"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    code_prefix = fields.Char()
    revision_scheme = fields.Selection([
        ("numeric", "Numeric: 1, 2, 3"),
        ("numeric_padded", "Numeric Padded: 001, 002"),
        ("alphabetic", "Alphabetic: A, B, C"),
        ("manual", "Manual"),
    ], default="numeric", required=True)
    default_review_months = fields.Integer(default=12)
    change_control_required = fields.Boolean(default=False)
    template_id = fields.Many2one("ims.document.template", string="Header/Footer Template")


class IMSDocument(models.Model):
    _name = "ims.document"
    _description = "Controlled IMS Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    active = fields.Boolean(default=True)
    code = fields.Char(required=True, index=True, tracking=True)
    name = fields.Char(required=True, translate=True, tracking=True)
    category_id = fields.Many2one("ims.document.category", tracking=True)
    folder_id = fields.Many2one("ims.document.folder", required=True, tracking=True)
    process_id = fields.Many2one("ims.process", tracking=True)
    owner_id = fields.Many2one("res.users", default=lambda self: self.env.user, tracking=True)
    issued_by_department_id = fields.Many2one("hr.department", string="Issued By", tracking=True)
    change_control_required = fields.Boolean(default=False, tracking=True)
    review_interval_months = fields.Integer(default=12)
    revision_ids = fields.One2many("ims.document.revision", "document_id", string="Revision History")
    current_revision_id = fields.Many2one("ims.document.revision", compute="_compute_current_revision", store=True, index=True)
    current_revision_label = fields.Char(related="current_revision_id.revision", string="Revision", store=True)
    current_revision_state = fields.Selection(related="current_revision_id.state", string="Revision Status", store=True)
    current_effective_date = fields.Date(related="current_revision_id.effective_date", string="Effective Date", store=True)
    current_review_date = fields.Date(related="current_revision_id.review_date", string="Review Date", store=True)

    standard_clause_ids = fields.Many2many("ims.standard.clause")
    related_document_ids = fields.Many2many(
        "ims.document", "ims_document_relation_rel", "src_id", "dst_id", string="Related Documents"
    )
    confidentiality = fields.Selection([
        ("internal", "Internal"),
        ("confidential", "Confidential"),
        ("public", "Public"),
    ], default="internal", tracking=True)

    @api.onchange("category_id")
    def _onchange_category_id(self):
        if self.category_id:
            self.review_interval_months = self.category_id.default_review_months
            self.change_control_required = self.category_id.change_control_required

    @api.depends("revision_ids.state", "revision_ids.effective_date")
    def _compute_current_revision(self):
        for rec in self:
            active_revs = rec.revision_ids.filtered(lambda r: r.state == "active").sorted(
                key=lambda r: (r.effective_date or fields.Date.from_string("1900-01-01"), r.id), reverse=True
            )
            rec.current_revision_id = active_revs[:1].id if active_revs else False

    def _next_revision_label(self):
        self.ensure_one()
        scheme = self.category_id.revision_scheme or "numeric"
        revs = [r.revision for r in self.revision_ids]
        if scheme == "alphabetic":
            letters = [r for r in revs if r and len(r) == 1 and r.isalpha()]
            return chr(max([ord(x.upper()) for x in letters], default=64) + 1)
        nums = []
        for r in revs:
            try:
                nums.append(int(r))
            except (TypeError, ValueError):
                pass
        value = max(nums, default=0) + 1
        return ("%03d" % value) if scheme == "numeric_padded" else str(value)

    def action_new_revision(self):
        self.ensure_one()
        if self.change_control_required:
            raise UserError(
                "This document is under enforced Change Control. "
                "A future IMS Pro build will create the revision from an approved Change Notice."
            )
        rev = self.env["ims.document.revision"].create({
            "document_id": self.id,
            "revision": self._next_revision_label(),
            "state": "draft",
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "ims.document.revision",
            "res_id": rev.id,
            "view_mode": "form",
            "target": "current",
        }
    _code_uniq = models.Constraint("UNIQUE(code)", "Controlled document code must be unique.")
class IMSDocumentRevision(models.Model):
    _name = "ims.document.revision"
    _description = "IMS Document Revision"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "document_id, id desc"

    document_id = fields.Many2one("ims.document", required=True, ondelete="cascade", tracking=True)
    revision = fields.Char(required=True, tracking=True)
    internal_revision = fields.Char()
    state = fields.Selection([
        ("draft", "Draft"),
        ("review", "In Review"),
        ("approval", "Approval"),
        ("approved", "Approved"),
        ("active", "Active / Released"),
        ("superseded", "Superseded"),
        ("archived", "Archived"),
    ], default="draft", required=True, tracking=True)
    effective_date = fields.Date(readonly=True, tracking=True)
    review_date = fields.Date(tracking=True)
    is_review_overdue = fields.Boolean(compute="_compute_review_overdue")
    body_html = fields.Html(
        string="Internal Editor",
        sanitize=False,
        help="Editable controlled source using the Odoo rich-text editor."
    )
    change_summary = fields.Html()
    release_notes = fields.Html()
    source_attachment_id = fields.Many2one("ir.attachment", string="Editable Source File")
    released_pdf_id = fields.Many2one("ir.attachment", string="Released PDF")
    approval_ids = fields.One2many("ims.document.approval", "revision_id")
    required_approvals = fields.Integer(default=1)
    approval_mode = fields.Selection([
        ("parallel", "Parallel"),
        ("sequential", "Sequential"),
    ], default="parallel", required=True)
    approval_count = fields.Integer(compute="_compute_approval_count")
    template_id = fields.Many2one(
        "ims.document.template",
        compute="_compute_template_id",
        store=False
    )

    @api.depends("document_id.category_id.template_id")
    def _compute_template_id(self):
        for rec in self:
            rec.template_id = rec.document_id.category_id.template_id

    @api.depends("review_date", "state")
    def _compute_review_overdue(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_review_overdue = bool(
                rec.state == "active" and rec.review_date and rec.review_date < today
            )

    @api.depends("approval_ids.state")
    def _compute_approval_count(self):
        for rec in self:
            rec.approval_count = len(rec.approval_ids.filtered(lambda a: a.state == "approved"))

    def write(self, vals):
        protected = {"body_html", "change_summary", "source_attachment_id", "revision"}
        if protected.intersection(vals):
            locked = self.filtered(lambda r: r.state in ("active", "superseded", "archived"))
            if locked:
                raise ValidationError(
                    "Released, superseded, and archived revisions are immutable. Create a new revision."
                )
        return super().write(vals)

    def action_request_review(self):
        self.write({"state": "review"})

    def action_request_approval(self):
        for rec in self:
            if not rec.approval_ids:
                raise ValidationError("Assign at least one approver before requesting approval.")
            today = fields.Date.context_today(self)
            for approval in rec.approval_ids.filtered(lambda a: a.state == "pending"):
                approval.write({"state": "requested", "request_date": today})
            rec.state = "approval"

    def action_mark_approved(self):
        for rec in self:
            if rec.approval_count < rec.required_approvals:
                raise ValidationError("Required approvals have not been completed.")
            rec.state = "approved"

    def action_release(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state != "approved":
                raise ValidationError("Only an approved revision can be released.")
            if rec.approval_count < rec.required_approvals:
                raise ValidationError("Required approvals have not been completed.")
            old = rec.document_id.revision_ids.filtered(lambda r: r.state == "active" and r != rec)
            old.write({"state": "superseded"})
            months = rec.document_id.review_interval_months or 12
            review_date = today + relativedelta(months=months)
            rec.write({
                "state": "active",
                "effective_date": today,
                "review_date": review_date,
            })
            rec.message_post(body="Revision released and made ACTIVE.")
        return True

    def action_archive(self):
        self.write({"state": "archived"})

    def action_print_controlled_pdf(self):
        self.ensure_one()
        if self.state not in ("approved", "active", "superseded", "archived"):
            raise ValidationError("Controlled PDF is available only for approved/released revisions.")
        return self.env.ref("ims_pro.action_report_ims_controlled_document").report_action(self)


class IMSDocumentApproval(models.Model):
    _name = "ims.document.approval"
    _description = "IMS Document Approval"
    _order = "sequence, id"

    revision_id = fields.Many2one("ims.document.revision", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    approver_id = fields.Many2one("res.users", required=True)
    request_date = fields.Date()
    due_date = fields.Date()
    decision_date = fields.Datetime(readonly=True)
    state = fields.Selection([
        ("pending", "Pending"),
        ("requested", "Requested"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ], default="pending", required=True)
    comment = fields.Text()
    is_overdue = fields.Boolean(compute="_compute_is_overdue")

    @api.depends("due_date", "state")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_overdue = bool(
                rec.due_date and rec.due_date < today and rec.state in ("pending", "requested")
            )

    def action_approve(self):
        for rec in self:
            revision = rec.revision_id
            if revision.approval_mode == "sequential":
                earlier = revision.approval_ids.filtered(
                    lambda a: a.sequence < rec.sequence and a.state != "approved"
                )
                if earlier:
                    raise ValidationError("Previous sequential approvals must be completed first.")
            rec.write({"state": "approved", "decision_date": fields.Datetime.now()})
            revision.message_post(
                body="Approved by %s." % rec.approver_id.display_name
            )
            if revision.approval_count >= revision.required_approvals:
                revision.state = "approved"

    def action_reject(self):
        self.write({"state": "rejected", "decision_date": fields.Datetime.now()})
        for rec in self:
            rec.revision_id.state = "review"
            rec.revision_id.message_post(
                body="Approval rejected by %s." % rec.approver_id.display_name
            )
