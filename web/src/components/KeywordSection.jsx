import React, { useState } from 'react';
import { Card, Typography, Tag, Divider, Flex, Spin, Empty, theme } from 'antd';
import { Hash } from 'lucide-react';

const { Title } = Typography;

const KeywordSection = ({ keywords = [], loading = false, selectedKeyword, onKeywordChange, style }) => {
  const { token } = theme.useToken();
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
    <Card
      variant="borderless"
      styles={{ body: { padding: token.paddingLG, display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 } }}
      style={{ boxShadow: token.boxShadowTertiary, borderRadius: token.borderRadiusLG, display: 'flex', flexDirection: 'column', ...style }}
    >
      <Spin spinning={loading}>
        <Flex vertical gap="middle" style={{ flex: 1 }}>
          <Flex align="center" gap="small">
            <Hash size={20} color={token.colorPrimary} />
            <Title level={4} style={{ margin: 0, fontWeight: 700 }}>品牌关键词</Title>
            {currentKeyword ? (
              <Tag
                closable
                onClose={handleClear}
                color="processing"
                style={{ marginLeft: token.marginSM }}
              >
                已选: {currentKeyword}
              </Tag>
            ) : null}
          </Flex>

          <Divider style={{ margin: '4px 0' }} />

          {keywords.length > 0 ? (
            <Flex wrap="wrap" gap="small">
              {keywords.map((kw) => {
                const isSelected = currentKeyword === kw;
                return (
                  <Tag
                    key={kw}
                    bordered={false}
                    onClick={() => handleSelect(kw)}
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
          ) : !loading && (
            <Empty description="暂无关键词" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </Flex>
      </Spin>
    </Card>
  );
};

export default KeywordSection;
