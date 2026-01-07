import React, { useState, useEffect } from 'react';
import { Card, List, Progress, Typography } from 'antd';

const ModelMentionRates = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchModelData = async () => {
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        const mockData = [
          { name: 'ChatGPT', rate: 85, color: '#52c41a' },
          { name: 'Gemini', rate: 72, color: '#1677ff' },
          { name: 'Claude', rate: 68, color: '#faad14' },
          { name: '通义千问', rate: 45, color: '#ff4d4f' },
          { name: '豆包', rate: 38, color: '#722ed1' },
          { name: 'DeepSeek', rate: 35, color: '#13c2c2' },
          { name: 'Kimi', rate: 32, color: '#2f54eb' },
          { name: '元宝', rate: 28, color: '#fa8c16' },
          { name: '夸克', rate: 25, color: '#eb2f96' },
          { name: '文心一言', rate: 22, color: '#8c8c8c' }
        ];
        
        setModels(mockData);
        setLoading(false);
      } catch (err) {
        setError('数据加载失败');
        setLoading(false);
      }
    };

    fetchModelData();
  }, []);

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
        renderItem={(model) => (
          <List.Item>
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <Typography.Text strong>{model.name}</Typography.Text>
                <Typography.Text>{model.rate}%</Typography.Text>
              </div>
              <Progress
                percent={model.rate}
                showInfo={false}
                strokeColor={model.color}
              />
            </div>
          </List.Item>
        )}
      />
    </Card>
  );
};

export default ModelMentionRates;
