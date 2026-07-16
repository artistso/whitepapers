"""Access to the packaged analysis-report JSON Schema."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def load_analysis_report_schema() -> dict[str, Any]:
    """Load the Draft 2020-12 analysis-report schema shipped with PSIV."""

    resource = files("phase_space_validator").joinpath(
        "schemas/analysis-report-v1.schema.json"
    )
    return json.loads(resource.read_text(encoding="utf-8"))
