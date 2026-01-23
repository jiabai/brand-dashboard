#!/usr/bin/env python3
import uuid

raw_uuid = str(uuid.uuid4()).replace("-", "")
short_uuid = raw_uuid[:12]
tenant_key = f"tn_{short_uuid}"
print(tenant_key)