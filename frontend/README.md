# 前端初始化骨架

沿用原项目 Vue 3 + Vite 与 src 下的文件组织；页面、组件和接口调用保留 TODO。

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

访问 `http://127.0.0.1:5173`。开发代理将 `/api` 转发至 `http://127.0.0.1:8000`。
需要修改代理时，将 `.env.example` 复制为 `.env.local` 并设置 `API_PROXY_TARGET`。
构建命令：`npm.cmd run build`。
