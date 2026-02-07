import React, { useEffect, useRef, useState } from 'react';
import { Card, Divider, Flex, Tag, Typography, theme } from 'antd';
import { SmileOutlined } from '@ant-design/icons';
import { Hash } from 'lucide-react';
import { Chart } from '@antv/g2';

const { Title } = Typography;

const MOCK_KEYWORDS = [
  '无尺码', '舒适', '内衣', '女性', '自由', '透气', '运动', '家居',
  '大胸显小', '小胸聚拢', '亲肤', '无痕', '夏季新品', '折扣'
];

const MOCK_SENTIMENT = [
  { name: '正面', value: 600 },
  { name: '负面', value: 200 },
  { name: '中性', value: 200 },
];

const MOCK_DETAILS = Array.from({ length: 10 }).map((_, i) => ({
  key: i,
  content: [
    '这款内衣真的很舒服，无痕效果满分！',
    '颜色有点偏差，不过面料确实很亲肤。',
    '发货速度太慢了，等了一周才到。',
    '第二次购买了，依然很满意。',
    '尺码偏小，建议大家买大一码。',
    '运动时穿也很稳固，透气性不错。',
    '包装很精美，送人也很合适。',
    '价格偏贵，性价比一般般。',
    '客服态度很好，处理问题很及时。',
    '夏天穿正合适，一点都不闷热。'
  ][i % 10],
  sentiment: ['正面', '中性', '负面', '正面', '负面', '正面', '正面', '中性', '正面', '正面'][i % 10],
  platform: ['小红书', '微博', '抖音', '知乎', '京东'][i % 5],
  date: '2025-09-16',
}));

const KeywordSection = ({ style }) => {
  const { token } = theme.useToken();
  const [selectedKeyword, setSelectedKeyword] = useState(null);

  return (
    <Card
      bordered={false}
      styles={{ body: { padding: token.paddingLG, display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 } }}
      style={{ boxShadow: token.boxShadowTertiary, borderRadius: token.borderRadiusLG, display: 'flex', flexDirection: 'column', ...style }}
    >
      <Flex vertical gap="middle" style={{ flex: 1 }}>
        <Flex align="center" gap="small">
          <Hash size={20} color={token.colorPrimary} />
          <Title level={4} style={{ margin: 0, fontWeight: 700 }}>品牌关键词</Title>
          {selectedKeyword ? (
            <Tag
              closable
              onClose={() => setSelectedKeyword(null)}
              color="processing"
              style={{ marginLeft: token.marginSM }}
            >
              已选: {selectedKeyword}
            </Tag>
          ) : null}
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
                  margin: 0,
                }}
                className={!isSelected ? 'hover:bg-blue-50 hover:text-blue-600' : ''}
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

const SentimentDonutChart = ({ containerRef }) => {
  const { token } = theme.useToken();
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }

    const total = MOCK_SENTIMENT.reduce((sum, item) => sum + item.value, 0);

    const chart = new Chart({
      container: containerRef.current,
      autoFit: true,
      height: (containerRef.current.clientHeight * 0.8) || 256,
      theme: 'dark',
      paddingTop: 40,
    });

    chart.coordinate({ type: 'theta', innerRadius: 0.6 });

    chart
      .interval()
      .data(MOCK_SENTIMENT)
      .transform({ type: 'stackY' })
      .encode('y', 'value')
      .encode('color', 'name')
      .style('stroke', token.colorBgContainer)
      .style('inset', 1)
      .style('radius', 10)
      .scale('color', {
        domain: ['正面', '负面', '中性'],
        range: ['#2582a1', '#c52125', '#f88c24'],
      })
      .label({
        text: (d) => `${d.name}：${d.value}条`,
        fontSize: 12,
        fontWeight: 'bold',
        fill: '#fff',
        position: 'outside',
      })
      .label({
        text: (d) => `${((d.value / total) * 100).toFixed(0)}%`,
        fontSize: 14,
        fill: '#fff',
        position: 'inside',
        fontWeight: 'bold',
      })
      .legend({
        position: 'bottom',
        layout: { justifyContent: 'center' },
      })
      .animate('enter', { type: 'waveIn' });

    chart.render();
    chartRef.current = chart;

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [token]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};

export default function SentimentAnalysis() {
  const { token } = theme.useToken();
  const donutRef = useRef(null);
  const wordCloudRef = useRef(null);

  useEffect(() => {
    if (!wordCloudRef.current) return;

    const chart = new Chart({
      container: wordCloudRef.current,
      autoFit: true,
      paddingTop: 80,
    });

    chart
      .wordCloud()
      .data({
        type: 'fetch',
        value: 'https://assets.antv.antgroup.com/g2/philosophy-word.json',
      })
      .layout({
        spiral: 'rectangular',
        fontSize: [12, 48],
      })
      .encode('color', 'text')
      .scale('color', {
        range: ['#2582a1', '#c52125', '#f88c24'],
      })
      .legend(false);

    chart.render();

    return () => {
      chart.destroy();
    };
  }, []);

  return (
    <Flex vertical gap="large" align="stretch" style={{ width: '100%', minHeight: 'calc(100vh - 112px)', height: '100%' }}>
      <KeywordSection style={{ flex: '0 0 auto' }} />
      <Card
        bordered={false}
        styles={{ body: { padding: token.paddingLG, display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 } }}
        style={{ boxShadow: token.boxShadowTertiary, borderRadius: token.borderRadiusLG, display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}
      >
        <Flex vertical gap="small" style={{ marginBottom: token.marginLG }}>
          <Flex align="center" gap="small">
            <SmileOutlined style={{ color: token.colorPrimary, fontSize: 18 }} />
            <Title level={4} style={{ margin: 0, fontWeight: 700 }}>情感分析</Title>
          </Flex>
          
          <Flex gap="large" align="center" style={{ paddingLeft: 24 }}>
            {[
              { label: '分析样本数', value: '1,280' },
              { label: '正面情感占比', value: '60%' },
              { label: '负面情感占比', value: '20%' }
            ].map(item => (
              <Flex key={item.label} align="center" gap="xs">
                <Typography.Text type="secondary" style={{ fontSize: token.fontSizeSM }}>{item.label}：</Typography.Text>
                <Typography.Text strong style={{ fontSize: token.fontSize }}>{item.value}</Typography.Text>
              </Flex>
            ))}
          </Flex>
        </Flex>

        <Flex gap="large" align="stretch" style={{ width: '100%', flex: 1, minHeight: 0 }}>
          <div style={{ flex: 1, minWidth: 0, minHeight: 0, paddingTop: token.paddingLG }}>
            <SentimentDonutChart containerRef={donutRef} />
          </div>
          <div style={{ flex: 0.8, minWidth: 0, minHeight: 0, paddingTop: token.paddingLG, transform: 'translate(-10%, -10%)' }}>
            <div ref={wordCloudRef} style={{ width: '100%', height: '100%' }} />
          </div>
        </Flex>
      </Card>
    </Flex>
  );
}
