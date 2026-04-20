# 部署说明

## 环境变量

核心配置来自 `.env`：

- `API_KEY`：第三方 AI 服务 key
- `BASE_URL`：文本/多模态接口地址
- `SEEDREAM_IMAGE_URL`：图片生成接口地址
- `MULTIMODAL_MODEL`：多模态模型
- `DEEPSEEK_MODEL`：策略生成模型
- `SEEDREAM_IMAGE_MODEL`：图片生成模型
- `REDIS_URL`：Redis 连接地址
- `DATABASE_URL`：MySQL 异步连接地址
- `SECRET_KEY`：JWT 密钥

## Docker Compose 服务

- `backend`：FastAPI 服务
- `db`：MySQL
- `redis`：Redis
- `celery_worker`：Celery Worker
- `celery_beat`：Celery Beat

## 启动

```bash
docker compose up --build
```

## 常用访问地址

- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/v1/health`
- Prometheus 指标：`http://localhost:8000/metrics`

## 生产建议

- 关闭 `ENABLE_DEMO_MODE`
- 收紧 `CORS_ORIGINS`
- 将 `SECRET_KEY`、`API_KEY` 配置到安全的密钥管理系统
- 按队列拆分多个 Worker 实例
- 接入 Prometheus + Grafana + Loki / ELK
- 为 MySQL 和 Redis 配置持久化与监控告警
