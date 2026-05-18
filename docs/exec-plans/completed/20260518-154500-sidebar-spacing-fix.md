# Sidebar 间距与触控目标修复

## 背景

SidebarMenu 使用 `gap-0`（见 `sidebar.jsx` 第 428 行），每个 SidebarMenuButton 默认高度仅 `h-8`（32px），远低于触控最低标准 44×44pt。桌面端鼠标操作问题不大，但 32px 行高加上 0 间距，视觉上确实显得局促。

## 目标

- 提升侧边栏菜单的视觉呼吸感
- 满足最小触控目标要求（44px）
- 保持折叠为 icon 模式时的紧凑性
- 不破坏现有 shadcn/ui Sidebar 的 API 契约

## 方案

### 变更 1：SidebarMenu gap 从 0 提升到 1

```diff
- className={cn("flex w-full min-w-0 flex-col gap-0", className)}
+ className={cn("flex w-full min-w-0 flex-col gap-1", className)}
```

理由：
- 父菜单 `gap-0` 而子菜单 `SidebarMenuSub` 用 `gap-1`，粗细倒挂
- `gap-1`（4px）是 shadcn/ui 其他组件（如 SidebarGroup、SidebarHeader）的常用间距
- 视觉上增加呼吸感，不显著增加总高度

### 变更 2：SidebarMenuButton 默认高度从 h-8 提升到 h-9

```diff
size: {
-   default: "h-8 text-sm",
+   default: "h-9 text-sm",
    sm: "h-7 text-xs",
    lg: "h-12 text-sm group-data-[collapsible=icon]:p-0!",
}
```

理由：
- `h-9` = 36px，更接近 44px 触控标准，同时不破坏桌面紧凑感
- 保持 `sm`（28px）和 `lg`（48px）不变，供调用方按需选择
- `group-data-[collapsible=icon]:size-8!` 保持折叠态 32px 正方形，icon 模式不需要文字高度

### 变更 3：SidebarMenuSkeleton 同步高度

```diff
- className={cn("flex h-8 items-center gap-2 rounded-md px-2", className)}
+ className={cn("flex h-9 items-center gap-2 rounded-md px-2", className)}
```

理由：骨架屏高度应与实际菜单按钮一致。

### 不变更项

| 组件 | 理由 |
|------|------|
| SidebarGroupLabel (h-8) | 标签不是交互元素，不需要触控目标 |
| SidebarInput (h-8) | 输入框有自身 padding，实际可点击区域足够 |
| SidebarMenuSubButton (h-7) | 子菜单按钮保持紧凑，由父级 gap-1 补偿 |
| SidebarContent (gap-0) | 内容区负责滚动，内部由 SidebarGroup p-2 控制间距 |

## 验证记录

- [x] 启动前端 dev server，展开态和折叠态侧边栏渲染正常
- [x] 菜单项 hover/active 状态正常
- [x] 无布局错位或溢出
- [x] `npm --prefix web run build` 构建通过

## 决策日志

| 时间 | 决策 | 原因 |
|------|------|------|
| 2026-05-18 | 高度从 h-8 改为 h-9 而非 h-10 | h-10（40px）过于接近 44px 但会显著增加侧边栏总高度，h-9 是视觉与触控的最佳平衡点 |
| 2026-05-18 | 不修改 SidebarMenuSubButton | 子菜单已有 gap-1，保持 h-7 可维持层级缩进的紧凑感 |

## 残余风险

- 侧边栏总高度略微增加（每项 +4px gap + 4px 高度），菜单较多时可能需要更多滚动空间
- 如影响严重，可回退为仅调 gap 不调高度
