## Summary
允许 Vite 开发服务器通过 `rushlink.click` 域名访问。

## Code Highlights
- [vite.config.js](file:///d:/Github/brand-dashboard/web/vite.config.js): 在 `server` 配置中添加了 `allowedHosts: ['rushlink.click']`。

## Self-Tests
- 手动检查了 `vite.config.js` 的语法。
- 确认配置符合 Vite 6+ 的域名限制修复建议。