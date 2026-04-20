# 架构说明

## 总体架构

项目采用典型的 API 服务 + 异步任务中心架构：

1. FastAPI 负责同步接口接入、鉴权、限流、参数校验和任务提交
2. Celery 负责异步任务调度与执行
3. Redis 负责 Broker、结果缓存和限流存储
4. MySQL 负责任务记录、执行状态、错误信息、生成资产落库
5. 第三方 AI 接口负责多模态分析、策略生成、图片生成

## 分层设计

### `app/api`

- 仅负责 HTTP 协议层工作
- 不直接编排第三方接口和数据库事务

### `app/services`

- 封装核心业务逻辑
- 负责任务提交、AI 客户端调用、业务流程编排

### `app/repositories`

- 封装数据库访问
- 统一任务创建、状态更新、资产落库等操作

### `app/workers`

- Celery 应用配置
- Worker 执行逻辑
- Beat 周期任务

### `app/core`

- 配置中心
- 日志
- Redis 客户端
- 安全与 JWT
- 数据库 Session

## 请求链路

### 商品分析

1. 前端调用 `/api/v1/analysis/submit`
2. FastAPI 完成鉴权、限流、入参校验
3. 服务层提交 Celery 分析任务
4. Repository 将任务初始化为 `PENDING`
5. Worker 执行任务并更新状态为 `STARTED`
6. 调用多模态模型生成分析结果
7. 结果写入 MySQL，任务状态变为 `SUCCESS`
8. 查询接口 `/api/v1/tasks/{task_id}` 返回执行状态和结果

### 营销图生成

1. 前端提交生成请求
2. 服务层创建图片生成任务
3. Worker 并发调用图片生成接口
4. 生成结果写入 `generated_assets`
5. 查询接口返回任务结果，页面轮询展示

## 可观测性

- `/api/v1/health`：检查 MySQL、Redis 连通性
- `/metrics`：Prometheus 指标
- `app.log`：应用与任务日志

## 安全策略

- JWT Bearer 鉴权
- Redis 限流
- 图片类型和体积校验
- 统一异常处理与错误响应
