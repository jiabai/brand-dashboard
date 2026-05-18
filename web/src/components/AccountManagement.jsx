import React, { useMemo, useState } from 'react';
import {
  Building2,
  CheckCircle,
  Key,
  Lock,
  Rocket,
  ShieldCheck,
  User,
  UserPlus,
} from 'lucide-react';
import dayjs from 'dayjs';

import {
  activateAuth,
  createPlatformTenant,
  login,
  registerUser,
  verifyInviteCode,
} from '@/api';
import '../styles/account-management.css';

import { Alert, AlertDescription, AlertTitle } from './ui/alert.jsx';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { Card, CardContent } from './ui/card.jsx';
import { Input } from './ui/input.jsx';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select.jsx';
import { Separator } from './ui/separator.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs.jsx';

const initialForms = {
  tenant: {
    tenantName: '',
    industry: '',
    adminName: '',
    adminEmail: '',
    companyLegalName: '',
    companyType: '',
    registrationNo: '',
    adminPhone: '',
    planType: '',
    billingCycle: '',
    maxUsers: '',
    contractStartDate: '',
    contractEndDate: '',
    preferredSubdomain: '',
    salesPersonId: '',
  },
  activate: {
    token: '',
    password: '',
    confirmPassword: '',
  },
  verify: {
    code: '',
  },
  register: {
    inviteCode: '',
    realName: '',
    email: '',
    phoneNumber: '',
    password: '',
  },
  login: {
    email: '',
    password: '',
  },
};

const stripEmpty = (payload) =>
  Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== '' && value !== undefined && value !== null),
  );

const FormField = ({ label, children, required = false }) => (
  <label className="block space-y-1.5">
    <span className="text-sm font-medium text-foreground">
      {label}
      {required ? <span className="text-destructive"> *</span> : null}
    </span>
    {children}
  </label>
);

const ResponseBadge = ({ status }) => {
  if (status === 'success') return <Badge>成功</Badge>;
  if (status === 'error') return <Badge variant="destructive">失败</Badge>;
  return <Badge variant="secondary">待操作</Badge>;
};

const TabLabel = ({ icon: Icon, children }) => (
  <span className="inline-flex items-center gap-1.5">
    <Icon className="size-4" />
    {children}
  </span>
);

const AccountManagement = () => {
  const [forms, setForms] = useState(initialForms);
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
  const [feedback, setFeedback] = useState(null);

  const updateForm = (formKey, field, value) => {
    setForms((current) => ({
      ...current,
      [formKey]: {
        ...current[formKey],
        [field]: value,
      },
    }));
  };

  const setLoading = (key, value) => {
    setLoadingMap((prev) => ({ ...prev, [key]: value }));
  };

  const pushResponse = (title, status, payload) => {
    setLatestResponse({ title, status, payload });
    setFeedback({
      type: status,
      title,
      message: status === 'success' ? payload?.message || '操作成功' : payload?.message || '操作失败',
    });
  };

  const handleOperation = (key, title, operation, prepare = (value) => value) => async (event) => {
    event.preventDefault();
    setLoading(key, true);
    setFeedback(null);
    try {
      const result = await operation(prepare(forms[key]));
      pushResponse(title, 'success', result);
    } catch (error) {
      pushResponse(title, 'error', { message: error.message });
    } finally {
      setLoading(key, false);
    }
  };

  const prepareTenantPayload = (values) =>
    stripEmpty({
      ...values,
      maxUsers: values.maxUsers ? Number(values.maxUsers) : undefined,
      contractStartDate: values.contractStartDate
        ? dayjs(values.contractStartDate).format('YYYY-MM-DD')
        : undefined,
      contractEndDate: values.contractEndDate
        ? dayjs(values.contractEndDate).format('YYYY-MM-DD')
        : undefined,
    });

  const prepareActivatePayload = (values) => {
    if (values.password !== values.confirmPassword) {
      throw new Error('两次输入的密码不一致');
    }
    return stripEmpty({
      token: values.token,
      password: values.password,
      confirmPassword: values.confirmPassword,
    });
  };

  const responsePayload = useMemo(
    () => (latestResponse.payload ? JSON.stringify(latestResponse.payload, null, 2) : '暂无数据'),
    [latestResponse.payload],
  );

  return (
    <div className="account-management">
      <div className="account-hero">
        <div>
          <span className="account-kicker">Account Command Center</span>
          <h2 className="account-title text-2xl font-medium text-foreground">账户与注册管理</h2>
          <p className="account-subtitle text-sm text-muted-foreground">
            租户开通、管理员激活、员工注册与登录流程都集中在这里管理
          </p>
        </div>
        <div className="account-hero-tags">
          <Badge variant="secondary">多租户</Badge>
          <Badge variant="outline">邀请注册</Badge>
          <Badge>安全激活</Badge>
        </div>
      </div>

      {feedback ? (
        <Alert variant={feedback.type === 'error' ? 'destructive' : 'default'}>
          <AlertTitle>{feedback.title}</AlertTitle>
          <AlertDescription>{feedback.message}</AlertDescription>
        </Alert>
      ) : null}

      <div className="account-grid">
        <Card className="account-card">
          <CardContent className="p-4">
            <Tabs defaultValue="tenant">
              <TabsList className="flex h-auto w-full flex-wrap justify-start">
                <TabsTrigger value="tenant">
                  <TabLabel icon={Building2}>租户开通</TabLabel>
                </TabsTrigger>
                <TabsTrigger value="activation">
                  <TabLabel icon={ShieldCheck}>管理员激活</TabLabel>
                </TabsTrigger>
                <TabsTrigger value="register">
                  <TabLabel icon={UserPlus}>员工注册</TabLabel>
                </TabsTrigger>
                <TabsTrigger value="login">
                  <TabLabel icon={User}>账户登录</TabLabel>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="tenant" className="pt-4">
                <form
                  className="account-form space-y-4"
                  onSubmit={handleOperation('tenant', '租户开通', createPlatformTenant, prepareTenantPayload)}
                >
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField label="租户名称" required>
                      <Input
                        required
                        value={forms.tenant.tenantName}
                        onChange={(event) => updateForm('tenant', 'tenantName', event.target.value)}
                        placeholder="例如：阿里巴巴集团"
                      />
                    </FormField>
                    <FormField label="行业" required>
                      <Input
                        required
                        value={forms.tenant.industry}
                        onChange={(event) => updateForm('tenant', 'industry', event.target.value)}
                        placeholder="例如：互联网/电子商务"
                      />
                    </FormField>
                    <FormField label="管理员姓名" required>
                      <Input
                        required
                        value={forms.tenant.adminName}
                        onChange={(event) => updateForm('tenant', 'adminName', event.target.value)}
                        placeholder="例如：张三"
                      />
                    </FormField>
                    <FormField label="管理员邮箱" required>
                      <Input
                        required
                        type="email"
                        value={forms.tenant.adminEmail}
                        onChange={(event) => updateForm('tenant', 'adminEmail', event.target.value)}
                        placeholder="zhangsan@company.com"
                      />
                    </FormField>
                  </div>

                  <details className="account-collapse rounded-md border bg-muted/20 p-4">
                    <summary className="cursor-pointer text-sm font-medium text-foreground">
                      补充企业与合同信息
                    </summary>
                    <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                      <FormField label="企业法定名称">
                        <Input value={forms.tenant.companyLegalName} onChange={(event) => updateForm('tenant', 'companyLegalName', event.target.value)} placeholder="企业法定名称" />
                      </FormField>
                      <FormField label="企业类型">
                        <Input value={forms.tenant.companyType} onChange={(event) => updateForm('tenant', 'companyType', event.target.value)} placeholder="例如：有限责任公司" />
                      </FormField>
                      <FormField label="统一社会信用代码">
                        <Input value={forms.tenant.registrationNo} onChange={(event) => updateForm('tenant', 'registrationNo', event.target.value)} placeholder="例如：91330000748833471G" />
                      </FormField>
                      <FormField label="管理员电话">
                        <Input value={forms.tenant.adminPhone} onChange={(event) => updateForm('tenant', 'adminPhone', event.target.value)} placeholder="例如：13800138000" />
                      </FormField>
                      <FormField label="订阅计划">
                        <Select value={forms.tenant.planType || undefined} onValueChange={(value) => updateForm('tenant', 'planType', value)}>
                          <SelectTrigger>
                            <SelectValue placeholder="选择计划" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectGroup>
                              <SelectItem value="basic">基础版</SelectItem>
                              <SelectItem value="pro">专业版</SelectItem>
                              <SelectItem value="enterprise">企业版</SelectItem>
                            </SelectGroup>
                          </SelectContent>
                        </Select>
                      </FormField>
                      <FormField label="计费周期">
                        <Select value={forms.tenant.billingCycle || undefined} onValueChange={(value) => updateForm('tenant', 'billingCycle', value)}>
                          <SelectTrigger>
                            <SelectValue placeholder="选择周期" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectGroup>
                              <SelectItem value="monthly">按月</SelectItem>
                              <SelectItem value="yearly">按年</SelectItem>
                            </SelectGroup>
                          </SelectContent>
                        </Select>
                      </FormField>
                      <FormField label="最大用户数">
                        <Input type="number" min="1" value={forms.tenant.maxUsers} onChange={(event) => updateForm('tenant', 'maxUsers', event.target.value)} placeholder="例如：200" />
                      </FormField>
                      <FormField label="合同开始日期">
                        <Input type="date" value={forms.tenant.contractStartDate} onChange={(event) => updateForm('tenant', 'contractStartDate', event.target.value)} />
                      </FormField>
                      <FormField label="合同结束日期">
                        <Input type="date" value={forms.tenant.contractEndDate} onChange={(event) => updateForm('tenant', 'contractEndDate', event.target.value)} />
                      </FormField>
                      <FormField label="期望子域名">
                        <Input value={forms.tenant.preferredSubdomain} onChange={(event) => updateForm('tenant', 'preferredSubdomain', event.target.value)} placeholder="例如：alibaba" />
                      </FormField>
                      <FormField label="销售人员编号">
                        <Input value={forms.tenant.salesPersonId} onChange={(event) => updateForm('tenant', 'salesPersonId', event.target.value)} placeholder="例如：SALES_001" />
                      </FormField>
                    </div>
                  </details>

                  <div className="flex flex-wrap items-center gap-3">
                    <Button type="submit" disabled={loadingMap.tenant}>
                      <Rocket className="size-4" />
                      {loadingMap.tenant ? '创建中...' : '创建租户并发送激活邮件'}
                    </Button>
                    <span className="text-sm text-muted-foreground">系统会自动生成租户 Key 与管理员激活链接</span>
                  </div>
                </form>
              </TabsContent>

              <TabsContent value="activation" className="pt-4">
                <form
                  className="account-form space-y-4"
                  onSubmit={handleOperation('activate', '管理员激活', activateAuth, prepareActivatePayload)}
                >
                  <FormField label="激活令牌" required>
                    <Input required value={forms.activate.token} onChange={(event) => updateForm('activate', 'token', event.target.value)} placeholder="邮件中的激活令牌" />
                  </FormField>
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField label="设置密码" required>
                      <Input required type="password" minLength="8" value={forms.activate.password} onChange={(event) => updateForm('activate', 'password', event.target.value)} placeholder="至少 8 位" />
                    </FormField>
                    <FormField label="确认密码" required>
                      <Input required type="password" minLength="8" value={forms.activate.confirmPassword} onChange={(event) => updateForm('activate', 'confirmPassword', event.target.value)} placeholder="再次输入密码" />
                    </FormField>
                  </div>
                  <Button type="submit" disabled={loadingMap.activate}>
                    <CheckCircle className="size-4" />
                    {loadingMap.activate ? '激活中...' : '激活管理员账号'}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register" className="space-y-6 pt-4">
                <Card className="account-subcard">
                  <CardContent className="space-y-4 p-4">
                    <div>
                      <div className="account-section-title">邀请码核验</div>
                      <p className="mt-1 text-sm text-muted-foreground">先验证邀请码，再进行注册，可直接返回租户信息</p>
                    </div>
                    <form className="flex flex-col gap-3 sm:flex-row" onSubmit={handleOperation('verify', '邀请码核验', verifyInviteCode)}>
                      <Input
                        required
                        value={forms.verify.code}
                        onChange={(event) => updateForm('verify', 'code', event.target.value)}
                        placeholder="例如：AB3K9M"
                      />
                      <Button type="submit" disabled={loadingMap.verify}>
                        <Key className="size-4" />
                        {loadingMap.verify ? '核验中...' : '核验'}
                      </Button>
                    </form>
                  </CardContent>
                </Card>

                <form className="account-form space-y-4" onSubmit={handleOperation('register', '员工注册', registerUser, stripEmpty)}>
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField label="邀请码" required>
                      <Input required value={forms.register.inviteCode} onChange={(event) => updateForm('register', 'inviteCode', event.target.value)} placeholder="员工邀请码" />
                    </FormField>
                    <FormField label="真实姓名" required>
                      <Input required value={forms.register.realName} onChange={(event) => updateForm('register', 'realName', event.target.value)} placeholder="例如：李四" />
                    </FormField>
                    <FormField label="邮箱" required>
                      <Input required type="email" value={forms.register.email} onChange={(event) => updateForm('register', 'email', event.target.value)} placeholder="lisi@example.com" />
                    </FormField>
                    <FormField label="手机号">
                      <Input value={forms.register.phoneNumber} onChange={(event) => updateForm('register', 'phoneNumber', event.target.value)} placeholder="可选" />
                    </FormField>
                    <FormField label="设置密码" required>
                      <Input required type="password" minLength="8" value={forms.register.password} onChange={(event) => updateForm('register', 'password', event.target.value)} placeholder="至少 8 位" />
                    </FormField>
                  </div>
                  <Button type="submit" disabled={loadingMap.register}>
                    <UserPlus className="size-4" />
                    {loadingMap.register ? '注册中...' : '完成注册'}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="login" className="pt-4">
                <form className="account-form space-y-4" onSubmit={handleOperation('login', '账户登录', login, stripEmpty)}>
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField label="邮箱" required>
                      <Input required type="email" value={forms.login.email} onChange={(event) => updateForm('login', 'email', event.target.value)} placeholder="lisi@example.com" />
                    </FormField>
                    <FormField label="密码" required>
                      <Input required type="password" value={forms.login.password} onChange={(event) => updateForm('login', 'password', event.target.value)} placeholder="密码" />
                    </FormField>
                  </div>
                  <Button type="submit" disabled={loadingMap.login}>
                    <Lock className="size-4" />
                    {loadingMap.login ? '登录中...' : '登录并获取访问令牌'}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <div className="flex w-full flex-col gap-4">
          <Card className="account-sidecard">
            <CardContent className="space-y-4 p-4">
              <div className="account-section-title">流程守护</div>
              <Alert>
                <AlertTitle>租户唯一性</AlertTitle>
                <AlertDescription>确保平台操作员邮箱与租户名称唯一，否则创建会失败</AlertDescription>
              </Alert>
              <Alert>
                <AlertTitle>激活有效期</AlertTitle>
                <AlertDescription>管理员激活令牌仅一次有效，建议在 7 天内完成激活</AlertDescription>
              </Alert>
              <Separator />
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">
                  <ShieldCheck className="size-3" />
                  Token 校验
                </Badge>
                <Badge variant="outline">
                  <Key className="size-3" />
                  邀请码核验
                </Badge>
                <Badge variant="outline">
                  <Lock className="size-3" />
                  密码强度
                </Badge>
              </div>
            </CardContent>
          </Card>
          <Card className="account-sidecard">
            <CardContent className="space-y-4 p-4">
              <div className="account-section-title">最新响应</div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-foreground">{latestResponse.title}</span>
                <ResponseBadge status={latestResponse.status} />
              </div>
              <div className="account-response">
                <pre>{responsePayload}</pre>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AccountManagement;
