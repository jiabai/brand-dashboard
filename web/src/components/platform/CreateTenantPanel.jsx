import React, { useMemo, useState } from 'react';
import { Check, Copy, Loader2, Plus } from 'lucide-react';

import { createPlatformTenant } from '../../api/platform.js';
import { Button } from '../ui/button.jsx';
import { Input } from '../ui/input.jsx';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select.jsx';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '../ui/sheet.jsx';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert.jsx';
import { prepareTenantCreatePayload } from './tenantPresentation.js';

const initialForm = {
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
};

const Field = ({ label, required = false, children }) => (
  <label className="grid gap-1.5">
    <span className="text-sm font-medium text-foreground">
      {label}
      {required ? <span className="text-destructive"> *</span> : null}
    </span>
    {children}
  </label>
);

const ResultRow = ({ label, value, onCopy, copied }) => (
  <div className="grid gap-1 rounded-md border border-border bg-background p-3">
    <span className="text-xs font-medium text-muted-foreground">{label}</span>
    <div className="flex min-w-0 items-center gap-2">
      <code className="min-w-0 flex-1 truncate text-xs text-foreground">{value || '未返回'}</code>
      {value ? (
        <Button type="button" variant="outline" size="icon-sm" onClick={() => onCopy(value, label)} title={`复制${label}`}>
          {copied === label ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
        </Button>
      ) : null}
    </div>
  </div>
);

const CreateTenantPanel = ({ onCreated, latestResult }) => {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(initialForm);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState('');

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const createResult = latestResult?.data || latestResult || null;

  const canSubmit = useMemo(
    () => form.tenantName.trim() && form.industry.trim() && form.adminName.trim() && form.adminEmail.trim(),
    [form],
  );

  const handleCopy = async (value, label) => {
    if (!navigator?.clipboard) return;
    await navigator.clipboard.writeText(value);
    setCopied(label);
    window.setTimeout(() => setCopied(''), 1600);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!canSubmit) return;

    setIsSubmitting(true);
    setError('');
    try {
      const result = await createPlatformTenant(prepareTenantCreatePayload(form));
      onCreated?.(result);
      setForm(initialForm);
      setOpen(false);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="grid gap-3">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button type="button">
            <Plus className="size-4" />
            创建租户
          </Button>
        </SheetTrigger>
        <SheetContent className="w-full overflow-y-auto sm:max-w-xl">
          <SheetHeader>
            <SheetTitle>创建企业租户</SheetTitle>
            <SheetDescription>提交后将生成首个管理员激活链接和员工邀请码。</SheetDescription>
          </SheetHeader>
          <form id="platform-create-tenant" className="grid gap-4 px-4 pb-4" onSubmit={handleSubmit}>
            {error ? (
              <Alert variant="destructive">
                <AlertTitle>创建失败</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}

            <div className="grid gap-4 md:grid-cols-2">
              <Field label="租户名称" required>
                <Input required value={form.tenantName} onChange={(event) => updateField('tenantName', event.target.value)} placeholder="例如：Acme 中国" />
              </Field>
              <Field label="行业" required>
                <Input required value={form.industry} onChange={(event) => updateField('industry', event.target.value)} placeholder="例如：软件服务" />
              </Field>
              <Field label="管理员姓名" required>
                <Input required value={form.adminName} onChange={(event) => updateField('adminName', event.target.value)} placeholder="例如：Alice" />
              </Field>
              <Field label="管理员邮箱" required>
                <Input required type="email" value={form.adminEmail} onChange={(event) => updateField('adminEmail', event.target.value)} placeholder="admin@example.com" />
              </Field>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <Field label="企业法定名称">
                <Input value={form.companyLegalName} onChange={(event) => updateField('companyLegalName', event.target.value)} />
              </Field>
              <Field label="企业类型">
                <Input value={form.companyType} onChange={(event) => updateField('companyType', event.target.value)} />
              </Field>
              <Field label="统一社会信用代码">
                <Input value={form.registrationNo} onChange={(event) => updateField('registrationNo', event.target.value)} />
              </Field>
              <Field label="管理员电话">
                <Input value={form.adminPhone} onChange={(event) => updateField('adminPhone', event.target.value)} />
              </Field>
              <Field label="订阅计划">
                <Select value={form.planType || undefined} onValueChange={(value) => updateField('planType', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择计划" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectItem value="trial">试用版</SelectItem>
                      <SelectItem value="basic">基础版</SelectItem>
                      <SelectItem value="pro">专业版</SelectItem>
                      <SelectItem value="enterprise">企业版</SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="计费周期">
                <Select value={form.billingCycle || undefined} onValueChange={(value) => updateField('billingCycle', value)}>
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
              </Field>
              <Field label="最大用户数">
                <Input type="number" min="1" value={form.maxUsers} onChange={(event) => updateField('maxUsers', event.target.value)} />
              </Field>
              <Field label="期望子域名">
                <Input value={form.preferredSubdomain} onChange={(event) => updateField('preferredSubdomain', event.target.value)} />
              </Field>
              <Field label="合同开始日期">
                <Input type="date" value={form.contractStartDate} onChange={(event) => updateField('contractStartDate', event.target.value)} />
              </Field>
              <Field label="合同结束日期">
                <Input type="date" value={form.contractEndDate} onChange={(event) => updateField('contractEndDate', event.target.value)} />
              </Field>
              <Field label="销售人员编号">
                <Input value={form.salesPersonId} onChange={(event) => updateField('salesPersonId', event.target.value)} />
              </Field>
            </div>
          </form>
          <SheetFooter>
            <Button type="submit" form="platform-create-tenant" disabled={!canSubmit || isSubmitting}>
              {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
              {isSubmitting ? '创建中...' : '创建租户'}
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      {createResult ? (
        <section className="grid gap-3 rounded-md border border-border bg-muted/30 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-medium text-foreground">最近创建结果</h3>
              <p className="text-xs text-muted-foreground">激活链接只在本次结果中展示。</p>
            </div>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <ResultRow label="tenantKey" value={createResult.tenantKey} onCopy={handleCopy} copied={copied} />
            <ResultRow label="管理员邮箱" value={createResult.adminEmail} onCopy={handleCopy} copied={copied} />
            <ResultRow label="激活链接" value={createResult.activationUrl} onCopy={handleCopy} copied={copied} />
            <ResultRow label="邀请码" value={createResult.inviteCode} onCopy={handleCopy} copied={copied} />
            <ResultRow label="登录地址" value={createResult.loginUrl} onCopy={handleCopy} copied={copied} />
          </div>
        </section>
      ) : null}
    </div>
  );
};

export default CreateTenantPanel;
