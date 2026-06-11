import React from 'react';
import { ShieldCheck } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '../ui/alert.jsx';

const PlatformReadonlyNotice = () => (
  <Alert>
    <ShieldCheck className="size-4" aria-hidden="true" />
    <AlertTitle>平台只读视角</AlertTitle>
    <AlertDescription>
      你正在以平台管理员身份查看客户项目。此页面仅用于查看、排障和体验客户视角，不提供项目创建、编辑、归档或删除操作。
    </AlertDescription>
  </Alert>
);

export default React.memo(PlatformReadonlyNotice);
