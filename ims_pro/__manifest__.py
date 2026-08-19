{
    "name": "IMS Pro",
    "summary": "Integrated Management System for Odoo 19",
    "description": "Commercial Integrated Management System for Quality, Environment, OH&S and Information Security.",
    "version": "19.0.1.0.2",
    "category": "Operations/IMS",
    "author": "Promotive IT System SRL",
    "maintainer": "Promotive IT System SRL",
    "license": "OPL-1",
    "application": True,
    "installable": True,
    "depends": ["base", "web", "mail", "hr", "documents", "contacts"],
    "data": [
        "security/ims_pro_security.xml",
        "security/ir.model.access.csv",
        "data/ims_sequence.xml",
        "data/ims_cron.xml",

        # Dashboard client action must be registered before the root menu references it.
        "views/ims_dashboard_views.xml",
        "views/ims_root_menu.xml",
        "views/ims_process_views.xml",
        "views/ims_action_views.xml",
        "views/ims_standard_views.xml",
        "views/ims_document_views.xml",
        "views/ims_notification_views.xml",
        "views/ims_global_search_views.xml",

        "views/ims_change_views.xml",
        "views/ims_risk_views.xml",
        "views/ims_nonconformity_views.xml",
        "views/ims_complaint_views.xml",
        "views/ims_capa_views.xml",
        "views/ims_supplier_views.xml",
        "views/ims_audit_views.xml",
        "views/ims_review_views.xml",
        "views/ims_compliance_views.xml",
        "views/ims_objective_views.xml",
        "views/ims_visual_views.xml",

        "report/ims_document_report.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "ims_pro/static/src/scss/ims_pro.scss",
            "ims_pro/static/src/js/ims_dashboard.js",
            "ims_pro/static/src/xml/ims_dashboard.xml"
        ]
    },
    "demo": [
        "demo/ims_demo.xml",
        "demo/ims_demo_full.xml"
    ]
}
