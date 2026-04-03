# H5 Portal - H5 客户门户

H5 客户门户是为客户提供的前端界面，支持订单查询、信息采集、计划书下载等功能。

## 功能概述

### 核心功能
1. **订单管理**：客户查看和管理自己的订单
2. **信息采集**：收集旅客信息和特殊需求
3. **计划书下载**：下载出团计划书和相关文档
4. **进度跟踪**：查看订单处理进度和状态
5. **在线咨询**：与客服进行在线沟通

### 技术特性
- **响应式设计**：适配手机、平板、电脑等多种设备
- **离线支持**：支持离线查看已下载的文档
- **实时更新**：WebSocket 实时更新订单状态
- **多语言支持**：支持中文和英文界面
- **无障碍访问**：符合无障碍访问标准

## 目录结构

```
h5_portal/
├── main.py                    # FastAPI 应用入口
├── config.py                  # 配置管理
├── dependencies.py            # 依赖注入
├── middleware/                # 中间件
│   ├── auth.py               # 认证中间件
│   ├── cors.py               # CORS 中间件
│   └── logging.py            # 日志中间件
├── routes/                    # API 路由
│   ├── orders.py             # 订单相关路由
│   ├── customers.py          # 客户相关路由
│   ├── documents.py          # 文档相关路由
│   └── chat.py               # 聊天相关路由
├── services/                  # 业务逻辑服务
│   ├── order_service.py      # 订单服务
│   ├── customer_service.py   # 客户服务
│   ├── document_service.py   # 文档服务
│   └── chat_service.py       # 聊天服务
├── models/                    # 数据模型
│   ├── schemas.py            # Pydantic 模式
│   ├── database.py           # 数据库模型
│   └── enums.py              # 枚举类型
├── templates/                 # HTML 模板
│   ├── base.html             # 基础模板
│   ├── order_detail.html     # 订单详情页
│   └── document_view.html    # 文档查看页
├── static/                    # 静态资源
│   ├── css/                  # 样式文件
│   ├── js/                   # JavaScript 文件
│   ├── images/               # 图片资源
│   └── fonts/                # 字体文件
└── utils/                     # 工具函数
    ├── validators.py         # 数据验证器
    ├── formatters.py         # 数据格式化
    └── security.py           # 安全工具
```

## API 接口

### 订单相关接口
```
GET    /api/v1/orders                    # 获取订单列表
POST   /api/v1/orders                    # 创建新订单
GET    /api/v1/orders/{order_id}         # 获取订单详情
PUT    /api/v1/orders/{order_id}         # 更新订单信息
GET    /api/v1/orders/{order_id}/status  # 获取订单状态
GET    /api/v1/orders/{order_id}/timeline # 获取订单时间线
```

### 客户相关接口
```
POST   /api/v1/customers/info            # 提交客户信息
PUT    /api/v1/customers/info/{info_id}  # 更新客户信息
GET    /api/v1/customers/requirements    # 获取特殊需求
POST   /api/v1/customers/requirements    # 提交特殊需求
```

### 文档相关接口
```
GET    /api/v1/documents/plans           # 获取计划书列表
GET    /api/v1/documents/plans/{plan_id} # 下载计划书
GET    /api/v1/documents/contracts       # 获取合同列表
GET    /api/v1/documents/contracts/{contract_id} # 下载合同
GET    /api/v1/documents/receipts        # 获取收据列表
GET    /api/v1/documents/receipts/{receipt_id} # 下载收据
```

### 聊天相关接口
```
GET    /api/v1/chat/sessions             # 获取聊天会话
POST   /api/v1/chat/sessions             # 创建聊天会话
GET    /api/v1/chat/sessions/{session_id}/messages # 获取消息
POST   /api/v1/chat/sessions/{session_id}/messages # 发送消息
WS     /api/v1/chat/ws/{session_id}      # WebSocket 连接
```

## 数据模型

### 订单模型
```python
class OrderSchema(BaseModel):
    """订单模式"""
    order_id: str
    order_number: str
    product_name: str
    travel_date: date
    people_count: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    customer_session_id: str
    h5_link: str
    documents: List[DocumentInfo]
```

### 客户信息模型
```python
class CustomerInfoSchema(BaseModel):
    """客户信息模式"""
    info_id: str
    order_id: str
    passengers: List[PassengerInfo]
    emergency_contact: EmergencyContact
    special_requirements: List[str]
    submitted_at: datetime
```

### 文档模型
```python
class DocumentSchema(BaseModel):
    """文档模式"""
    document_id: str
    order_id: str
    document_type: DocumentType
    file_name: str
    file_size: int
    file_url: str
    generated_at: datetime
    version: int
```

## 安全机制

### 身份验证
- **会话ID验证**：通过 customer_session_id 验证用户身份
- **JWT Token**：API 调用使用 JWT Token 验证
- **链接有效期**：H5 链接设置有效期限制
- **访问频率限制**：防止暴力访问

### 数据安全
- **数据脱敏**：敏感信息脱敏显示
- **权限控制**：只能访问自己的数据
- **SQL 注入防护**：参数化查询
- **XSS 防护**：输入输出过滤

### 通信安全
- **HTTPS 加密**：所有通信使用 HTTPS
- **CORS 配置**：严格的跨域配置
- **CSRF 防护**：防止跨站请求伪造
- **内容安全策略**：CSP 策略配置

## 性能优化

### 前端优化
- **代码分割**：按需加载 JavaScript
- **图片优化**：图片压缩和懒加载
- **缓存策略**：静态资源缓存
- **CDN 加速**：使用 CDN 加速静态资源

### 后端优化
- **数据库索引**：优化查询性能
- **查询缓存**：缓存热点数据
- **连接池**：数据库连接池管理
- **异步处理**：耗时操作异步处理

### 网络优化
- **HTTP/2**：使用 HTTP/2 协议
- **Gzip 压缩**：响应数据压缩
- **资源合并**：合并 CSS 和 JavaScript
- **域名分片**：多个域名并行加载

## 部署配置

### 环境变量
```bash
# 数据库配置
DATABASE_URL=mysql://user:password@localhost:3306/h5_portal
REDIS_URL=redis://localhost:6379/0

# 应用配置
APP_ENV=production
APP_SECRET_KEY=your-secret-key
APP_DEBUG=false

# 文件存储
OSS_ENDPOINT=your-oss-endpoint
OSS_ACCESS_KEY=your-access-key
OSS_SECRET_KEY=your-secret-key
OSS_BUCKET=your-bucket

# 安全配置
JWT_SECRET_KEY=your-jwt-secret
SESSION_EXPIRE_HOURS=24
RATE_LIMIT_PER_MINUTE=60
```

### Docker 配置
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 测试要求

### 单元测试
- 服务层单元测试覆盖率 85%+
- 工具函数单元测试覆盖率 90%+
- 数据验证单元测试覆盖率 95%+

### 集成测试
- API 接口集成测试
- 数据库操作集成测试
- 文件上传下载集成测试
- WebSocket 连接集成测试

### 端到端测试
- 用户注册登录流程
- 订单创建查看流程
- 文档下载查看流程
- 在线聊天沟通流程

## 监控告警

### 应用监控
- **请求响应时间**：监控 API 响应时间
- **错误率监控**：监控错误请求比例
- **资源使用监控**：监控 CPU、内存使用
- **数据库监控**：监控数据库性能

### 业务监控
- **订单创建数量**：监控订单创建趋势
- **用户活跃度**：监控用户活跃情况
- **文档下载次数**：监控文档下载情况
- **聊天消息数量**：监控聊天活跃度

### 安全监控
- **异常访问监控**：监控异常访问行为
- **安全事件监控**：监控安全相关事件
- **数据泄露监控**：监控数据泄露风险
- **合规性监控**：监控合规性要求

## 维护说明

### 日常维护
- **日志分析**：定期分析应用日志
- **性能优化**：持续优化应用性能
- **安全更新**：及时更新安全补丁
- **备份恢复**：定期备份和恢复测试

### 版本发布
- **版本规划**：制定版本发布计划
- **测试验证**：发布前充分测试验证
- **回滚预案**：准备版本回滚预案
- **文档更新**：同步更新相关文档

### 故障处理
- **故障诊断**：快速诊断故障原因
- **应急处理**：执行应急处理流程
- **根本原因分析**：分析故障根本原因
- **预防措施**：制定预防措施