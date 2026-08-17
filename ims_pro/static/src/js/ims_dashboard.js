/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";


export class IMSProDashboard extends Component {
    static template = "ims_pro.IMSProDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            data: {
                kpis: {},
                nc_by_domain: {},
                heatmap: {},
                recent_actions: [],
                next_review: {},
                next_audit: {},
            },
        });

        this.modules = [
            { key: "documents", title: "Document Control", subtitle: "Library · Revisions · Approvals · Release", icon: "fa-file-text-o", action: "ims_pro.action_ims_document", group: "Control" },
            { key: "changes", title: "Change Control", subtitle: "Impact · Authorization · Implementation", icon: "fa-random", action: "ims_pro.action_ims_change", group: "Control" },
            { key: "risk", title: "Risk & Opportunities", subtitle: "Quality · OHS · Environment · ISMS", icon: "fa-exclamation-triangle", action: "ims_pro.action_ims_risk_case", group: "Risk & Improvement" },
            { key: "nc", title: "NC & Incidents", subtitle: "Quality · OHS · Environment", icon: "fa-bolt", action: "ims_pro.action_ims_nonconformity", group: "Risk & Improvement" },
            { key: "capa", title: "CAPA", subtitle: "Root Cause · Actions · Effectiveness", icon: "fa-check-circle-o", action: "ims_pro.action_ims_capa", group: "Risk & Improvement" },
            { key: "complaints", title: "Customer Complaints", subtitle: "Investigation · NC · CAPA · Response", icon: "fa-comments-o", action: "ims_pro.action_ims_complaint", group: "Risk & Improvement" },
            { key: "audits", title: "IMS Audits", subtitle: "Program · Plan · Findings · Follow-up", icon: "fa-search", action: "ims_pro.action_ims_audit", group: "Assurance" },
            { key: "review", title: "Management Review", subtitle: "Inputs · KPI · Decisions · Objectives", icon: "fa-line-chart", action: "ims_pro.action_ims_review", group: "Management" },
            { key: "objectives", title: "Objectives & KPI", subtitle: "Targets · Progress · Evaluation", icon: "fa-bullseye", action: "ims_pro.action_ims_objective", group: "Management" },
            { key: "compliance", title: "Compliance", subtitle: "Legal obligations · Evaluation · Evidence", icon: "fa-balance-scale", action: "ims_pro.action_ims_compliance", group: "Assurance" },
        ];

        onWillStart(async () => {
            this.state.data = await this.orm.call("ims.dashboard", "get_dashboard_data", [], {});
            this.state.loading = false;
        });
    }

    openAction(xmlid) {
        return this.action.doAction(xmlid);
    }

    openMyActions() {
        return this.action.doAction("ims_pro.action_ims_action");
    }

    openSearch() {
        return this.action.doAction("ims_pro.action_ims_global_search");
    }

    getHeatClass(prob, sev) {
        const score = Number(prob) * Number(sev);
        if (score >= 17) return "ims_heat_critical";
        if (score >= 10) return "ims_heat_high";
        if (score >= 5) return "ims_heat_medium";
        return "ims_heat_low";
    }

    getHeatCount(prob, sev) {
        const p = this.state.data.heatmap[String(prob)] || {};
        return p[String(sev)] || 0;
    }
}

registry.category("actions").add("ims_pro.dashboard", IMSProDashboard);
