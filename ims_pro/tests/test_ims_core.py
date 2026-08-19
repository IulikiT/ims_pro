from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestIMSProCore(TransactionCase):
    """Smoke/functional regression coverage for IMS Pro on Odoo 19."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.user
        cls.folder = cls.env["ims.document.folder"].create({"name": "Test IMS"})
        cls.category = cls.env["ims.document.category"].create({
            "name": "Procedure",
            "revision_scheme": "numeric",
            "default_review_months": 12,
        })
        cls.matrix = cls.env["ims.risk.matrix"].create({
            "name": "QA 5x5",
            "domain": "enterprise",
        })
        cls.prob = cls.env["ims.risk.scale"].create({
            "matrix_id": cls.matrix.id,
            "scale_type": "probability",
            "name": "Possible",
            "score": 3,
        })
        cls.sev = cls.env["ims.risk.scale"].create({
            "matrix_id": cls.matrix.id,
            "scale_type": "severity",
            "name": "Major",
            "score": 4,
        })
        cls.env["ims.risk.level"].create([
            {"matrix_id": cls.matrix.id, "name": "Low", "min_score": 1, "max_score": 4},
            {"matrix_id": cls.matrix.id, "name": "Medium", "min_score": 5, "max_score": 9},
            {"matrix_id": cls.matrix.id, "name": "High", "min_score": 10, "max_score": 16},
            {"matrix_id": cls.matrix.id, "name": "Critical", "min_score": 17, "max_score": 25},
        ])

    def test_required_xmlids_exist(self):
        for xmlid in (
            "ims_pro.action_ims_dashboard_client",
            "ims_pro.menu_ims_root",
            "ims_pro.action_ims_document",
            "ims_pro.action_ims_risk_case",
            "ims_pro.action_ims_capa",
            "ims_pro.action_ims_audit",
            "ims_pro.group_ims_user",
            "ims_pro.group_ims_manager",
            "ims_pro.group_ims_admin",
        ):
            self.assertTrue(self.env.ref(xmlid, raise_if_not_found=False), xmlid)

    def test_document_revision_release_and_immutability(self):
        doc = self.env["ims.document"].create({
            "code": "QA-PRO-001",
            "name": "QA Controlled Procedure",
            "folder_id": self.folder.id,
            "category_id": self.category.id,
            "owner_id": self.user.id,
        })
        rev = self.env["ims.document.revision"].create({
            "document_id": doc.id,
            "revision": "1",
            "required_approvals": 1,
        })
        approval = self.env["ims.document.approval"].create({
            "revision_id": rev.id,
            "approver_id": self.user.id,
            "state": "requested",
        })
        approval.action_approve()
        self.assertEqual(rev.state, "approved")
        rev.action_release()
        self.assertEqual(rev.state, "active")
        self.assertTrue(rev.effective_date)
        self.assertEqual(doc.current_revision_id, rev)
        with self.assertRaises(ValidationError):
            rev.write({"revision": "99"})

    def test_risk_scoring(self):
        project = self.env["ims.risk.project"].create({
            "name": "QA Enterprise Risk Project",
            "matrix_id": self.matrix.id,
        })
        hazard = self.env["ims.risk.hazard"].create({
            "project_id": project.id,
            "name": "QA Hazard",
        })
        case = self.env["ims.risk.case"].create({
            "title": "QA Risk Case",
            "hazard_id": hazard.id,
            "initial_probability_id": self.prob.id,
            "initial_severity_id": self.sev.id,
            "residual_probability_id": self.prob.id,
            "residual_severity_id": self.sev.id,
        })
        self.assertEqual(case.initial_score, 12)
        self.assertEqual(case.initial_level, "High")
        self.assertEqual(case.residual_score, 12)

    def test_action_overdue_search_and_close(self):
        action = self.env["ims.action"].create({
            "name": "QA Corrective Action",
            "responsible_id": self.user.id,
            "due_date": fields.Date.context_today(self.env.user) - timedelta(days=1),
        })
        self.assertTrue(action.is_overdue)
        self.assertIn(action, self.env["ims.action"].search([("is_overdue", "=", True)]))
        action.action_close()
        self.assertEqual(action.state, "done")
        self.assertFalse(action.is_overdue)

    def test_global_search_smoke(self):
        process = self.env["ims.process"].create({"code": "QA-041", "name": "QA Context Process"})
        wizard = self.env["ims.global.search"].create({"query": "QA Context"})
        wizard.action_search()
        self.assertTrue(wizard.result_ids.filtered(lambda r: r.model_name == "ims.process" and r.record_id == process.id))

    def test_notification_service_smoke(self):
        action = self.env["ims.action"].create({
            "name": "QA Notification Action",
            "responsible_id": self.user.id,
            "due_date": fields.Date.context_today(self.env.user),
        })
        self.env["ims.notification.rule"].create({
            "name": "QA Due Today",
            "event_type": "action_due",
            "days_before": 0,
            "create_activity": True,
            "post_chatter": False,
            "escalation_days": 7,
        })
        self.env["ims.notification.service"].run_daily_notifications()
        self.assertTrue(action.activity_ids)
