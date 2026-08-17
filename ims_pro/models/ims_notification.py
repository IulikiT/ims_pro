from datetime import timedelta
from odoo import api, fields, models

class IMSNotificationRule(models.Model):
    _name = "ims.notification.rule"
    _description = "IMS Notification Rule"
    _order = "sequence, name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    event_type = fields.Selection([
        ("document_review", "Document Review Due"),
        ("approval_due", "Approval Due"),
        ("action_due", "IMS Action Due"),
    ], required=True, default="action_due")
    days_before = fields.Integer(
        string="Days Before Due Date",
        default=30,
        help="Use 0 for the due date itself."
    )
    create_activity = fields.Boolean(default=True)
    post_chatter = fields.Boolean(default=True)
    escalation_days = fields.Integer(
        string="Escalate After Overdue Days",
        default=7
    )

class IMSNotificationService(models.AbstractModel):
    _name = "ims.notification.service"
    _description = "IMS Notification and Escalation Service"

    @api.model
    def _activity_type(self):
        return self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)

    @api.model
    def _schedule_once(self, record, user, summary, due_date, note=None):
        if not record or not user or not due_date:
            return
        activity_type = self._activity_type()
        if not activity_type:
            return
        existing = self.env["mail.activity"].search([
            ("res_model", "=", record._name),
            ("res_id", "=", record.id),
            ("user_id", "=", user.id),
            ("summary", "=", summary),
            ("date_deadline", "=", due_date),
        ], limit=1)
        if existing:
            return
        record.activity_schedule(
            activity_type_id=activity_type.id,
            user_id=user.id,
            summary=summary,
            note=note or summary,
            date_deadline=due_date,
        )

    @api.model
    def run_daily_notifications(self):
        today = fields.Date.context_today(self)
        rules = self.env["ims.notification.rule"].search([("active", "=", True)])

        for rule in rules:
            trigger_date = today + timedelta(days=rule.days_before)

            if rule.event_type == "action_due":
                records = self.env["ims.action"].search([
                    ("due_date", "=", trigger_date),
                    ("state", "not in", ("done", "cancelled")),
                ])
                for rec in records:
                    summary = "IMS Action due: %s" % rec.reference
                    if rule.create_activity:
                        self._schedule_once(rec, rec.responsible_id, summary, rec.due_date)
                    if rule.post_chatter:
                        rec.message_post(body=summary)

                if rule.escalation_days >= 0:
                    overdue_date = today - timedelta(days=rule.escalation_days)
                    overdue = self.env["ims.action"].search([
                        ("due_date", "<=", overdue_date),
                        ("state", "not in", ("done", "cancelled")),
                    ])
                    managers = self.env.ref("ims_pro.group_ims_manager", raise_if_not_found=False)
                    manager_users = managers.all_user_ids if managers else self.env["res.users"]
                    for rec in overdue:
                        for user in manager_users:
                            self._schedule_once(
                                rec, user,
                                "ESCALATION: overdue IMS Action %s" % rec.reference,
                                today,
                                "The IMS action is overdue and requires escalation."
                            )

            elif rule.event_type == "approval_due":
                approvals = self.env["ims.document.approval"].search([
                    ("due_date", "=", trigger_date),
                    ("state", "in", ("pending", "requested")),
                ])
                for approval in approvals:
                    revision = approval.revision_id
                    summary = "Document approval due: %s Rev. %s" % (
                        revision.document_id.code, revision.revision
                    )
                    if rule.create_activity:
                        self._schedule_once(revision, approval.approver_id, summary, approval.due_date)
                    if rule.post_chatter:
                        revision.message_post(body=summary)

            elif rule.event_type == "document_review":
                revisions = self.env["ims.document.revision"].search([
                    ("state", "=", "active"),
                    ("review_date", "=", trigger_date),
                ])
                for rec in revisions:
                    summary = "Document review due: %s Rev. %s" % (
                        rec.document_id.code, rec.revision
                    )
                    owner = rec.document_id.owner_id
                    if rule.create_activity:
                        self._schedule_once(rec, owner, summary, rec.review_date)
                    if rule.post_chatter:
                        rec.message_post(body=summary)
