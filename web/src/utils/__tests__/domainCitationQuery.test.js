import assert from 'node:assert/strict';
import { buildDomainCitationQueryString } from '../domainCitationQuery.js';

const specificQuery = buildDomainCitationQueryString({
  tenantKey: 'tn_1b02b3ef4fbd',
  jobId: 'job_20260127_223236_989cc4db',
  brand: '学而思',
  timeframe: 'specific_day',
  startDate: '20260102',
  endDate: '20260131',
});

const specificParams = new URLSearchParams(specificQuery);
assert.equal(specificParams.get('tenant_key'), 'tn_1b02b3ef4fbd');
assert.equal(specificParams.get('job_id'), 'job_20260127_223236_989cc4db');
assert.equal(specificParams.get('brand'), '学而思');
assert.equal(specificParams.get('timeframe'), 'specific_day');
assert.equal(specificParams.get('start_date'), '20260102');
assert.equal(specificParams.get('end_date'), '20260131');
assert.equal(specificParams.get('date'), null);

const rangeQuery = buildDomainCitationQueryString({
  tenantKey: 'tn_1b02b3ef4fbd',
  jobId: 'job_20260127_223236_989cc4db',
  brand: '学而思',
  timeframe: '30days',
  startDate: '20260102',
  endDate: '20260131',
});

const rangeParams = new URLSearchParams(rangeQuery);
assert.equal(rangeParams.get('timeframe'), '30days');
assert.equal(rangeParams.get('start_date'), null);
assert.equal(rangeParams.get('end_date'), null);
