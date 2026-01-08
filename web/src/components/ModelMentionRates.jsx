import React, { useState, useEffect } from 'react';
import { Card, List, Progress, Typography, Statistic, Tag, theme } from 'antd';
import { TrophyOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

const ModelMentionRates = () => {
  const { token } = theme.useToken();
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchModelData = async () => {
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        const mockData = [
          { name: 'ChatGPT', rate: 85, color: token.colorSuccess, change: +5 },
          { name: 'Gemini', rate: 72, color: '#722ed1', change: -2 },
          { name: 'Claude', rate: 68, color: token.colorWarning, change: +3 },
          { name: '通义千问', rate: 45, color: token.colorError, change: -1 },
          { name: '豆包', rate: 38, color: '#9254de', change: +4 },
          { name: 'DeepSeek', rate: 35, color: '#13c2c2', change: 0 },
          { name: 'Kimi', rate: 32, color: '#531dab', change: -3 },
          { name: '元宝', rate: 28, color: token.colorPrimary, change: +2 },
          { name: '夸克', rate: 25, color: '#eb2f96', change: 0 },
          { name: '文心一言', rate: 22, color: token.colorTextSecondary, change: -1 }
        ];
        
        setModels(mockData);
        setLoading(false);
      } catch (err) {
        setError('数据加载失败');
        setLoading(false);
      }
    };

    fetchModelData();
  }, [token]);

  if (loading) {
    return (
      <Card title="各模型提及率" loading />
    );
  }

  if (error) {
    return (
      <Card title="各模型提及率">
        <Typography.Text type="danger">{error}</Typography.Text>
      </Card>
    );
  }

  if (models.length === 0) {
    return (
      <Card title="各模型提及率">
        <Typography.Text type="secondary">暂无模型数据</Typography.Text>
      </Card>
    );
  }

  return (
    <Card title="各模型提及率">
      <List
        dataSource={models}
        renderItem={(model, index) => (
          <List.Item
            style={{
              padding: token.padding,
              marginBottom: token.marginSM,
              borderRadius: token.borderRadiusLG,
              background: index < 3 ? token.colorFillAlter : 'transparent',
              border: index < 3 ? `1px solid ${token.colorBorderSecondary}` : 'none',
              transition: 'all 0.3s ease'
            }}
            hoverable
          >
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: token.marginXS }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: token.marginSM }}>
                  {index < 3 && (
                    <Tag color={model.color} icon={<TrophyOutlined />}>
                      {index + 1}
                    </Tag>
                  )}
                  <Typography.Text strong style={{ fontSize: index < 3 ? token.fontSizeLG : token.fontSize }}>
                    {model.name}
                  </Typography.Text>
                </div>
                <Statistic
                  value={model.rate}
                  suffix="%"
                  valueStyle={{ color: model.color, fontSize: token.fontSizeXL, fontWeight: 'bold' }}
                />
              </div>
              <Progress
                percent={model.rate}
                showInfo={false}
                strokeColor={model.color}
                size="small"
                strokeWidth={8}
              />
              {model.change !== 0 && (
                <div style={{ marginTop: token.marginXS, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {model.change > 0 ? (
                    <ArrowUpOutlined style={{ color: token.colorSuccess, fontSize: token.fontSizeSM }} />
                  ) : (
                    <ArrowDownOutlined style={{ color: token.colorError, fontSize: token.fontSizeSM }} />
                  )}
                  <Typography.Text type={model.change > 0 ? 'success' : 'danger'} style={{ fontSize: token.fontSizeSM }}>
                    {Math.abs(model.change)}%
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

export default ModelMentionRates;
