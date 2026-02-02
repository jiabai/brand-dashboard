import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Empty, Table, Progress, Card, Tag, Space, Typography, Tooltip } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import { CONFIG } from '@/config';

const { Text } = Typography;
const { DEFAULT_TENANT_KEY, DEFAULT_JOB_ID } = CONFIG;

const COLUMN_WIDTH_STORAGE_KEY = 'BrandShareOfVoiceTable:columnWidths';
const MIN_COLUMN_WIDTH = 96;
const MAX_COLUMN_WIDTH = 720;

const buildQueryString = (params) => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    if (String(value) === '') return;
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

const ResizableHeaderCell = ({ onResize, width, style, children, ...restProps }) => {
  const handleMouseDown = (event) => {
    if (!onResize) return;
    event.preventDefault();
    event.stopPropagation();

    const startX = event.clientX;
    const startWidth = Number(width) || 0;

    const prevCursor = document.body.style.cursor;
    const prevUserSelect = document.body.style.userSelect;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const handleMouseMove = (moveEvent) => {
      const nextWidth = Math.max(
        MIN_COLUMN_WIDTH,
        Math.min(MAX_COLUMN_WIDTH, startWidth + (moveEvent.clientX - startX)),
      );
      onResize(nextWidth);
    };

    const handleMouseUp = () => {
      document.body.style.cursor = prevCursor;
      document.body.style.userSelect = prevUserSelect;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <th
      {...restProps}
      style={{
        ...style,
        width,
        position: 'relative',
      }}
    >
      {children}
      {!!onResize && (
        <div
          role="separator"
          aria-orientation="vertical"
          onMouseDown={handleMouseDown}
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            height: '100%',
            width: 10,
            cursor: 'col-resize',
            userSelect: 'none',
            touchAction: 'none',
            zIndex: 1,
          }}
        />
      )}
    </th>
  );
};

const BrandShareOfVoiceTable = ({
  timeframe = '7days',
  date = '',
  tenantKey = DEFAULT_TENANT_KEY,
  jobId = DEFAULT_JOB_ID,
}) => {
  const abortControllerRef = useRef(null);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [columnWidths, setColumnWidths] = useState(() => {
    try {
      const raw = window.localStorage.getItem(COLUMN_WIDTH_STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (_) {
      return {};
    }
  });

  const queryString = useMemo(
    () =>
      buildQueryString({
        tenant_key: tenantKey,
        job_id: jobId,
        timeframe,
        date: timeframe === 'specific_day' ? date : '',
      }),
    [tenantKey, jobId, timeframe, date],
  );

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const run = async () => {
      try {
        setLoading(true);
        setError('');
        const result = await fetchJson(
          `/api/v1/dashboard/keyword-platform-brand-rates?${queryString}`,
          { signal: controller.signal },
        );

        if (result?.status && result.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const list = Array.isArray(result?.data) ? result.data : [];

        const normalized = list
          .map((item) => {
            const keyword = item?.keyword;
            const platform = item?.platform;
            const brand = item?.brand;
            const mentionRate = Number(item?.mention_rate ?? 0);
            const firstMentionRate = Number(item?.first_mention_rate ?? 0);
            return {
              keyword,
              platform,
              brand,
              mention_rate: Number.isFinite(mentionRate) ? mentionRate : 0,
              first_mention_rate: Number.isFinite(firstMentionRate) ? firstMentionRate : 0,
            };
          })
          .filter((item) => item.keyword && item.platform && item.brand);

        setRows(normalized);
        setLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setRows([]);
        setError(err?.message || '数据加载失败');
        setLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [queryString]);

  const keywordFilters = useMemo(() => {
    const keywords = [...new Set(rows.map((item) => item.keyword).filter(Boolean))];
    return keywords.map(k => ({ text: k, value: k }));
  }, [rows]);

  const platformFilters = useMemo(() => {
    const platforms = [...new Set(rows.map((item) => item.platform).filter(Boolean))];
    return platforms.map(p => ({ text: p, value: p }));
  }, [rows]);

  const setColumnWidth = useCallback((key, nextWidth) => {
    const width = Math.max(MIN_COLUMN_WIDTH, Math.min(MAX_COLUMN_WIDTH, Math.round(nextWidth)));
    setColumnWidths((prev) => {
      const next = { ...prev, [key]: width };
      try {
        window.localStorage.setItem(COLUMN_WIDTH_STORAGE_KEY, JSON.stringify(next));
      } catch (_) {
        // ignore
      }
      return next;
    });
  }, []);

  const handleResize = useCallback(
    (key) => (nextWidth) => {
      setColumnWidth(key, nextWidth);
    },
    [setColumnWidth],
  );

  const columns = useMemo(() => {
    const defs = [
      {
        title: 'Platform',
        dataIndex: 'platform',
        key: 'platform',
        filters: platformFilters,
        onFilter: (value, record) => record.platform === value,
        render: (text) => <Tag color="blue">{text}</Tag>,
        width: columnWidths.platform ?? 140,
      },
      {
        title: 'Keyword',
        dataIndex: 'keyword',
        key: 'keyword',
        filters: keywordFilters,
        onFilter: (value, record) => record.keyword === value,
        render: (text) => <Text strong>{text}</Text>,
        width: columnWidths.keyword ?? 240,
      },
      {
        title: 'Brand',
        dataIndex: 'brand',
        key: 'brand',
        render: (text) => <Text>{text}</Text>,
        width: columnWidths.brand ?? 200,
      },
      {
        title: (
          <Space>
            Mention Rate
            <Tooltip title="Percentage of conversations where the brand was mentioned">
              <InfoCircleOutlined style={{ color: 'rgba(0,0,0,0.45)' }} />
            </Tooltip>
          </Space>
        ),
        dataIndex: 'mention_rate',
        key: 'mention_rate',
        sorter: (a, b) => a.mention_rate - b.mention_rate,
        defaultSortOrder: 'descend',
        render: (value) => (
          <Space direction="vertical" style={{ width: '100%' }} size={0}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>{(value * 100).toFixed(2)}%</Text>
            </div>
            <Progress 
              percent={value * 100} 
              showInfo={false} 
              size="small" 
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
          </Space>
        ),
        width: columnWidths.mention_rate ?? 200,
      },
      {
        title: (
          <Space>
            First Mention Rate
            <Tooltip title="Percentage of conversations where the brand was mentioned first">
              <InfoCircleOutlined style={{ color: 'rgba(0,0,0,0.45)' }} />
            </Tooltip>
          </Space>
        ),
        dataIndex: 'first_mention_rate',
        key: 'first_mention_rate',
        sorter: (a, b) => a.first_mention_rate - b.first_mention_rate,
        render: (value) => (
          <Space direction="vertical" style={{ width: '100%' }} size={0}>
             <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>{(value * 100).toFixed(2)}%</Text>
            </div>
            <Progress 
              percent={value * 100} 
              showInfo={false} 
              size="small" 
              strokeColor="#faad14"
            />
          </Space>
        ),
        width: columnWidths.first_mention_rate ?? 200,
      },
    ];

    return defs.map((col) => ({
      ...col,
      onHeaderCell: () => ({
        width: col.width,
        onResize: handleResize(col.key),
      }),
    }));
  }, [columnWidths, handleResize, keywordFilters, platformFilters]);

  return (
    <Card 
      bordered={false}
      style={{ margin: 24, borderRadius: 8 }}
    >
      {!!error && (
        <div style={{ marginBottom: 12 }}>
          <Alert type="error" showIcon message="数据加载失败" description={error} />
        </div>
      )}
      <Table 
        columns={columns} 
        dataSource={rows} 
        rowKey={(record) => `${record.keyword}-${record.platform}-${record.brand}`}
        loading={loading}
        components={{ header: { cell: ResizableHeaderCell } }}
        tableLayout="fixed"
        scroll={{ x: 'max-content' }}
        pagination={{ pageSize: 10 }}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={error ? '加载失败，请检查URL参数或稍后重试' : '暂无数据'}
            />
          ),
        }}
      />
    </Card>
  );
};

export default BrandShareOfVoiceTable;
