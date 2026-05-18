import React from 'react';
import { CheckCircle, FileSearch, Plus } from 'lucide-react';
import dayjs from 'dayjs';

import { Button } from './ui/button.jsx';
import { Card, CardContent } from './ui/card.jsx';

const SubmissionSuccess = ({ result, onReset, onViewStatus }) => {
  if (!result) return null;

  return (
    <div className="flex flex-col items-center justify-center py-12 fade-in min-h-[60vh]">
      <div className="relative mb-6">
        <div className="absolute inset-0 bg-green-500/20 blur-3xl rounded-full animate-pulse"></div>
        <CheckCircle className="relative z-10 size-16 text-chart-3" />
      </div>
      
      <h2 className="mb-2 text-2xl font-semibold text-foreground">任务提交成功</h2>
      <p className="mb-8 text-lg text-muted-foreground">您的查询任务已成功进入队列</p>

      <Card 
        className="w-full max-w-2xl mb-10 glass-card"
      >
        <CardContent>
          <dl className="grid grid-cols-[120px_minmax(0,1fr)] gap-x-4 gap-y-3 text-sm">
            <dt className="text-muted-foreground">任务 ID</dt>
            <dd className="min-w-0 font-mono text-foreground">{result.job_id || 'N/A'}</dd>
            <dt className="text-muted-foreground">插入行数</dt>
            <dd className="font-semibold text-foreground">{result.inserted_rows}</dd>
            <dt className="text-muted-foreground">提交时间</dt>
            <dd className="text-foreground">{dayjs().format('YYYY-MM-DD HH:mm:ss')}</dd>
          {result.message && (
              <>
                <dt className="text-muted-foreground">系统消息</dt>
                <dd className="text-foreground">{result.message}</dd>
              </>
          )}
          </dl>
        </CardContent>
      </Card>

      <div className="flex flex-wrap justify-center gap-4">
        <Button 
          size="lg" 
          onClick={onReset}
          className="min-w-[140px]"
        >
          <Plus data-icon="inline-start" />
          创建新任务
        </Button>
        <Button 
          size="lg" 
          onClick={onViewStatus}
          className="min-w-[140px]"
        >
          <FileSearch data-icon="inline-start" />
          查看任务状态
        </Button>
      </div>

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
