import React, { useMemo, useState } from 'react';
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Space,
  Typography,
  Row,
  Col,
  DatePicker,
  InputNumber,
  Select,
  message,
  Tag,
  Alert,
  Divider,
  Collapse
} from 'antd';
import {
  BankOutlined,
  CheckCircleOutlined,
  KeyOutlined,
  LockOutlined,
  RocketOutlined,
  SafetyCertificateOutlined,
  UserAddOutlined,
  UserOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  activateAuth,
  createPlatformTenant,
  login,
  registerUser,
  verifyInviteCode,
} from '@/api';
import '../styles/account-management.css';

const { Title, Text } = Typography;

const AccountManagement = () => {
  const [messageApi, contextHolder] = message.useMessage();
  const [loadingMap, setLoadingMap] = useState({
    tenant: false,
    activate: false,
    verify: false,
    register: false,
    login: false,
  });
  const [latestResponse, setLatestResponse] = useState({
    title: '等待操作',
    status: 'idle',
    payload: null,
  });

  const setLoading = (key, value) => {
    setLoadingMap((prev) => ({ ...prev, [key]: value }));
  };

  const pushResponse = (title, status, payload) => {
    setLatestResponse({ title, status, payload });
  };

  const handleCreateTenant = async (values) => {
    setLoading('tenant', true);
    try {
      const payload = {
        ...values,
        contractStartDate: values.contractStartDate
          ? dayjs(values.contractStartDate).format('YYYY-MM-DD')
          : undefined,
        contractEndDate: values.contractEndDate
          ? dayjs(values.contractEndDate).format('YYYY-MM-DD')
          : undefined,
      };
      const result = await createPlatformTenant(payload);
      messageApi.success(result?.message || '租户创建成功');
      pushResponse('租户开通', 'success', result);
    } catch (error) {
      messageApi.error(error.message);
      pushResponse('租户开通', 'error', { message: error.message });
    } finally {
      setLoading('tenant', false);
    }
  };

  const handleActivateAdmin = async (values) => {
    setLoading('activate', true);
    try {
      const result = await activateAuth(values);
      messageApi.success(result?.message || '账号激活成功');
      pushResponse('管理员激活', 'success', result);
    } catch (error) {
      messageApi.error(error.message);
      pushResponse('管理员激活', 'error', { message: error.message });
    } finally {
      setLoading('activate', false);
    }
  };

  const handleVerifyInviteCode = async (values) => {
    setLoading('verify', true);
    try {
      const result = await verifyInviteCode(values);
      messageApi.success(result?.message || '邀请码有效');
      pushResponse('邀请码核验', 'success', result);
    } catch (error) {
      messageApi.error(error.message);
      pushResponse('邀请码核验', 'error', { message: error.message });
    } finally {
      setLoading('verify', false);
    }
  };

  const handleRegisterEmployee = async (values) => {
    setLoading('register', true);
    try {
      const result = await registerUser(values);
      messageApi.success(result?.message || '注册成功');
      pushResponse('员工注册', 'success', result);
    } catch (error) {
      messageApi.error(error.message);
      pushResponse('员工注册', 'error', { message: error.message });
    } finally {
      setLoading('register', false);
    }
  };

  const handleLogin = async (values) => {
    setLoading('login', true);
    try {
      const result = await login(values);
      messageApi.success(result?.message || '登录成功');
      pushResponse('账户登录', 'success', result);
    } catch (error) {
      messageApi.error(error.message);
      pushResponse('账户登录', 'error', { message: error.message });
    } finally {
      setLoading('login', false);
    }
  };

  const responseTag = useMemo(() => {
    if (latestResponse.status === 'success') {
      return <Tag color="green">成功</Tag>;
    }
    if (latestResponse.status === 'error') {
      return <Tag color="red">失败</Tag>;
    }
    return <Tag color="default">待操作</Tag>;
  }, [latestResponse.status]);

  const tabs = useMemo(
    () => [
      {
        key: 'tenant',
        label: (
          <Space size={6}>
            <BankOutlined />
            租户开通
          </Space>
        ),
        children: (
          <Form layout="vertical" onFinish={handleCreateTenant} className="account-form">
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Form.Item
                  label="租户名称"
                  name="tenantName"
                  rules={[{ required: true, message: '请输入租户名称' }]}
                >
                  <Input placeholder="例如：阿里巴巴集团" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  label="行业"
                  name="industry"
                  rules={[{ required: true, message: '请输入行业信息' }]}
                >
                  <Input placeholder="例如：互联网/电子商务" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  label="管理员姓名"
                  name="adminName"
                  rules={[{ required: true, message: '请输入管理员姓名' }]}
                >
                  <Input placeholder="例如：张三" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  label="管理员邮箱"
                  name="adminEmail"
                  rules={[
                    { required: true, message: '请输入管理员邮箱' },
                    { type: 'email', message: '邮箱格式不正确' },
                  ]}
                >
                  <Input placeholder="zhangsan@company.com" />
                </Form.Item>
              </Col>
            </Row>
            <Collapse
              className="account-collapse"
              items={[
                {
                  key: 'more',
                  label: '补充企业与合同信息',
                  children: (
                    <Row gutter={[16, 16]}>
                      <Col xs={24} md={12}>
                        <Form.Item label="企业法定名称" name="companyLegalName">
                          <Input placeholder="企业法定名称" />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={12}>
                        <Form.Item label="企业类型" name="companyType">
                          <Input placeholder="例如：有限责任公司" />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={12}>
                        <Form.Item label="统一社会信用代码" name="registrationNo">
                          <Input placeholder="例如：91330000748833471G" />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={12}>
                        <Form.Item label="管理员电话" name="adminPhone">
                          <Input placeholder="例如：13800138000" />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={8}>
                        <Form.Item label="订阅计划" name="planType">
                          <Select
                            placeholder="选择计划"
                            options={[
                              { value: 'basic', label: '基础版' },
                              { value: 'pro', label: '专业版' },
                              { value: 'enterprise', label: '企业版' },
                            ]}
                          />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={8}>
                        <Form.Item label="计费周期" name="billingCycle">
                          <Select
                            placeholder="选择周期"
                            options={[
                              { value: 'monthly', label: '按月' },
                              { value: 'yearly', label: '按年' },
                            ]}
                          />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={8}>
                        <Form.Item label="最大用户数" name="maxUsers">
                          <InputNumber min={1} placeholder="例如：200" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={12}>
                        <Form.Item label="合同开始日期" name="contractStartDate">
                          <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={12}>
                        <Form.Item label="合同结束日期" name="contractEndDate">
                          <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={12}>
                        <Form.Item label="期望子域名" name="preferredSubdomain">
                          <Input placeholder="例如：alibaba" />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={12}>
                        <Form.Item label="销售人员编号" name="salesPersonId">
                          <Input placeholder="例如：SALES_001" />
                        </Form.Item>
                      </Col>
                    </Row>
                  ),
                },
              ]}
            />
            <Space size="middle">
              <Button type="primary" htmlType="submit" loading={loadingMap.tenant} icon={<RocketOutlined />}>
                创建租户并发送激活邮件
              </Button>
              <Text type="secondary">系统会自动生成租户 Key 与管理员激活链接</Text>
            </Space>
          </Form>
        ),
      },
      {
        key: 'activation',
        label: (
          <Space size={6}>
            <SafetyCertificateOutlined />
            管理员激活
          </Space>
        ),
        children: (
          <Form layout="vertical" onFinish={handleActivateAdmin} className="account-form">
            <Row gutter={[16, 16]}>
              <Col xs={24}>
                <Form.Item
                  label="激活令牌"
                  name="token"
                  rules={[{ required: true, message: '请输入激活令牌' }]}
                >
                  <Input prefix={<KeyOutlined />} placeholder="邮件中的激活令牌" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  label="设置密码"
                  name="password"
                  rules={[{ required: true, message: '请输入密码' }, { min: 8, message: '至少 8 位字符' }]}
                >
                  <Input.Password prefix={<LockOutlined />} placeholder="至少 8 位" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  label="确认密码"
                  name="confirmPassword"
                  dependencies={['password']}
                  rules={[
                    { required: true, message: '请再次输入密码' },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('password') === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject(new Error('两次输入的密码不一致'));
                      },
                    }),
                  ]}
                >
                  <Input.Password prefix={<LockOutlined />} placeholder="再次输入密码" />
                </Form.Item>
              </Col>
            </Row>
            <Button type="primary" htmlType="submit" loading={loadingMap.activate} icon={<CheckCircleOutlined />}>
              激活管理员账号
            </Button>
          </Form>
        ),
      },
      {
        key: 'register',
        label: (
          <Space size={6}>
            <UserAddOutlined />
            员工注册
          </Space>
        ),
        children: (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card className="account-subcard" variant="borderless">
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text className="account-section-title">邀请码核验</Text>
                  <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                    先验证邀请码，再进行注册，可直接返回租户信息
                  </Text>
                </div>
                <Form layout="inline" onFinish={handleVerifyInviteCode}>
                  <Form.Item
                    name="code"
                    rules={[{ required: true, message: '请输入邀请码' }]}
                    style={{ flex: 1, minWidth: 200 }}
                  >
                    <Input placeholder="例如：AB3K9M" prefix={<KeyOutlined />} />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loadingMap.verify}>
                      核验
                    </Button>
                  </Form.Item>
                </Form>
              </Space>
            </Card>
            <Form layout="vertical" onFinish={handleRegisterEmployee} className="account-form">
              <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="邀请码"
                    name="inviteCode"
                    rules={[{ required: true, message: '请输入邀请码' }]}
                  >
                    <Input placeholder="员工邀请码" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="真实姓名"
                    name="realName"
                    rules={[{ required: true, message: '请输入姓名' }]}
                  >
                    <Input placeholder="例如：李四" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="邮箱"
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱' },
                      { type: 'email', message: '邮箱格式不正确' },
                    ]}
                  >
                    <Input placeholder="lisi@example.com" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item label="手机号" name="phoneNumber">
                    <Input placeholder="可选" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="设置密码"
                    name="password"
                    rules={[{ required: true, message: '请输入密码' }, { min: 8, message: '至少 8 位字符' }]}
                  >
                    <Input.Password prefix={<LockOutlined />} placeholder="至少 8 位" />
                  </Form.Item>
                </Col>
              </Row>
              <Button type="primary" htmlType="submit" loading={loadingMap.register} icon={<UserAddOutlined />}>
                完成注册
              </Button>
            </Form>
          </Space>
        ),
      },
      {
        key: 'login',
        label: (
          <Space size={6}>
            <UserOutlined />
            账户登录
          </Space>
        ),
        children: (
          <Form layout="vertical" onFinish={handleLogin} className="account-form">
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Form.Item
                  label="邮箱"
                  name="email"
                  rules={[
                    { required: true, message: '请输入邮箱' },
                    { type: 'email', message: '邮箱格式不正确' },
                  ]}
                >
                  <Input placeholder="lisi@example.com" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  label="密码"
                  name="password"
                  rules={[{ required: true, message: '请输入密码' }]}
                >
                  <Input.Password prefix={<LockOutlined />} placeholder="密码" />
                </Form.Item>
              </Col>
            </Row>
            <Button type="primary" htmlType="submit" loading={loadingMap.login} icon={<LockOutlined />}>
              登录并获取访问令牌
            </Button>
          </Form>
        ),
      },
    ],
    [loadingMap, messageApi],
  );

  return (
    <div className="account-management">
      {contextHolder}
      <div className="account-hero">
        <div>
          <Text className="account-kicker">Account Command Center</Text>
          <Title level={2} className="account-title">账户与注册管理</Title>
          <Text type="secondary" className="account-subtitle">
            租户开通、管理员激活、员工注册与登录流程都集中在这里管理
          </Text>
        </div>
        <div className="account-hero-tags">
          <Tag color="gold">多租户</Tag>
          <Tag color="cyan">邀请注册</Tag>
          <Tag color="purple">安全激活</Tag>
        </div>
      </div>
      <div className="account-grid">
        <Card className="account-card" variant="borderless">
          <Tabs items={tabs} />
        </Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Card className="account-sidecard" variant="borderless">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Text className="account-section-title">流程守护</Text>
              <Alert
                type="info"
                showIcon
                message="确保平台操作员邮箱与租户名称唯一，否则创建会失败"
              />
              <Alert
                type="warning"
                showIcon
                message="管理员激活令牌仅一次有效，建议在 7 天内完成激活"
              />
              <Divider style={{ margin: '12px 0' }} />
              <Space size="small" wrap>
                <Tag icon={<SafetyCertificateOutlined />} color="blue">
                  Token 校验
                </Tag>
                <Tag icon={<KeyOutlined />} color="geekblue">
                  邀请码核验
                </Tag>
                <Tag icon={<LockOutlined />} color="volcano">
                  密码强度
                </Tag>
              </Space>
            </Space>
          </Card>
          <Card className="account-sidecard" variant="borderless">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Text className="account-section-title">最新响应</Text>
              <Space size="middle">
                <Text>{latestResponse.title}</Text>
                {responseTag}
              </Space>
              <div className="account-response">
                <pre>{latestResponse.payload ? JSON.stringify(latestResponse.payload, null, 2) : '暂无数据'}</pre>
              </div>
            </Space>
          </Card>
        </Space>
      </div>
    </div>
  );
};

export default AccountManagement;
