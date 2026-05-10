from api.v1.repositories.brand_mention import (
    query_brand_mention_data as _brand_mention,
)
from api.v1.repositories.brand_mention import (
    query_brand_metrics as _brand_metrics,
)
from api.v1.repositories.brand_mention import (
    query_brand_platform_keyword_daily_mention_rates as _daily_rates,
)
from api.v1.repositories.brand_mention import (
    query_brand_platform_mention_data as _platform_mention,
)
from api.v1.repositories.brand_mention import (
    query_platform_metrics_by_brand as _platform_metrics,
)
from api.v1.repositories.citation import (
    query_citation_type_stats as _cite_type_stats,
)
from api.v1.repositories.citation import (
    query_citation_url_stats as _cite_url_stats,
)
from api.v1.repositories.citation import (
    query_domain_citation_rate as _domain_cite_rate,
)
from api.v1.repositories.citation import (
    query_domain_citation_summary as _domain_cite_summary,
)
from api.v1.repositories.citation import (
    query_post_citation_rate as _post_cite_rate,
)
from api.v1.repositories.connection import (
    DATABASE_CONFIG,  # noqa: F401
    SessionLocal,  # noqa: F401
    engine,
    get_db,  # noqa: F401
)
from api.v1.repositories.filter_metadata import (
    get_available_dates as _available_dates,
)
from api.v1.repositories.filter_metadata import (
    query_filter_metadata as _filter_metadata,
)
from api.v1.repositories.filter_metadata import (
    query_keyword_platform_brand_rates as _kw_platform_brand_rates,
)
from api.v1.utils.date_range import (
    get_date_range,  # noqa: F401
    get_previous_date_range,  # noqa: F401
)


def query_brand_mention_data(tenant_key, job_id, brand, timeframe, specific_date=None):
    return _brand_mention(engine, tenant_key, job_id, brand, timeframe, specific_date)


def query_brand_metrics(tenant_key, job_id, start_date, end_date, brand=None, platform=None):
    return _brand_metrics(engine, tenant_key, job_id, start_date, end_date, brand, platform)


def query_brand_platform_keyword_daily_mention_rates(
    tenant_key, job_id, brand, platform, keyword, start_date, end_date
):
    return _daily_rates(
        engine, tenant_key, job_id, brand, platform, keyword, start_date, end_date
    )


def query_brand_platform_mention_data(
    tenant_key, job_id, brand, category, keyword, timeframe, specific_date=None
):
    return _platform_mention(
        engine, tenant_key, job_id, brand, category, keyword, timeframe, specific_date
    )


def query_platform_metrics_by_brand(tenant_key, job_id, brand, start_date, end_date):
    return _platform_metrics(engine, tenant_key, job_id, brand, start_date, end_date)


def query_post_citation_rate(tenant_key, job_id, brand, start_date, end_date):
    return _post_cite_rate(engine, tenant_key, job_id, brand, start_date, end_date)


def query_domain_citation_rate(
    tenant_key, job_id, brand, start_date, end_date, keyword=None, platform=None
):
    return _domain_cite_rate(
        engine, tenant_key, job_id, brand, start_date, end_date, keyword, platform
    )


def query_citation_url_stats(tenant_key, job_id, keyword, domain, start_date, end_date):
    return _cite_url_stats(
        engine, tenant_key, job_id, keyword, domain, start_date, end_date
    )


def query_citation_type_stats(tenant_key, job_id, start_date, end_date):
    return _cite_type_stats(engine, tenant_key, job_id, start_date, end_date)


def query_domain_citation_summary(tenant_key, job_id, brand, start_date, end_date):
    return _domain_cite_summary(engine, tenant_key, job_id, brand, start_date, end_date)


def get_available_dates(tenant_key, job_id=None):
    return _available_dates(engine, tenant_key, job_id)


def query_filter_metadata(tenant_key, job_id, start_date=None, end_date=None):
    return _filter_metadata(engine, tenant_key, job_id, start_date, end_date)


def query_keyword_platform_brand_rates(tenant_key, job_id, start_date, end_date):
    return _kw_platform_brand_rates(engine, tenant_key, job_id, start_date, end_date)