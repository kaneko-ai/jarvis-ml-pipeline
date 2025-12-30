export const ADAPTER_REQUIREMENTS = {
    "core": [
        "capabilities",
        "health",
        "runs_list",
        "run_detail",
        "run_files",
        "run_file_get"
    ],
    "research": ["research_rank", "research_paper"],
    "qa": ["qa_report"],
    "submission": ["submission_build", "submission_latest"],
    "decision": ["decision_simulate"],
    "finance": ["finance_optimize", "finance_simulate", "finance_download"],
    "dashboard": [
        "run_manifest",
        "jobs",
        "job_detail",
        "job_events",
        "search",
        "upload_pdf",
        "upload_bibtex",
        "upload_zip"
    ]
};
