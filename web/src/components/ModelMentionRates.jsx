import React, { useState, useEffect } from 'react';
import '../styles/model-mention-rates.css';

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
          { name: 'ChatGPT', rate: 85, color: '#10b981' },
          { name: 'Gemini', rate: 72, color: '#3b82f6' },
          { name: 'Claude', rate: 68, color: '#f59e0b' },
          { name: '通义千问', rate: 45, color: '#ef4444' },
          { name: '豆包', rate: 38, color: '#8b5cf6' },
          { name: 'DeepSeek', rate: 35, color: '#06b6d4' },
          { name: 'Kimi', rate: 32, color: '#a855f7' },
          { name: '元宝', rate: 28, color: '#f97316' },
          { name: '夸克', rate: 25, color: '#ec4899' },
          { name: '文心一言', rate: 22, color: '#6b7280' }
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
      <div className="model-mention-rates">
        <h2>
          <div></div>
          各模型提及率
        </h2>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="model-mention-rates">
        <h2>
          <div></div>
          各模型提及率
        </h2>
        <div className="error-state">{error}</div>
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <div className="model-mention-rates">
        <h2>
          <div></div>
          各模型提及率
        </h2>
        <div className="empty-state">
          <p>暂无模型数据</p>
        </div>
      </div>
    );
  }

  return (
    <div className="model-mention-rates">
      <h2>
        <div></div>
        各模型提及率
      </h2>
      <div className="models-container">
        {models.map((model) => (
          <div key={model.name} className="model-item">
            <div className="model-name">{model.name}</div>
            <div className="rate-bar-container">
              <div 
                className="rate-bar"
                style={{ 
                  width: `${model.rate}%`,
                  background: `linear-gradient(90deg, ${model.color}dd, ${model.color})`
                }}
              ></div>
            </div>
            <div className="rate-value">{model.rate}%</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ModelMentionRates;