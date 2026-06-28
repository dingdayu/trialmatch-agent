# TrialMatch Agent Frontend

Vite + React 前端，用于对接 `../backend` FastAPI 服务，并复用 `~/github/trialmatch-ai` 的临床证据工作台布局与视觉语言。

## 本地运行

```bash
npm install
npm run dev
```

默认通过 Vite proxy 访问后端：`http://127.0.0.1:8000`。如果后端在其他地址，可设置：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

后端默认账号来自 `backend/app/main.py`：

- `admin / admin123`
- `crc001 / 123456`
- `pm001 / 123456`

## 已对接功能

- 登录与 JWT 保存
- 项目列表与项目创建
- 项目详情、项目级 AI 提示词、受试者、入排标准、项目文件
- 受试者创建、标准创建、文件上传
- 最新 AI 初筛结果、证据引用抽屉、人工复核提交、启动初筛、导出报告
- 审计日志与健康检查
