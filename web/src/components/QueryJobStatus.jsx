import React, { useState, useEffect, useCallback } from 'react';
import {
  Table,
  Select,
  Switch,
  Card,
  Tag,
  Typography,
  Space,
  Button,
  Tooltip,
  Badge,
  Empty,
  message
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { CONFIG } from '../config';
import { getQueryParam, updateQueryParams } from '../utils';

const { Title, Text } = Typography;

// Mapping status codes to visual elements
// Assuming 1 is active/effective based on context, adjusting as needed
const STATUS_MAP = {
  0: { text: '未生效', color: 'default', icon: <ClockCircleOutlined /> },
  1: { text: '生效中', color: 'processing', icon: <SyncOutlined spin /> },
  2: { text: '已完成', color: 'success', icon: <CheckCircleOutlined /> },
  3: { text: '已失效', color: 'error', icon: <CloseCircleOutlined /> },
};

const QueryJobStatus = ({ tenantKey: propTenantKey }) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [tenantKey] = useState(() => propTenantKey || getQueryParam('tenant_key', CONFIG.DEFAULT_TENANT_KEY));
  const [selectedJobId, setSelectedJobId] = useState(() => getQueryParam('job_id', ''));
  const [jobIdOptions, setJobIdOptions] = useState([]);
  const [includeDeleted, setIncludeDeleted] = useState(() => {
    const raw = getQueryParam('include_deleted', 'false');
    return raw === 'true' || raw === '1';
  });

  useEffect(() => {
    updateQueryParams({ include_deleted: includeDeleted });
  }, [includeDeleted]);

  const fetchData = useCallback(async () => {
    if (!tenantKey) {
      return;
    }
    setLoading(true);
    try {
      const params = new URLSearchParams({
        tenant_key: tenantKey,
        include_deleted: includeDeleted ? 'true' : 'false',
      });
      if (selectedJobId) {
        params.set('job_id', selectedJobId);
      }

      const response = await fetch(`/api/v1/query-jobs/status?${params}`);
      if (!response.ok) {
        message.error('查询失败');
        return;
      }
      const result = await response.json();

      if (result?.success) {
        const jobs = Array.isArray(result.jobs) ? result.jobs : [];
        setData(jobs);
        const nextJobIds = jobs.map((job) => job?.job_id).filter(Boolean);
        setJobIdOptions((prev) => {
          if (selectedJobId) {
            return Array.from(new Set([...prev, ...nextJobIds]));
          }
          return Array.from(new Set(nextJobIds));
        });
      } else {
        message.error(result?.message || '查询失败');
      }
    } catch (error) {
      console.error('Fetch error:', error);
      message.error('网络请求错误');
    } finally {
      setLoading(false);
    }
  }, [tenantKey, includeDeleted, selectedJobId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const columns = [
    {
      title: '品牌 / 竞品',
      key: 'brand_info',
      width: 250,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ fontSize: '16px' }}>{record.brand}</Text>
          <Space wrap size={[0, 4]} style={{ marginTop: 4 }}>
            {record.competitor?.map((comp, idx) => (
              <Tag key={idx} bordered={false} style={{ background: 'rgba(255,255,255,0.08)', marginRight: 4 }}>
                {comp}
              </Tag>
            ))}
          </Space>
        </Space>
      ),
    },
    {
      title: '查询内容',
      dataIndex: 'query_content',
      key: 'query_content',
      render: (text) => (
        <Tooltip title={text} placement="topLeft">
          <Text
            style={{ 
              maxWidth: 400, 
              display: 'block', 
              overflow: 'hidden', 
              textOverflow: 'ellipsis', 
              whiteSpace: 'nowrap',
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace" // Technical feel
            }}
          >
            {text}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: '生效时间',
      key: 'time',
      width: 200,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            From: {dayjs(record.effective_from).format('YYYY-MM-DD HH:mm')}
          </Text>
          {record.effective_to && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              To: &nbsp;&nbsp;&nbsp;{dayjs(record.effective_to).format('YYYY-MM-DD HH:mm')}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'query_status',
      key: 'query_status',
      width: 120,
      render: (status) => {
        const statusConfig = STATUS_MAP[status] || { text: '未知', color: 'default' };
        return (
          <Badge status={statusConfig.color} text={statusConfig.text} />
        );
      },
    },
  ];

  return (
    <div className="max-w-6xl mx-auto p-4 fade-in-up">
      <style>{`
        .fade-in-up {
          animation: fadeInUp 0.6s ease-out;
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .glass-card {
          background: rgba(255, 255, 255, 0.02);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.06);
        }
      `}</style>
      
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div className="flex justify-between items-center">
          <div>
            <Title level={2} style={{ marginBottom: 0 }}>任务状态监控</Title>
            <Text type="secondary">实时追踪 LLM 查询任务的执行与生效情况</Text>
          </div>
          <Space>
             <Select
                allowClear
                placeholder="选择任务 ID"
                value={selectedJobId || undefined}
                options={jobIdOptions.map((jobId) => ({ label: jobId, value: jobId }))}
                onChange={(value) => setSelectedJobId(value || '')}
                style={{ width: 280 }}
                suffixIcon={<SearchOutlined style={{ color: 'rgba(255,255,255,0.25)' }} />}
             />
             <Space size="small">
                <Text type="secondary" style={{ fontSize: 12 }}>包含已删除</Text>
                <Switch 
                  size="small" 
                  checked={includeDeleted} 
                  onChange={setIncludeDeleted} 
                />
             </Space>
             <Button type="primary" icon={<ReloadOutlined />} onClick={fetchData} loading={loading}>
                查询
             </Button>
          </Space>
        </div>

        <Card 
          className="glass-card" 
          bordered={false} 
          bodyStyle={{ padding: 0 }}
        >
          <Table
            dataSource={data}
            columns={columns}
            rowKey={(record) => `${record.tenant_key}-${record.effective_from}-${Math.random()}`} // Best effort key
            loading={loading}
            pagination={{ pageSize: 10 }}
            locale={{ emptyText: <Empty description="暂无数据，请尝试查询" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
            rowClassName="hover:bg-white/5 transition-colors duration-200"
          />
        </Card>
      </Space>
    </div>
  );
};

export default QueryJobStatus;
