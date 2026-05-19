import React, { useState } from 'react';
import { Hash } from 'lucide-react';

import EmptyState from './EmptyState.jsx';
import LoadingSpinner from './LoadingSpinner.jsx';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import { Separator } from './ui/separator.jsx';
import { cn } from '@/lib/cn';

const KeywordSection = ({ keywords = [], loading = false, selectedKeyword, onKeywordChange, style }) => {
  const [internalKeyword, setInternalKeyword] = useState('');

  const isControlled = selectedKeyword !== undefined;
  const currentKeyword = isControlled ? selectedKeyword : internalKeyword;

  const handleSelect = (kw) => {
    const next = currentKeyword === kw ? '' : kw;
    if (!isControlled) {
      setInternalKeyword(next);
    }
    onKeywordChange?.(next);
  };

  const handleClear = () => {
    if (!isControlled) {
      setInternalKeyword('');
    }
    onKeywordChange?.('');
  };

  return (
    <Card className="min-h-full" style={style}>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <Hash className="text-primary" />
          <CardTitle>品牌关键词</CardTitle>
          {currentKeyword ? (
            <Badge variant="secondary" className="gap-2">
              已选: {currentKeyword}
              <Button variant="ghost" size="icon-xs" onClick={handleClear} aria-label="清除关键词">
                x
              </Button>
            </Badge>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Separator />

        {loading ? (
          <LoadingSpinner text="正在加载关键词..." />
        ) : keywords.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {keywords.map((kw) => {
              const isSelected = currentKeyword === kw;
              return (
                <button
                  key={kw}
                  type="button"
                  onClick={() => handleSelect(kw)}
                  className={cn(
                    'rounded-lg px-3 py-1 text-sm transition-colors',
                    isSelected
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                  )}
                >
                  {kw}
                </button>
              );
            })}
          </div>
        ) : (
          <EmptyState title="暂无关键词" description="当前筛选条件下没有关键词数据" icon={Hash} />
        )}
      </CardContent>
    </Card>
  );
};

export default KeywordSection;
