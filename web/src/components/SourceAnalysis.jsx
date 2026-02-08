import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Card, Typography, Tag, Table, Badge, theme, Flex, Button, Divider, Tooltip, Empty, Spin, Select, Popover } from 'antd';
import { Chart } from '@antv/g2';
import dayjs from 'dayjs';
import { 
  Download, 
  ExternalLink, 
  Globe, 
  FileText, 
  Filter,
  Info,
  TrendingUp,
  Hash
} from 'lucide-react';
import { CONFIG } from '@/config';
import { normalizeCitationTypeStats } from '@/utils/sourceAnalysis';

const { Title, Text } = Typography;

const { DEFAULT_TENANT_KEY, DEFAULT_JOB_ID, DEFAULT_BRAND } = CONFIG;

// --- Helpers ---

const parseDateInput = (value) => {
  if (!value) return null;
  const text = String(value);
  if (/^\d{8}$/.test(text)) {
    const parsed = dayjs(text, 'YYYYMMDD');
    return parsed.isValid() ? parsed : null;
  }
  const parsed = dayjs(text);
  return parsed.isValid() ? parsed : null;
};

const formatDateDisplay = (value) => {
  if (!value) return '';
  const parsed = dayjs.isDayjs(value) ? value : dayjs(value);
  if (!parsed.isValid()) return '';
  return parsed.format('YYYY-MM-DD');
};

const formatDateParam = (value) => {
  if (!value) return '';
  const parsed = dayjs.isDayjs(value) ? value : dayjs(value);
  if (!parsed.isValid()) return '';
  return parsed.format('YYYYMMDD');
};

const getRangeByTimeframe = (timeframe, dateParam) => {
  const today = dayjs();
  if (timeframe === 'yesterday') {
    const yesterday = today.subtract(1, 'day');
    return { startDate: yesterday, endDate: yesterday };
  }
  if (timeframe === 'specific_day') {
    const parsed = parseDateInput(dateParam);
    const day = parsed || today;
    return { startDate: day, endDate: day };
  }
  const days = timeframe === '30days' ? 30 : 7;
  return {
    startDate: today.subtract(days - 1, 'day'),
    endDate: today,
  };
};

const buildQueryString = (params) => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    searchParams.set(key, String(value));
  });
  return searchParams.toString();
};

const fetchJson = async (url, { signal } = {}) => {
  const response = await fetch(url, { method: 'GET', signal });
  if (!response.ok) {
    throw new Error(`请求失败(${response.status})`);
  }
  return response.json();
};

const clampPercent = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.max(0, Math.min(100, num));
};

const roundTwoDecimals = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.round(num * 100) / 100;
};

const normalizeListValue = (value) => {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || '').trim()).filter(Boolean);
  }
  const text = String(value || '');
  return text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
};

const buildSourceUrl = (domain) => {
  if (!domain) return '';
  const text = String(domain).trim();
  if (!text) return '';
  if (/^https?:\/\//i.test(text)) {
    return text;
  }
  return `https://${text}`;
};

// --- Components ---

const KeywordSection = ({ keywords = [], loading = false, selectedKeyword, onKeywordChange }) => {
  const { token } = theme.useToken();
  
  return (
    <Card 
      bordered={false} 
      styles={{ body: { padding: token.paddingLG } }}
      style={{ boxShadow: token.boxShadowTertiary, borderRadius: token.borderRadiusLG }}
    >
      <Spin spinning={loading}>
        <Flex vertical gap="middle">
          <Flex align="center" gap="small">
            <Hash size={20} color={token.colorPrimary} />
            <Title level={4} style={{ margin: 0, fontWeight: 700 }}>品牌关键词</Title>
            {selectedKeyword && (
              <Tag 
                closable 
                onClose={() => onKeywordChange?.('')}
                color="processing"
                style={{ marginLeft: token.marginSM }}
              >
                已选: {selectedKeyword}
              </Tag>
            )}
          </Flex>
          
          <Divider style={{ margin: '4px 0' }} />
          
          {keywords.length > 0 ? (
            <Flex wrap="wrap" gap="small">
              {keywords.map((kw) => {
                const isSelected = selectedKeyword === kw;
                return (
                  <Tag 
                    key={kw} 
                    bordered={false}
                    onClick={() => onKeywordChange?.(isSelected ? '' : kw)}
                    style={{ 
                      borderRadius: token.borderRadiusLG,
                      backgroundColor: isSelected ? token.colorPrimary : token.colorFillTertiary,
                      color: isSelected ? '#fff' : token.colorTextDescription,
                      padding: '4px 12px',
                      cursor: 'pointer',
                      transition: 'all 0.3s',
                      margin: 0
                    }}
                    className={!isSelected ? "hover:bg-blue-50 hover:text-blue-600" : ""}
                  >
                    {kw}
                  </Tag>
                );
              })}
            </Flex>
          ) : !loading && (
            <Empty description="暂无关键词" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </Flex>
      </Spin>
    </Card>
  );
};

const SourceAnalysisChart = ({
  displayDate,
  timeframeLabel = '按天',
  summary,
  stats,
  loading,
}) => {
  const { token } = theme.useToken();
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const chartData = useMemo(
    () =>
      stats.map((item) => ({
        category: 'all',
        type: item.type,
        value: item.value / 100,
      })),
    [stats],
  );
  const colorRange = useMemo(() => stats.map((item) => item.color), [stats]);

  useEffect(() => {
    if (!containerRef.current) return;

    containerRef.current.innerHTML = '';

    const chart = new Chart({
      container: containerRef.current,
      autoFit: true,
      height: 16,
      padding: 0,
      inset: 0, // 确保图表内部无任何边距
    });

    chart.data(chartData);

    chart
      .interval()
      .coordinate({ transform: [{ type: 'transpose' }] })
      .encode('x', 'category')
      .encode('y', 'value')
      .encode('color', 'type')
      .transform([{ type: 'stackY' }, { type: 'normalizeY' }])
      .scale('color', {
        range: colorRange,
      })
      .scale('x', {
        padding: 0,
      })
      .axis(false)
      .legend(false)
      .tooltip(false)
      .style('radius', 0)
      .style('stroke', '#fff')
      .style('lineWidth', 0)
      .label({
        text: 'value',
        position: 'inside',
        transform: [{ type: 'stackY' }, { type: 'normalizeY' }],
        formatter: (val) => val > 0.08 ? `${(val * 100).toFixed(0)}%` : '',
        style: {
          fill: '#fff',
          fontSize: 10,
          fontWeight: 600,
        },
      });

    chart.render();
    chartRef.current = chart;

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [chartData, colorRange]);

  return (
    <Card 
      bordered={false} 
      styles={{ body: { padding: token.paddingLG } }}
      style={{ boxShadow: token.boxShadowTertiary, borderRadius: token.borderRadiusLG }}
    >
      <Flex vertical gap="small" style={{ marginBottom: token.marginLG }}>
        <Flex align="center" gap="small">
          <TrendingUp size={20} color={token.colorPrimary} />
          <Title level={4} style={{ margin: 0, fontWeight: 700 }}>信源分析</Title>
          <Tooltip title="基于大模型引用的信源分布比例">
            <Info size={14} color={token.colorTextPlaceholder} style={{ cursor: 'help' }} />
          </Tooltip>
        </Flex>
        
        <Flex gap="large" align="center" style={{ paddingLeft: 28 }}>
          {[
            { label: timeframeLabel, value: displayDate },
            { label: 'Prompt 总数', value: summary?.conversations ?? 0 },
            { label: '引用信源数', value: summary?.totalRows ?? 0 },
          ].map(item => (
            <Flex key={item.label} align="center" gap="xs">
              <Text type="secondary" style={{ fontSize: token.fontSizeSM }}>{item.label}：</Text>
              <Text strong style={{ fontSize: token.fontSize }}>
                {loading ? '加载中' : item.value}
              </Text>
            </Flex>
          ))}
        </Flex>
      </Flex>

      {/* G2 百分比堆叠条形图容器 */}
      <div style={{ 
        marginBottom: token.marginLG, 
        paddingLeft: 28, 
        paddingRight: token.paddingLG,
        height: 16
      }}>
        <div 
          ref={containerRef} 
          style={{ 
            width: '100%', 
            height: '100%', 
            borderRadius: 8, 
            overflow: 'hidden', 
            backgroundColor: token.colorFillTertiary,
            display: 'flex',
            alignItems: 'center'
          }} 
        />
      </div>

      <Flex wrap="wrap" justify="center" gap="xl">
        {stats.map((item) => (
          <Flex key={item.type} align="center" gap="small" style={{ 
            padding: '4px 12px', 
            borderRadius: token.borderRadiusSM,
            transition: 'all 0.2s',
            cursor: 'default'
          }} className="hover:bg-gray-50">
            <Badge color={item.color} />
            <Text strong style={{ color: token.colorTextHeading }}>{item.type}</Text>
            <Text type="secondary" style={{ minWidth: 40 }}>{item.value}%</Text>
          </Flex>
        ))}
      </Flex>
    </Card>
  );
};

const MediaListTable = ({
  rows = [],
  loading = false,
  error = '',
  platformOptions = [],
  selectedPlatform,
  onPlatformChange,
}) => {
  const { token } = theme.useToken();
  const normalizedPlatformOptions = useMemo(() => {
    const fallback = ['deepseek', '千问', '豆包', '元宝'];
    const base = platformOptions.length ? platformOptions : fallback;
    return Array.from(new Set(base.filter(Boolean))).map((item) => ({
      label: item,
      value: item,
    }));
  }, [platformOptions]);

  const columns = [
    {
      title: '引用来源',
      key: 'source',
      width: 280,
      render: (_, record) => (
        <Flex vertical gap={2}>
          <Flex align="center" gap="small">
            <Globe size={14} color={token.colorTextDescription} />
            <Text strong>{record.sourceName}</Text>
          </Flex>
          <Text type="secondary" style={{ fontSize: token.fontSizeSM }} copyable>{record.domain}</Text>
        </Flex>
      ),
    },
    {
      title: '品牌关键词',
      dataIndex: 'keyword',
      key: 'keyword',
      render: (text) => {
        const items = normalizeListValue(text);
        if (!items.length) return <Text type="secondary">--</Text>;
        return (
          <Flex wrap="wrap" gap="small">
            {items.map((item) => (
              <Tag key={item} bordered={false} icon={<Hash size={10} />} style={{ borderRadius: 4 }}>
                {item}
              </Tag>
            ))}
          </Flex>
        );
      },
    },
    {
      title: '内容类型',
      dataIndex: 'contentType',
      key: 'contentType',
      render: (text) => {
        const colors = { '新闻': 'blue', '论坛': 'cyan', '博客': 'purple', '评论': 'orange' };
        const items = normalizeListValue(text);
        if (!items.length) return <Text type="secondary">--</Text>;
        return (
          <Flex wrap="wrap" gap="small">
            {items.map((item) => (
              <Tag key={item} color={colors[item] || 'default'} bordered={false}>{item}</Tag>
            ))}
          </Flex>
        );
      },
    },
    {
      title: '大模型平台',
      dataIndex: 'platform',
      key: 'platform',
      render: (text) => {
        const items = normalizeListValue(text);
        if (!items.length) return <Text type="secondary">--</Text>;
        return (
          <Flex wrap="wrap" gap="small">
            {items.map((item) => (
              <Tag key={item} color="processing" bordered={false}>{item}</Tag>
            ))}
          </Flex>
        );
      },
    },
    {
      title: '引用率',
      dataIndex: 'citationRate',
      key: 'citationRate',
      sorter: (a, b) => a.citationRate - b.citationRate,
      render: (value) => {
        let color = token.colorSuccess;
        if (value < 30) color = token.colorTextDescription;
        else if (value > 70) color = token.colorWarning;
        
        return (
          <Flex align="center" gap="small">
            <div style={{ width: 60, height: 6, background: token.colorFillTertiary, borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${value}%`, height: '100%', background: color, borderRadius: 3 }} />
            </div>
            <Text strong style={{ color, minWidth: 40, fontSize: token.fontSizeSM }}>{value}%</Text>
          </Flex>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Tooltip title="查看原文">
          <Button 
            type="text" 
            icon={<ExternalLink size={16} />} 
            href={record.sourceUrl || undefined} 
            target="_blank" 
            disabled={!record.sourceUrl}
          />
        </Tooltip>
      ),
    },
  ];

  return (
    <Card 
      bordered={false} 
      styles={{ body: { padding: 0 } }}
      style={{ boxShadow: token.boxShadowTertiary, borderRadius: token.borderRadiusLG, overflow: 'hidden' }}
    >
      <Flex justify="space-between" align="center" style={{ padding: token.paddingLG, borderBottom: `1px solid ${token.colorBorderSecondary}` }}>
        <Flex align="center" gap="small">
          <FileText size={20} color={token.colorPrimary} />
          <Title level={4} style={{ margin: 0, fontWeight: 700 }}>引用媒介列表</Title>
        </Flex>
        <Flex gap="small">
          <Popover
            trigger="click"
            placement="bottomRight"
            content={
              <Flex vertical gap="small" style={{ minWidth: 220 }}>
                <Text type="secondary">大模型平台</Text>
                <Select
                  allowClear
                  placeholder="全部平台"
                  value={selectedPlatform || undefined}
                  onChange={(value) => onPlatformChange?.(value || '')}
                  options={normalizedPlatformOptions}
                />
              </Flex>
            }
          >
            <Button icon={<Filter size={14} />}>高级筛选</Button>
          </Popover>
          <Button type="primary" icon={<Download size={14} />}>导出报告</Button>
        </Flex>
      </Flex>
      {error ? (
        <Flex align="center" gap="small" style={{ padding: token.paddingLG, color: token.colorError }}>
          <Text type="danger">{error}</Text>
        </Flex>
      ) : null}
      <Table 
        columns={columns} 
        dataSource={rows} 
        rowKey={(record) => record.key || record.domain || record.sourceUrl}
        pagination={{ 
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`
        }}
        loading={loading}
        size="middle"
        locale={{
          emptyText: error ? '加载失败，请稍后再试' : '暂无数据',
        }}
      />
    </Card>
  );
};

export default function SourceAnalysis({ 
  timeframe = '30days',
  date = '',
  endDate = '',
  tenantKey = DEFAULT_TENANT_KEY,
  jobId = DEFAULT_JOB_ID,
  brand = DEFAULT_BRAND,
}) {
  const [keywords, setKeywords] = useState([]);
  const [selectedKeyword, setSelectedKeyword] = useState('');
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [platformOptions, setPlatformOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [citationSummary, setCitationSummary] = useState({ totalRows: 0, conversations: 0 });
  const [citationStats, setCitationStats] = useState([]);
  const [citationLoading, setCitationLoading] = useState(false);
  const [citationError, setCitationError] = useState('');
  const citationAbortRef = useRef(null);
  const mediaAbortRef = useRef(null);
  const [mediaRows, setMediaRows] = useState([]);
  const [mediaLoading, setMediaLoading] = useState(false);
  const [mediaError, setMediaError] = useState('');

  const dateRange = useMemo(() => {
    if (timeframe === 'specific_day') {
      const start = parseDateInput(date) || dayjs();
      const end = parseDateInput(endDate) || start;
      const normalizedEnd = end.isBefore(start, 'day') ? start : end;
      return { startDate: start, endDate: normalizedEnd };
    }
    return getRangeByTimeframe(timeframe, date);
  }, [timeframe, date, endDate]);

  const displayDate = useMemo(() => {
    const start = formatDateDisplay(dateRange.startDate);
    const end = formatDateDisplay(dateRange.endDate);
    return start === end ? start : `${start} ~ ${end}`;
  }, [dateRange]);

  const startDateParam = useMemo(
    () => formatDateParam(dateRange.startDate),
    [dateRange.startDate],
  );
  const endDateParam = useMemo(
    () => formatDateParam(dateRange.endDate),
    [dateRange.endDate],
  );

  const timeframeLabel = useMemo(() => {
    if (timeframe === 'yesterday') return '昨天';
    if (timeframe === '7days') return '最近7天';
    if (timeframe === '30days') return '最近30天';
    return '指定日期';
  }, [timeframe]);

  useEffect(() => {
    const controller = new AbortController();
    
    const fetchMetadata = async () => {
      setLoading(true);
      setError(null);
      try {
        const queryParams = buildQueryString({
          tenant_key: tenantKey,
          job_id: jobId,
          start_date: startDateParam,
          end_date: endDateParam,
        });

        const result = await fetchJson(`/api/v1/dashboard/filter-metadata?${queryParams}`, {
          signal: controller.signal
        });

        if (result?.code === 200 && result.data) {
          setKeywords(result.data.keywords || []);
          setPlatformOptions(result.data.platforms || []);
        } else {
          throw new Error(result?.message || '获取元数据失败');
        }
      } catch (err) {
        if (err.name === 'AbortError') return;
        console.error('Fetch filter metadata error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMetadata();

    return () => {
      controller.abort();
    };
  }, [tenantKey, jobId, startDateParam, endDateParam]);

  useEffect(() => {
    if (selectedKeyword && !keywords.includes(selectedKeyword)) {
      setSelectedKeyword('');
    }
  }, [keywords, selectedKeyword]);

  useEffect(() => {
    if (!tenantKey || !jobId) {
      setCitationSummary({ totalRows: 0, conversations: 0 });
      setCitationStats([]);
      return;
    }

    if (citationAbortRef.current) {
      citationAbortRef.current.abort();
    }

    const controller = new AbortController();
    citationAbortRef.current = controller;

    const run = async () => {
      setCitationLoading(true);
      setCitationError('');
      try {
        const queryParams = buildQueryString({
          tenant_key: tenantKey,
          job_id: jobId,
          timeframe,
          start_date: timeframe === 'specific_day' ? startDateParam : undefined,
          end_date: timeframe === 'specific_day' ? endDateParam : undefined,
        });

        const result = await fetchJson(`/api/v1/dashboard/citation-type-stats?${queryParams}`, {
          signal: controller.signal,
        });

        if (result?.status && result.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const normalized = normalizeCitationTypeStats(result, { maxItems: 5 });
        setCitationSummary(normalized.summary);
        setCitationStats(normalized.stats);
        setCitationLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setCitationSummary({ totalRows: 0, conversations: 0 });
        setCitationStats([]);
        setCitationError(err?.message || '数据加载失败');
        setCitationLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [tenantKey, jobId, timeframe, startDateParam, endDateParam]);

  useEffect(() => {
    if (!tenantKey || !jobId || !brand) {
      setMediaRows([]);
      setMediaError('');
      return;
    }

    if (mediaAbortRef.current) {
      mediaAbortRef.current.abort();
    }

    const controller = new AbortController();
    mediaAbortRef.current = controller;

    const run = async () => {
      setMediaLoading(true);
      setMediaError('');
      try {
        const queryParams = buildQueryString({
          tenant_key: tenantKey,
          job_id: jobId,
          brand,
          timeframe,
          start_date: timeframe === 'specific_day' ? startDateParam : undefined,
          end_date: timeframe === 'specific_day' ? endDateParam : undefined,
          keyword: selectedKeyword || undefined,
          platform: selectedPlatform || undefined,
        });

        const result = await fetchJson(`/api/v1/dashboard/citation-domain-stats?${queryParams}`, {
          signal: controller.signal,
        });

        if (result?.status && result.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const list = Array.isArray(result?.domain_distribution) ? result.domain_distribution : [];
        const normalized = list
          .map((item, index) => {
            const domain = item?.domain ?? '';
            const chineseName = item?.chinese_name ?? item?.chineseName ?? '';
            const keywordValue = item?.keywords ?? item?.keyword ?? '';
            const contentTypeValue = item?.content_types ?? item?.contentTypes ?? '';
            const platformValue = item?.platforms ?? item?.platform ?? '';
            const rawRate =
              item?.['domain-citation-rate'] ??
              item?.domain_citation_rate ??
              item?.domainCitationRate ??
              0;
            const citationRate = roundTwoDecimals(clampPercent(rawRate));
            return {
              key: `${domain || 'row'}-${index}`,
              domain,
              sourceName: chineseName || domain || '--',
              sourceUrl: buildSourceUrl(domain),
              keyword: keywordValue,
              contentType: contentTypeValue,
              platform: platformValue,
              citationRate,
            };
          })
          .filter((item) => item.domain);

        setMediaRows(normalized);
        setMediaLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setMediaRows([]);
        setMediaError(err?.message || '数据加载失败');
        setMediaLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [
    tenantKey,
    jobId,
    brand,
    timeframe,
    startDateParam,
    endDateParam,
    selectedKeyword,
    selectedPlatform,
  ]);

  return (
    <Flex vertical gap="large">
      <KeywordSection
        keywords={keywords}
        loading={loading}
        selectedKeyword={selectedKeyword}
        onKeywordChange={setSelectedKeyword}
      />
      <SourceAnalysisChart
        displayDate={displayDate}
        timeframeLabel={timeframeLabel}
        summary={citationSummary}
        stats={citationStats}
        loading={citationLoading}
      />
      <MediaListTable
        rows={mediaRows}
        loading={mediaLoading}
        error={mediaError}
        platformOptions={platformOptions}
        selectedPlatform={selectedPlatform}
        onPlatformChange={setSelectedPlatform}
      />
    </Flex>
  );
}


