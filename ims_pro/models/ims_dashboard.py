from odoo import api, fields, models


class IMSDashboard(models.TransientModel):
    _name = "ims.dashboard"
    _description = "IMS Pro Dashboard"

    @api.model
    def get_dashboard_data(self):
        today = fields.Date.context_today(self)

        open_action_domain = [("state", "not in", ("done", "cancelled"))]
        overdue_action_domain = open_action_domain + [("due_date", "<", today)]

        # My work
        my_open = self.env["ims.action"].search_count(
            open_action_domain + [("responsible_id", "=", self.env.user.id)]
        )
        my_overdue = self.env["ims.action"].search_count(
            overdue_action_domain + [("responsible_id", "=", self.env.user.id)]
        )

        # Approvals waiting for current user
        pending_approvals = self.env["ims.document.approval"].search_count([
            ("approver_id", "=", self.env.user.id),
            ("state", "in", ("pending", "requested")),
        ])

        # Core indicators
        kpis = {
            "active_documents": self.env["ims.document.revision"].search_count([("state", "=", "active")]),
            "pending_approvals": pending_approvals,
            "overdue_actions": self.env["ims.action"].search_count(overdue_action_domain),
            "open_changes": self.env["ims.change"].search_count([
                ("state", "not in", ("closed", "rejected", "cancelled"))
            ]),
            "high_risks": self.env["ims.risk.case"].search_count([
                ("residual_level", "in", ("HIGH", "CRITICAL")),
                ("state", "!=", "closed"),
            ]),
            "open_nc": self.env["ims.nonconformity"].search_count([
                ("state", "not in", ("closed", "cancelled"))
            ]),
            "open_capa": self.env["ims.capa"].search_count([("state", "!=", "closed")]),
            "open_findings": self.env["ims.audit.finding"].search_count([("state", "!=", "closed")]),
            "open_complaints": self.env["ims.complaint"].search_count([("state", "!=", "closed")]),
            "my_open": my_open,
            "my_overdue": my_overdue,
        }

        # Domain composition for universal NC/Incident register
        nc_by_domain = {}
        for key, _label in self.env["ims.nonconformity"]._fields["domain"].selection:
            nc_by_domain[key] = self.env["ims.nonconformity"].search_count([
                ("domain", "=", key),
                ("state", "not in", ("closed", "cancelled")),
            ])

        # Risk heatmap 5x5: P score x S score, using the active/current assessment.
        heatmap = {str(p): {str(s): 0 for s in range(1, 6)} for p in range(1, 6)}
        risks = self.env["ims.risk.case"].search([("state", "!=", "closed")])
        for risk in risks:
            prob = risk.residual_probability_id.score or risk.initial_probability_id.score or 0
            sev = risk.residual_severity_id.score or risk.initial_severity_id.score or 0
            if 1 <= prob <= 5 and 1 <= sev <= 5:
                heatmap[str(prob)][str(sev)] += 1

        # Recent actions
        recent_actions = []
        for rec in self.env["ims.action"].search(
            [("responsible_id", "=", self.env.user.id)],
            order="is_overdue desc, due_date asc, id desc",
            limit=7,
        ):
            recent_actions.append({
                "id": rec.id,
                "reference": rec.reference,
                "name": rec.name,
                "source_type": rec.source_type,
                "due_date": fields.Date.to_string(rec.due_date) if rec.due_date else "",
                "state": rec.state,
                "is_overdue": rec.is_overdue,
            })

        # Review / audit snapshot
        next_review = self.env["ims.review"].search(
            [("state", "!=", "closed")], order="review_date asc, id asc", limit=1
        )
        next_audit = self.env["ims.audit"].search(
            [("state", "not in", ("completed", "closed"))],
            order="planned_date asc, id asc", limit=1
        )

        return {
            "kpis": kpis,
            "nc_by_domain": nc_by_domain,
            "heatmap": heatmap,
            "recent_actions": recent_actions,
            "next_review": {
                "name": next_review.name or "",
                "title": next_review.title or "",
                "date": fields.Date.to_string(next_review.review_date) if next_review.review_date else "",
            } if next_review else {},
            "next_audit": {
                "name": next_audit.name or "",
                "title": next_audit.title or "",
                "date": fields.Date.to_string(next_audit.planned_date) if next_audit.planned_date else "",
            } if next_audit else {},
        }
