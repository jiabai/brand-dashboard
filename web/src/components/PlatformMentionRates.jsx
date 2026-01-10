import React, { useState, useEffect } from 'react';
import { Card, List, Progress, Typography, Statistic, Tag, theme } from 'antd';
import { TrophyOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

const PlatformMentionRates = ({ onPlatformClick }) => {
  const { token } = theme.useToken();
  const [platforms, setPlatforms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPlatformData = async () => {
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        const mockData = [
          { name: '豆包', rate: 45, color: '#9254de', change: +4 },
          { name: 'DeepSeek', rate: 38, color: '#13c2c2', change: 0 },
          { name: '千问', rate: 35, color: token.colorError, change: -1 },
          { name: '夸克', rate: 32, color: '#eb2f96', change: 0 },
          { name: 'Kimi', rate: 28, color: '#531dab', change: -3 },
          { name: '元宝', rate: 25, color: token.colorPrimary, change: +2 },
          { name: 'AI抖音', rate: 22, color: token.colorWarning, change: +5 }
        ];
        
        setPlatforms(mockData);
        setLoading(false);
      } catch (err) {
        setError('数据加载失败');
        setLoading(false);
      }
    };

    fetchPlatformData();
  }, [token]);

  if (loading) {
    return (
      <Card title="各平台提及率" loading />
    );
  }

  if (error) {
    return (
      <Card title="各平台提及率">
        <Typography.Text type="danger">{error}</Typography.Text>
      </Card>
    );
  }

  if (platforms.length === 0) {
    return (
      <Card title="各平台提及率">
        <Typography.Text type="secondary">暂无平台数据</Typography.Text>
      </Card>
    );
  }

  return (
    <Card title="各平台提及率">
      <List
        dataSource={platforms}
        renderItem={(platform, index) => (
          <List.Item
            style={{
              padding: token.padding,
              marginBottom: token.marginSM,
              borderRadius: token.borderRadiusLG,
              background: index < 3 ? token.colorFillAlter : 'transparent',
              border: index < 3 ? `1px solid ${token.colorBorderSecondary}` : 'none',
              transition: 'all 0.3s ease',
              cursor: 'pointer'
            }}
            hoverable
            onClick={() => {
              if (onPlatformClick) {
                onPlatformClick(platform);
              }
            }}
          >
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: token.marginXS }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: token.marginSM }}>
                  {index < 3 && (
                    <Tag color={platform.color} icon={<TrophyOutlined />}>
                      {index + 1}
                    </Tag>
                  )}
                  <Typography.Text strong style={{ fontSize: index < 3 ? token.fontSizeLG : token.fontSize }}>
                    {platform.name}
                  </Typography.Text>
                </div>
                <Statistic
                  value={platform.rate}
                  suffix="%"
                  valueStyle={{ color: platform.color, fontSize: token.fontSizeXL, fontWeight: 'bold' }}
                />
              </div>
              <Progress
                percent={platform.rate}
                showInfo={false}
                strokeColor={platform.color}
                size="small"
                strokeWidth={8}
              />
              {platform.change !== 0 && (
                <div style={{ marginTop: token.marginXS, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {platform.change > 0 ? (
                    <ArrowUpOutlined style={{ color: token.colorSuccess, fontSize: token.fontSizeSM }} />
                  ) : (
                    <ArrowDownOutlined style={{ color: token.colorError, fontSize: token.fontSizeSM }} />
                  )}
                  <Typography.Text type={platform.change > 0 ? 'success' : 'danger'} style={{ fontSize: token.fontSizeSM }}>
                    {Math.abs(platform.change)}%
                  </Typography.Text>
                </div>
              )}
            </div>
          </List.Item>
        )}
      />
    </Card>
  );
};

export default PlatformMentionRates;
