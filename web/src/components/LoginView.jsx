import React, { useEffect, useMemo, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { CheckCircle2, KeyRound, Lock, UserPlus } from 'lucide-react';

import { activateAuth, registerUser, verifyInviteCode } from '../api/auth.js';
import { useAuth } from '../auth/AuthContext.jsx';
import { getLoginRedirectTarget } from '../auth/redirect.js';
import { Alert, AlertDescription, AlertTitle } from './ui/alert.jsx';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { Card, CardContent } from './ui/card.jsx';
import { Input } from './ui/input.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs.jsx';

const initialForms = {
  login: {
    email: '',
    password: '',
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
};

const stripEmpty = (payload) =>
  Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== '' && value !== null && value !== undefined),
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

const LoginView = ({ defaultTab = 'login' }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentTenantKey, isAuthenticated, isInitializing, login, session } = useAuth();
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [forms, setForms] = useState(initialForms);
  const [loadingKey, setLoadingKey] = useState('');
  const [feedback, setFeedback] = useState(null);

  useEffect(() => {
    setActiveTab(defaultTab);
  }, [defaultTab]);

  const updateForm = (formKey, field, value) => {
    setForms((current) => ({
      ...current,
      [formKey]: {
        ...current[formKey],
        [field]: value,
      },
    }));
  };

  const setResult = (type, title, message) => {
    setFeedback({ type, title, message });
  };

  const handleLogin = async (event) => {
    event.preventDefault();
    setLoadingKey('login');
    setFeedback(null);
    try {
      const session = await login(stripEmpty(forms.login));
      navigate(
        getLoginRedirectTarget({
          location,
          session,
          tenantKey: session.currentTenantKey,
        }),
        { replace: true },
      );
    } catch (error) {
      setResult('error', '登录失败', error.message);
    } finally {
      setLoadingKey('');
    }
  };

  const handleActivate = async (event) => {
    event.preventDefault();
    if (forms.activate.password !== forms.activate.confirmPassword) {
      setResult('error', '激活失败', '两次输入的密码不一致');
      return;
    }

    setLoadingKey('activate');
    setFeedback(null);
    try {
      const result = await activateAuth(stripEmpty(forms.activate));
      setResult('success', '账号已激活', result?.message || '请使用新密码登录');
      setActiveTab('login');
    } catch (error) {
      setResult('error', '激活失败', error.message);
    } finally {
      setLoadingKey('');
    }
  };

  const handleVerifyInvite = async (event) => {
    event.preventDefault();
    setLoadingKey('verify');
    setFeedback(null);
    try {
      const result = await verifyInviteCode(stripEmpty(forms.verify));
      updateForm('register', 'inviteCode', forms.verify.code);
      setResult('success', '邀请码有效', result?.data?.tenantName || result?.message || '可以继续注册');
    } catch (error) {
      setResult('error', '邀请码无效', error.message);
    } finally {
      setLoadingKey('');
    }
  };

  const handleRegister = async (event) => {
    event.preventDefault();
    setLoadingKey('register');
    setFeedback(null);
    try {
      const result = await registerUser(stripEmpty(forms.register));
      updateForm('login', 'email', forms.register.email);
      setResult('success', '注册成功', result?.message || '请使用刚设置的账号登录');
      setActiveTab('login');
    } catch (error) {
      setResult('error', '注册失败', error.message);
    } finally {
      setLoadingKey('');
    }
  };

  const feedbackNode = useMemo(() => {
    if (!feedback) return null;
    return (
      <Alert variant={feedback.type === 'error' ? 'destructive' : 'default'}>
        <AlertTitle>{feedback.title}</AlertTitle>
        <AlertDescription>{feedback.message}</AlertDescription>
      </Alert>
    );
  }, [feedback]);

  if (!isInitializing && isAuthenticated && activeTab === 'login') {
    return (
      <Navigate
        to={getLoginRedirectTarget({ location, session, tenantKey: currentTenantKey })}
        replace
      />
    );
  }

  return (
    <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-3rem)] w-full max-w-5xl items-center gap-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(360px,440px)]">
        <section className="min-w-0 space-y-5">
          <div className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-3 py-1.5 text-sm font-medium text-muted-foreground">
            <span className="grid size-5 place-items-center rounded-sm bg-primary text-xs text-primary-foreground">明</span>
            InsightFlow
          </div>
          <div className="space-y-3">
            <h1 className="max-w-xl text-4xl font-medium leading-tight text-foreground sm:text-5xl">
              明察品牌数据工作台
            </h1>
            <p className="max-w-xl text-base leading-7 text-muted-foreground">
              企业租户登录后进入自己的数据空间，平台会按账号、租户和角色完成访问校验。
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">JWT 登录态</Badge>
            <Badge variant="outline">租户上下文</Badge>
            <Badge variant="outline">角色授权</Badge>
          </div>
        </section>

        <Card className="w-full rounded-lg border-border shadow-none">
          <CardContent className="space-y-5 p-5 sm:p-6">
            <div className="space-y-1">
              <h2 className="text-xl font-medium text-foreground">账户访问</h2>
              <p className="text-sm text-muted-foreground">登录、激活管理员账号或通过邀请码注册员工账号</p>
            </div>

            {feedbackNode}

            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid h-auto w-full grid-cols-3">
                <TabsTrigger value="login">登录</TabsTrigger>
                <TabsTrigger value="activate">激活</TabsTrigger>
                <TabsTrigger value="register">注册</TabsTrigger>
              </TabsList>

              <TabsContent value="login" className="pt-4">
                <form className="space-y-4" onSubmit={handleLogin}>
                  <FormField label="邮箱" required>
                    <Input
                      required
                      type="email"
                      autoComplete="email"
                      value={forms.login.email}
                      onChange={(event) => updateForm('login', 'email', event.target.value)}
                      placeholder="name@company.com"
                    />
                  </FormField>
                  <FormField label="密码" required>
                    <Input
                      required
                      type="password"
                      autoComplete="current-password"
                      value={forms.login.password}
                      onChange={(event) => updateForm('login', 'password', event.target.value)}
                      placeholder="输入密码"
                    />
                  </FormField>
                  <Button type="submit" className="w-full" disabled={loadingKey === 'login'}>
                    <Lock className="size-4" />
                    {loadingKey === 'login' ? '登录中...' : '登录'}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="activate" className="pt-4">
                <form className="space-y-4" onSubmit={handleActivate}>
                  <FormField label="激活令牌" required>
                    <Input
                      required
                      value={forms.activate.token}
                      onChange={(event) => updateForm('activate', 'token', event.target.value)}
                      placeholder="邮件中的激活令牌"
                    />
                  </FormField>
                  <FormField label="设置密码" required>
                    <Input
                      required
                      type="password"
                      minLength="8"
                      autoComplete="new-password"
                      value={forms.activate.password}
                      onChange={(event) => updateForm('activate', 'password', event.target.value)}
                      placeholder="至少 8 位"
                    />
                  </FormField>
                  <FormField label="确认密码" required>
                    <Input
                      required
                      type="password"
                      minLength="8"
                      autoComplete="new-password"
                      value={forms.activate.confirmPassword}
                      onChange={(event) => updateForm('activate', 'confirmPassword', event.target.value)}
                      placeholder="再次输入密码"
                    />
                  </FormField>
                  <Button type="submit" className="w-full" disabled={loadingKey === 'activate'}>
                    <CheckCircle2 className="size-4" />
                    {loadingKey === 'activate' ? '激活中...' : '激活账号'}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register" className="space-y-5 pt-4">
                <form className="flex flex-col gap-3 sm:flex-row" onSubmit={handleVerifyInvite}>
                  <Input
                    required
                    value={forms.verify.code}
                    onChange={(event) => updateForm('verify', 'code', event.target.value)}
                    placeholder="邀请码"
                  />
                  <Button type="submit" variant="outline" disabled={loadingKey === 'verify'}>
                    <KeyRound className="size-4" />
                    {loadingKey === 'verify' ? '核验中...' : '核验'}
                  </Button>
                </form>

                <form className="space-y-4" onSubmit={handleRegister}>
                  <FormField label="邀请码" required>
                    <Input
                      required
                      value={forms.register.inviteCode}
                      onChange={(event) => updateForm('register', 'inviteCode', event.target.value)}
                      placeholder="员工邀请码"
                    />
                  </FormField>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <FormField label="姓名" required>
                      <Input
                        required
                        value={forms.register.realName}
                        onChange={(event) => updateForm('register', 'realName', event.target.value)}
                        placeholder="真实姓名"
                      />
                    </FormField>
                    <FormField label="手机号">
                      <Input
                        value={forms.register.phoneNumber}
                        onChange={(event) => updateForm('register', 'phoneNumber', event.target.value)}
                        placeholder="可选"
                      />
                    </FormField>
                  </div>
                  <FormField label="邮箱" required>
                    <Input
                      required
                      type="email"
                      autoComplete="email"
                      value={forms.register.email}
                      onChange={(event) => updateForm('register', 'email', event.target.value)}
                      placeholder="name@company.com"
                    />
                  </FormField>
                  <FormField label="密码" required>
                    <Input
                      required
                      type="password"
                      minLength="8"
                      autoComplete="new-password"
                      value={forms.register.password}
                      onChange={(event) => updateForm('register', 'password', event.target.value)}
                      placeholder="至少 8 位"
                    />
                  </FormField>
                  <Button type="submit" className="w-full" disabled={loadingKey === 'register'}>
                    <UserPlus className="size-4" />
                    {loadingKey === 'register' ? '注册中...' : '完成注册'}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>

            <div className="text-center text-sm text-muted-foreground">
              <Link to="/login" className="font-medium text-primary hover:underline">
                返回登录入口
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
};

export default LoginView;
