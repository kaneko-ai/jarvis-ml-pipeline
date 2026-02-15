(function (global) {
  const PERSONAL_CORE_API_MAP = {
    health: "/api/health",
    health_cron: "/api/health/cron",
    capabilities: "/api/capabilities",
    runs_list: "/api/runs",
    runs_detail: "/api/runs/:runId",
    runs_files: "/api/runs/:runId/files",
    runs_events: "/api/runs/:runId/events",
    qa_report: "/api/qa/report",
    feedback_risk: "/api/feedback/risk",
    feedback_import: "/api/feedback/import",
    decision_simulate: "/api/decision/simulate",
  };

  global.adapter_manifest_personal = {
    profile: "personal-core",
    apis: Object.keys(PERSONAL_CORE_API_MAP),
  };

  global.api_map_v1 = {
    ...(global.api_map_v1 || {}),
    ...PERSONAL_CORE_API_MAP,
  };
})(window);
