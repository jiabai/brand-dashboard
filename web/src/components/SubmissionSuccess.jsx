import React from 'react';
import { Button, Card, Typography, Descriptions, Space } from 'antd';
import { CheckCircleOutlined, PlusOutlined, FileSearchOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const SubmissionSuccess = ({ result, onReset, onViewStatus }) => {
  if (!result) return null;

  return (
    <div className="flex flex-col items-center justify-center py-12 fade-in min-h-[60vh]">
      <div className="relative mb-6">
        <div className="absolute inset-0 bg-green-500/20 blur-3xl rounded-full animate-pulse"></div>
        <CheckCircleOutlined className="text-[64px] text-[#52c41a] relative z-10" />
      </div>
      
      <Title level={2} style={{ marginBottom: 8 }}>任务提交成功</Title>
      <Text type="secondary" className="mb-8 text-lg">您的查询任务已成功进入队列</Text>

      <Card 
        className="w-full max-w-2xl mb-10 glass-card"
        variant="borderless"
      >
        <Descriptions column={1} bordered size="middle" labelStyle={{ width: '120px' }}>
          <Descriptions.Item label="任务 ID">
            <Text copyable code>{result.job_id || 'N/A'}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="插入行数">
            <Text strong>{result.inserted_rows}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="提交时间">
            {dayjs().format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          {result.message && (
             <Descriptions.Item label="系统消息">
                {result.message}
             </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      <Space size="large">
        <Button 
          size="large" 
          icon={<PlusOutlined />} 
          onClick={onReset}
          className="min-w-[140px]"
        >
          创建新任务
        </Button>
        <Button 
          type="primary" 
          size="large" 
          icon={<FileSearchOutlined />} 
          onClick={onViewStatus}
          className="min-w-[140px]"
        >
          查看任务状态
        </Button>
      </Space>

      <style>{`
        .glass-card {
          background: rgba(255, 255, 255, 0.02);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .fade-in {
          animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); scale: 0.98; }
          to { opacity: 1; transform: translateY(0); scale: 1; }
        }
      `}</style>
    </div>
  );
};

export default SubmissionSuccess;
