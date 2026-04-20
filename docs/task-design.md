# 异步任务设计

## 队列划分

- `analysis`：商品分析任务
- `strategy`：营销策略生成任务
- `image_gen`：主图与详情图生成任务

这样拆分的目的：

- 避免高耗时任务相互阻塞
- 便于独立扩容 Worker
- 便于观察不同业务队列的堆积情况

## 任务状态流转

任务记录统一落库到 `task_records`：

- `PENDING`：任务已创建，等待消费
- `STARTED`：Worker 已领取任务
- `RETRY`：执行失败并进入重试
- `SUCCESS`：任务执行成功
- `FAILURE`：任务最终失败

同时记录：

- `retry_count`
- `duration_ms`
- `error_message`
- `request_payload`
- `result_payload`

## 重试策略

- 商品分析任务：最多重试 3 次
- 策略生成任务：最多重试 2 次
- 图片生成任务：最多重试 2 次

重试前会将状态更新为 `RETRY` 并记录异常信息，最终失败时转为 `FAILURE`。

## Beat 定时任务

项目内置 `system_heartbeat_task`，由 Celery Beat 每 10 分钟触发一次。

目的：

- 演示 Beat 调度用法
- 验证 Redis 与 Worker 的周期任务链路
- 作为后续扩展定时巡检、失败补偿、统计汇总的基础

## 后续可扩展方向

- 对不同队列设置不同优先级
- 为图片任务增加批次号和幂等键
- 增加任务日志表，记录每次重试和外部请求耗时
- 增加失败任务补偿与人工重放机制
