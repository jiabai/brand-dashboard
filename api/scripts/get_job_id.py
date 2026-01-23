#!/usr/bin/env python3

import datetime
import uuid


def generate_job_id() -> str:
    """Generate job_id in format: job_YYYYMMDD_HHMMSS_<process_id>"""
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    unique_suffix = str(uuid.uuid4())[:8]
    return f"job_{timestamp}_{unique_suffix}"

job_id = generate_job_id()
print(job_id)
