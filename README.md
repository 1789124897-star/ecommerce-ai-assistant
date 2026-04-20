# Ecommerce AI Assistant

一个面向电商运营场景的 AI 后端服务，支持商品分析、营销策略生成、主图生成、详情图生成，并使用 FastAPI、Celery、Redis、MySQL 形成完整的异步任务闭环。

## 技术栈

- FastAPI
- Celery
- Redis
- MySQL
- SQLAlchemy Async ORM
- httpx
- Pillow
- Prometheus
- Docker Compose

## 目录结构

```text
app/
  api/            # 路由层
  core/           # 配置、日志、数据库、Redis、安全
  repositories/   # 数据访问层
  schemas/        # 请求与响应模型
  services/       # 业务逻辑与第三方客户端
  workers/        # Celery 应用与异步任务
  models.py       # ORM 模型
  prompts.py      # AI prompt 模板
  image_utils.py  # 图片校验与压缩
```

## 核心能力

- 商品图文分析：上传商品图和商品信息，生成结构化分析报告
- 营销策略生成：基于分析结果生成 A/B/C 三套电商策略
- 图片异步生成：根据策略生成主图和详情图
- JWT 鉴权：支持 bearer token 访问
- Redis 限流：对高成本接口进行请求限流
- 任务追踪：任务状态、耗时、错误原因、重试次数持久化到 MySQL
- Beat 定时任务：定时执行系统心跳任务，示范 Celery Beat 用法
- 可观测性：开放 `/metrics`、`/health` 与请求日志

## API 入口

- 新版 API 前缀：`/api/v1`
- 兼容旧版接口：保留 `/analyze`、`/generate_strategies`、`/task/result/{task_id}` 等入口，方便旧页面继续使用

## 启动方式

1. 配置 `.env`
2. 启动基础服务

```bash
docker compose up --build
```

3. 打开接口文档

```text
http://localhost:8000/docs
```

## 默认演示账号

- 用户名：`admin`
- 密码：`123456`

如果 `ENABLE_DEMO_MODE=True`，旧页面不带 token 也可以走 demo 用户身份，方便本地演示；生产环境建议关闭。

## 文档

- 架构说明：`docs/architecture.md`
- 任务设计：`docs/task-design.md`
- 部署说明：`docs/deployment.md`
