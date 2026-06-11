import React, { useMemo, useState } from 'react';
import {
  Building2,
  Key,
  KeyRound,
  Lock,
  ShieldCheck,
  User,
  UserPlus,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import {
  changePassword,
  login as loginApi,
  registerUser,
  verifyInviteCode,
} from '@/api';
import { useAuth } from '../auth/AuthContext.jsx';
import '../styles/account-management.css';

import { Alert, AlertDescription, AlertTitle } from './ui/alert.jsx';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { Card, CardContent } from './ui/card.jsx';
import { Input } from './ui/input.jsx';
import { Separator } from './ui/separator.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs.jsx';

const initialForms = {
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
  password: {
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
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
  const { user } = useAuth();
  const [forms, setForms] = useState(initialForms);
  const [loadingMap, setLoadingMap] = useState({
    verify: false,
    register: false,
    password: false,
    login: false,
  });
  const [latestResponse, setLatestResponse] = useState({
    title: '等待操作',
    status: 'idle',
    payload: null,
  });
  const [feedback, setFeedback] = useState(null);
  const platformRoles = user?.platformRoles || [];
  const isPlatformAdmin = platformRoles.includes('platform_admin');

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

  const handleChangePassword = async (event) => {
    event.preventDefault();
    if (forms.password.newPassword !== forms.password.confirmPassword) {
      setFeedback({ type: 'error', title: '修改密码', message: '两次输入的新密码不一致' });
      return;
    }
    setLoading('password', true);
    setFeedback(null);
    try {
      const result = await changePassword(stripEmpty(forms.password));
      pushResponse('修改密码', 'success', result);
      setForms((current) => ({
        ...current,
        password: { currentPassword: '', newPassword: '', confirmPassword: '' },
      }));
    } catch (error) {
      pushResponse('修改密码', 'error', { message: error.message });
    } finally {
      setLoading('password', false);
    }
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
            租户入口、员工注册与登录辅助流程集中在这里管理
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
                <TabsTrigger value="register">
                  <TabLabel icon={UserPlus}>员工注册</TabLabel>
                </TabsTrigger>
                <TabsTrigger value="login">
                  <TabLabel icon={User}>账户登录</TabLabel>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="tenant" className="pt-4">
                <div className="space-y-4">
                  <Alert>
                    <AlertTitle>租户开通已迁移到平台运营后台</AlertTitle>
                    <AlertDescription>
                      租户工作台保留员工注册与邀请码核验；企业租户创建请从平台运营后台执行。
                    </AlertDescription>
                  </Alert>
                  <div className="flex flex-wrap items-center gap-3">
                    {isPlatformAdmin ? (
                      <Button asChild>
                        <Link to="/platform/tenants">
                          <Building2 className="size-4" />
                          进入平台租户管理
                        </Link>
                      </Button>
                    ) : (
                      <Badge variant="secondary">当前账号无平台运营权限</Badge>
                    )}
                  </div>
                </div>
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
                <form className="account-form space-y-4" onSubmit={handleOperation('login', '账户登录', loginApi, stripEmpty)}>
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

            <form className="account-form space-y-4" onSubmit={handleChangePassword}>
              <div>
                <div className="account-section-title">修改密码</div>
                <p className="mt-1 text-sm text-muted-foreground">
                  验证当前密码后设置新密码；修改成功后下次登录使用新密码。
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <FormField label="当前密码" required>
                  <Input required type="password" autoComplete="current-password" value={forms.password.currentPassword} onChange={(event) => updateForm('password', 'currentPassword', event.target.value)} placeholder="输入当前密码" />
                </FormField>
                <FormField label="新密码" required>
                  <Input required type="password" minLength="8" autoComplete="new-password" value={forms.password.newPassword} onChange={(event) => updateForm('password', 'newPassword', event.target.value)} placeholder="至少 8 位" />
                </FormField>
                <FormField label="确认新密码" required>
                  <Input required type="password" minLength="8" autoComplete="new-password" value={forms.password.confirmPassword} onChange={(event) => updateForm('password', 'confirmPassword', event.target.value)} placeholder="再次输入新密码" />
                </FormField>
              </div>
              <Button type="submit" disabled={loadingMap.password}>
                <KeyRound className="size-4" />
                {loadingMap.password ? '提交中...' : '修改密码'}
              </Button>
            </form>
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
                <AlertTitle>首次设置密码</AlertTitle>
                <AlertDescription>客户管理员应通过邮件中的公开链接完成首次设置密码，账户页不承载登录前流程</AlertDescription>
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
