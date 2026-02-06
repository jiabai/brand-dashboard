import React, { useState, useEffect, useRef } from 'react';
import { Card, Typography, Tag, Table, Badge, theme, Flex, Input, Button, Divider, Tooltip, Empty } from 'antd';
import { Chart } from '@antv/g2';
import { 
  Search, 
  Download, 
  ExternalLink, 
  Globe, 
  FileText, 
  Filter,
  Info,
  TrendingUp,
  Hash
} from 'lucide-react';

const { Title, Text } = Typography;

// --- Mock Data ---

const MOCK_KEYWORDS = [
  '无尺码', '舒适', '内衣', '女性', '自由', '透气', '运动', '家居', 
  '大胸显小', '小胸聚拢', '亲肤', '无痕', '夏季新品', '折扣'
];

const MOCK_SOURCE_STATS = [
  { type: '电商', value: 40, color: '#2582a1', icon: '🛒' }, 
  { type: '新闻', value: 20, color: '#f88c24', icon: '📰' }, 
  { type: '问答百科', value: 15, color: '#c52125', icon: '❓' }, 
  { type: '官网', value: 10, color: '#87f4d0', icon: '🏢' }, 
  { type: '社交媒体', value: 15, color: '#a062d4', icon: '📱' }, 
];

const MOCK_MEDIA_LIST = Array.from({ length: 15 }).map((_, i) => ({
  key: i,
  domain: `source-${i}.com`,
  sourceName: `信源名称 ${i + 1}`,
  sourceUrl: `https://source-${i}.com`,
  keyword: MOCK_KEYWORDS[i % MOCK_KEYWORDS.length],
  contentType: ['新闻', '论坛', '博客', '评论'][i % 4],
  platform: ['Google', 'Bing', 'Baidu'][i % 3],
  citationRate: Math.floor(Math.random() * 100),
}));

// --- Components ---

const KeywordSection = () => {
  const { token } = theme.useToken();
  const [selectedKeyword, setSelectedKeyword] = useState(null);
  
  return (
    <Card 
      bordered={false} 
      styles={{ body: { padding: token.paddingLG } }}
      style={{ boxShadow: token.boxShadowTertiary, borderRadius: token.borderRadiusLG }}
    >
      <Flex vertical gap="middle">
        <Flex align="center" gap="small">
          <Hash size={20} color={token.colorPrimary} />
          <Title level={4} style={{ margin: 0, fontWeight: 700 }}>品牌关键词</Title>
          {selectedKeyword && (
            <Tag 
              closable 
              onClose={() => setSelectedKeyword(null)}
              color="processing"
              style={{ marginLeft: token.marginSM }}
            >
              已选: {selectedKeyword}
            </Tag>
          )}
        </Flex>
        
        <Divider style={{ margin: '4px 0' }} />
        
        <Flex wrap="wrap" gap="small">
          {MOCK_KEYWORDS.map((kw) => {
            const isSelected = selectedKeyword === kw;
            return (
              <Tag 
                key={kw} 
                bordered={false}
                onClick={() => setSelectedKeyword(isSelected ? null : kw)}
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
      </Flex>
    </Card>
  );
};

const SourceAnalysisChart = () => {
  const { token } = theme.useToken();
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // 清空容器内容（防止热更新重复渲染）
    containerRef.current.innerHTML = '';

    const chart = new Chart({
      container: containerRef.current,
      autoFit: true,
      height: 16,
      padding: 0,
      inset: 0, // 确保图表内部无任何边距
    });

    chart.data(MOCK_SOURCE_STATS.map(item => ({
      category: 'all',
      type: item.type,
      value: item.value / 100,
    })));

    chart
      .interval()
      .coordinate({ transform: [{ type: 'transpose' }] })
      .encode('x', 'category')
      .encode('y', 'value')
      .encode('color', 'type')
      .transform([{ type: 'stackY' }, { type: 'normalizeY' }])
      .scale('color', {
        range: MOCK_SOURCE_STATS.map(item => item.color),
      })
      .scale('x', {
        padding: 0, // 消除分类轴的默认内边距，确保撑满高度
      })
      .axis(false)
      .legend(false)
      .tooltip(false)
      .style('radius', 0) // 在堆叠条形图中，中间的块不应该有圆角，否则会出现间隙
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
  }, []);

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
            { label: '按天', value: '2025-09-16' },
            { label: 'Prompt 总数', value: '75' },
            { label: '引用信源数', value: '762' }
          ].map(item => (
            <Flex key={item.label} align="center" gap="xs">
              <Text type="secondary" style={{ fontSize: token.fontSizeSM }}>{item.label}：</Text>
              <Text strong style={{ fontSize: token.fontSize }}>{item.value}</Text>
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
        {MOCK_SOURCE_STATS.map((item) => (
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

const MediaListTable = () => {
  const { token } = theme.useToken();

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
      render: (text) => (
        <Tag bordered={false} icon={<Hash size={10} />} style={{ borderRadius: 4 }}>
          {text}
        </Tag>
      ),
    },
    {
      title: '内容类型',
      dataIndex: 'contentType',
      key: 'contentType',
      render: (text) => {
        const colors = { '新闻': 'blue', '论坛': 'cyan', '博客': 'purple', '评论': 'orange' };
        return <Tag color={colors[text] || 'default'} bordered={false}>{text}</Tag>;
      },
    },
    {
      title: '大模型平台',
      dataIndex: 'platform',
      key: 'platform',
      render: (text) => (
        <Flex align="center" gap="small">
          <Badge status="processing" />
          <Text>{text}</Text>
        </Flex>
      )
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
            href={record.sourceUrl} 
            target="_blank" 
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
          <Button icon={<Filter size={14} />}>高级筛选</Button>
          <Button type="primary" icon={<Download size={14} />}>导出报告</Button>
        </Flex>
      </Flex>
      <Table 
        columns={columns} 
        dataSource={MOCK_MEDIA_LIST} 
        pagination={{ 
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`
        }}
        size="middle"
      />
    </Card>
  );
};

export default function SourceAnalysis() {
  return (
    <Flex vertical gap="large">
      <KeywordSection />
      <SourceAnalysisChart />
      <MediaListTable />
    </Flex>
  );
}


