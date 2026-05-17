import React, { useEffect, useRef, useState } from 'react';
import { Card, Flex, Typography, theme } from 'antd';
import { SmileOutlined } from '@ant-design/icons';
import { fetchFilterMetadata } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import { loadG2Chart } from '@/utils/loadG2Chart';
import KeywordSection from './KeywordSection';

const { Title } = Typography;

const MOCK_SENTIMENT = [
  { name: '正面', value: 600 },
  { name: '负面', value: 200 },
  { name: '中性', value: 200 },
];

const WORD_CLOUD_DATA = [
  { text: '品牌声量', value: 88 },
  { text: '正面反馈', value: 72 },
  { text: '体验', value: 66 },
  { text: '信任', value: 58 },
  { text: '价格', value: 52 },
  { text: '服务', value: 46 },
  { text: '质量', value: 44 },
  { text: '推荐', value: 40 },
  { text: '社媒讨论', value: 36 },
  { text: '复购', value: 32 },
  { text: '物流', value: 28 },
  { text: '客服', value: 24 },
];

const SentimentDonutChart = ({ containerRef }) => {
  const { token } = theme.useToken();
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    let disposed = false;
    const container = containerRef.current;

    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }

    const run = async () => {
      const Chart = await loadG2Chart();
      if (disposed) return;

      const total = MOCK_SENTIMENT.reduce((sum, item) => sum + item.value, 0);

      const chart = new Chart({
        container,
        autoFit: true,
        height: (container.clientHeight * 0.8) || 256,
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
    };

    run().catch(() => {});

    return () => {
      disposed = true;
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [containerRef, token.colorBgContainer]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};

export default function SentimentAnalysis() {
  const { date, endDate, tenantKey, jobId } = useDashboardRequestParams();
  const { token } = theme.useToken();
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const donutRef = useRef(null);
  const wordCloudRef = useRef(null);
  const wordCloudChartRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    
    const fetchMetadata = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchFilterMetadata(
          { tenantKey, jobId, startDate: date, endDate },
          { signal: controller.signal },
        );

        if (result?.code === 200 && result.data) {
          setKeywords(result.data.keywords || []);
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
  }, [tenantKey, jobId, date, endDate]);

  useEffect(() => {
    if (!wordCloudRef.current) return;

    let disposed = false;
    const container = wordCloudRef.current;

    if (wordCloudChartRef.current) {
      wordCloudChartRef.current.destroy();
      wordCloudChartRef.current = null;
    }

    const run = async () => {
      const Chart = await loadG2Chart();
      if (disposed) return;

      const chart = new Chart({
        container,
        autoFit: true,
        paddingTop: 80,
      });

      chart
        .wordCloud()
        .data(WORD_CLOUD_DATA)
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
      wordCloudChartRef.current = chart;
    };

    run().catch(() => {});
    return () => {
      disposed = true;
      if (wordCloudChartRef.current) {
        wordCloudChartRef.current.destroy();
        wordCloudChartRef.current = null;
      }
    };
  }, []);

  return (
    <Flex vertical gap="large" align="stretch" style={{ width: '100%', minHeight: 'calc(100vh - 112px)', height: '100%' }}>
      <KeywordSection keywords={keywords} loading={loading} style={{ flex: '0 0 auto' }} />
      <Card
        variant="borderless"
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
