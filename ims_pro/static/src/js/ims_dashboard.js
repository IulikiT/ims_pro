/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class IMSProDashboard extends Component {
    static template = "ims_pro.IMSProDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");

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
            { key: "documents", title: "Document Control", subtitle: "Library, revisions, approvals and release", icon: "fa-file-text-o", action: "ims_pro.action_ims_document", group: "Control" },
            { key: "changes", title: "Change Control", subtitle: "Impact, authorization and implementation", icon: "fa-random", action: "ims_pro.action_ims_change", group: "Control" },
            { key: "risk", title: "Risk & Opportunities", subtitle: "Quality, OHS, Environment and ISMS", icon: "fa-exclamation-triangle", action: "ims_pro.action_ims_risk_case", group: "Risk & Improvement" },
            { key: "nc", title: "NC & Incidents", subtitle: "Quality, OHS and Environment", icon: "fa-bolt", action: "ims_pro.action_ims_nonconformity", group: "Risk & Improvement" },
            { key: "capa", title: "CAPA", subtitle: "Root cause, actions and effectiveness", icon: "fa-check-circle-o", action: "ims_pro.action_ims_capa", group: "Risk & Improvement" },
            { key: "complaints", title: "Customer Complaints", subtitle: "Investigation, NC, CAPA and response", icon: "fa-comments-o", action: "ims_pro.action_ims_complaint", group: "Risk & Improvement" },
            { key: "audits", title: "IMS Audits", subtitle: "Program, plan, findings and follow-up", icon: "fa-search", action: "ims_pro.action_ims_audit", group: "Assurance" },
            { key: "review", title: "Management Review", subtitle: "Inputs, KPI, decisions and objectives", icon: "fa-line-chart", action: "ims_pro.action_ims_review", group: "Management" },
            { key: "objectives", title: "Objectives & KPI", subtitle: "Targets, progress and evaluation", icon: "fa-bullseye", action: "ims_pro.action_ims_objective", group: "Management" },
            { key: "compliance", title: "Compliance", subtitle: "Legal obligations, evaluation and evidence", icon: "fa-balance-scale", action: "ims_pro.action_ims_compliance", group: "Assurance" },
        ];

        // OWL template callbacks can be invoked without a JS `this` context.
        // Keep all click handlers as lexical closures so the Odoo action service
        // is always available and dashboard navigation cannot fail on binding.
        this.openAction = async (xmlid) => {
            if (!xmlid) {
                this.notification.add("The requested IMS action is not configured.", { type: "warning" });
                return;
            }
            try {
                return await this.actionService.doAction(xmlid);
            } catch (error) {
                this.notification.add("Unable to open this IMS workspace. Please contact the IMS administrator.", { type: "danger" });
                throw error;
            }
        };
        this.openMyActions = () => this.openAction("ims_pro.action_ims_action");
        this.openSearch = () => this.openAction("ims_pro.action_ims_global_search");

        onWillStart(async () => {
            this.state.data = await this.orm.call("ims.dashboard", "get_dashboard_data", [], {});
            this.state.loading = false;
        });
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
