import React, { useState } from 'react';
import {
  Form,
  Input,
  InputNumber,
  DatePicker,
  Button,
  Card,
  Space,
  Typography,
  Divider,
  message,
  Alert
} from 'antd';
import { MinusCircleOutlined, PlusOutlined, UploadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { CONFIG } from '../config';
import { getQueryParam, updateQueryParams } from '../utils';

const { Title, Text } = Typography;
const { TextArea } = Input;

const CreateQueryJob = ({ tenantKey: propTenantKey, jobId: propJobId }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const executorId = getQueryParam('executor_id', 'exec_bbda021a');
  const tenantKey = propTenantKey || getQueryParam('tenant_key', CONFIG.DEFAULT_TENANT_KEY);
  const initialJobId = propJobId || getQueryParam('job_id', '');

  React.useEffect(() => {
    updateQueryParams({ executor_id: executorId });
  }, [executorId]);

  const onFinish = async (values) => {
    setLoading(true);
    setResult(null);
    try {
      // Format dates
      const payload = {
        ...values,
        effective_from: values.effective_from ? values.effective_from.toISOString() : undefined,
        effective_to: values.effective_to ? values.effective_to.toISOString() : undefined,
        last_executed_date: values.last_executed_date ? values.last_executed_date.format('YYYY-MM-DD') : dayjs().format('YYYY-MM-DD'),
        // Ensure defaults if not present (though form initialValues handles this mostly)
        total_runs: values.total_runs || 15,
        executed_runs: values.executed_runs || 0,
      };

      const response = await fetch(`/api/v1/query-jobs/load`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        message.success(data.message || '任务加载成功');
        setResult(data);
        form.resetFields();
      } else {
        message.error(data.message || '任务加载失败');
      }
    } catch (error) {
      console.error('Error submitting form:', error);
      message.error('请求发生错误: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateRandomIds = () => {
    const randomHex = (len) => [...Array(len)].map(() => Math.floor(Math.random() * 16).toString(16)).join('');
    const today = dayjs().format('YYYYMMDD_HHmmss');
    
    form.setFieldsValue({
      job_id: `job_${today}_${randomHex(8)}`,
    });
  };

  return (
    <div className="max-w-5xl mx-auto p-4">
      <Card title={<Title level={3}>LLM 查询任务加载</Title>} extra={<Button onClick={generateRandomIds}>生成示例 ID</Button>}>
        {result && (
          <Alert
            message="加载成功"
            description={`成功插入 ${result.inserted_rows} 行数据`}
            type="success"
            showIcon
            closable
            onClose={() => setResult(null)}
            style={{ marginBottom: 24 }}
          />
        )}
        
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            tenant_key: tenantKey,
            job_id: initialJobId || undefined,
            executor_id: executorId,
            total_runs: 15,
            executed_runs: 0,
            last_executed_date: dayjs(),
            effective_from: dayjs().startOf('day'),
          }}
        >
          <Divider orientation="left">基本信息</Divider>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item
              name="tenant_key"
              label="租户标识 Key"
              rules={[{ required: true, message: '请输入租户标识 Key' }]}
            >
              <Input placeholder="tn_..." disabled />
            </Form.Item>
            <Form.Item
              name="job_id"
              label="任务 ID"
              rules={[{ required: true, message: '请输入任务 ID' }]}
            >
              <Input placeholder="job_..." />
            </Form.Item>
            <Form.Item
              name="executor_id"
              label="执行器 ID"
              rules={[{ required: true, message: '请输入执行器 ID' }]}
            >
              <Input placeholder="exec_..." disabled />
            </Form.Item>
            <Form.Item
              name="last_executed_date"
              label="最近执行日期"
              rules={[{ required: true, message: '请选择日期' }]}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="effective_from"
              label="生效开始时间"
              rules={[{ required: true, message: '请选择开始时间' }]}
            >
              <DatePicker showTime style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="effective_to"
              label="生效结束时间"
            >
              <DatePicker showTime style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="total_runs"
              label="总执行次数"
              rules={[{ required: true, message: '请输入总执行次数' }]}
            >
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="executed_runs"
              label="已执行次数"
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <Divider orientation="left">数据配置 (Data)</Divider>
          <Form.Item
            name={['data', 'category']}
            label="分类名称"
            rules={[{ required: true, message: '请输入分类名称' }]}
          >
            <Input placeholder="例如：游戏" />
          </Form.Item>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item
              name={['data', 'brand']}
              label="品牌名称"
              rules={[{ required: true, message: '请输入品牌名称' }]}
            >
              <Input placeholder="例如：哈基桃电竞" />
            </Form.Item>
          </div>

          <Form.List 
            name={['data', 'competitor']}
            rules={[
              {
                validator: async (_, names) => {
                  if (!names || names.length < 1) {
                    return Promise.reject(new Error('至少需要一个竞品名称'));
                  }
                },
              },
            ]}
          >
            {(fields, { add, remove }, { errors }) => (
              <>
                <Form.Item 
                  label="竞品名称列表"
                  required
                  validateStatus={errors.length > 0 ? 'error' : ''}
                  help={errors[0]}
                >
                  {fields.map((field, index) => (
                    <div key={field.key} className="flex gap-2 mb-2">
                      <Form.Item
                        {...field}
                        noStyle
                        rules={[{ required: true, message: '请输入竞品名称' }]}
                      >
                        <Input placeholder="竞品名称" />
                      </Form.Item>
                      <Button
                        type="text"
                        danger
                        icon={<MinusCircleOutlined />}
                        onClick={() => remove(field.name)}
                      />
                    </div>
                  ))}
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                    添加竞品
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>

          <Divider orientation="left">查询内容 (Content)</Divider>
          <Form.List name={['data', 'content']} 
             rules={[
                {
                  validator: async (_, names) => {
                    if (!names || names.length < 1) {
                      return Promise.reject(new Error('至少需要一个内容项'));
                    }
                  },
                },
              ]}
          >
            {(fields, { add, remove }) => (
              <div className="space-y-4">
                {fields.map(({ key, name, ...restField }) => (
                  <Card 
                    key={key} 
                    size="small" 
                    title={`内容项 #${name + 1}`} 
                    extra={<Button type="text" danger icon={<MinusCircleOutlined />} onClick={() => remove(name)} />}
                  >
                    <Form.Item
                      {...restField}
                      name={[name, 'keyword']}
                      label="关键词"
                      rules={[{ required: true, message: '请输入关键词' }]}
                    >
                      <Input placeholder="例如：三角洲陪玩" />
                    </Form.Item>

                    <Form.List name={[name, 'query_content']}>
                      {(queryFields, { add: addQuery, remove: removeQuery }) => (
                        <>
                          <Text type="secondary" className="mb-2 block">查询语句列表:</Text>
                          {queryFields.map((queryField) => (
                            <div key={queryField.key} className="flex gap-2 mb-2">
                              <Form.Item
                                {...queryField}
                                noStyle
                                rules={[{ required: true, message: '请输入查询语句' }]}
                              >
                                <Input placeholder="例如：三角洲陪玩哪家好？" />
                              </Form.Item>
                              <Button
                                type="text"
                                danger
                                icon={<MinusCircleOutlined />}
                                onClick={() => removeQuery(queryField.name)}
                              />
                            </div>
                          ))}
                          <Button type="dashed" size="small" onClick={() => addQuery()} block icon={<PlusOutlined />}>
                            添加查询语句
                          </Button>
                        </>
                      )}
                    </Form.List>
                  </Card>
                ))}
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  添加内容项
                </Button>
              </div>
            )}
          </Form.List>

          <div className="sticky bottom-0 bg-opacity-90 py-4 mt-6 z-10 border-t border-gray-700 backdrop-blur-sm">
             <Button type="primary" htmlType="submit" loading={loading} block size="large" icon={<UploadOutlined />}>
              提交任务
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default CreateQueryJob;
