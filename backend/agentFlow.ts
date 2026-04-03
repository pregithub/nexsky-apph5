/**
 * AI 智能计调流转 - 后端模拟服务
 * 负责生成模拟数据流，展示多机器人之间的动态交互
 */

// 模拟数据配置
const SIMULATION_CONFIG = {
    // 用户下单消息
    userMessages: [
        "我想去云南旅游，3个人，5天4晚",
        "帮我安排一个亲子游线路",
        "需要包含酒店、车辆和导游",
        "预算大概在每人3000元左右"
    ],

    // AI 回复消息
    aiReplies: [
        "好的！我来为您规划这次云南之旅。根据您的需求，我需要先了解一些信息...",
        "根据您的要求，我为您推荐以下行程方案：\n\n📍 目的地：云南大理+丽江\n⏰ 时长：5天4晚\n👨‍👩‍👧 人数：3人\n💰 预算：约9000元（人均3000）",
        "我已经为您匹配了以下资源：\n\n🏨 酒店：大理古城客栈\n🚗 车辆：7座商务车\n🎤 导游：王师傅（资深导游）",
        "好的，您的订单已提交成功！我们会尽快为您确认资源，稍后会有专人与您电话联系确认细节。"
    ],

    // 派发目标机器人
    dispatchTargets: [
        { role: '订单机器人', content: '创建新订单: 云南5日游, 3人' },
        { role: '酒店机器人', content: '搜索酒店: 大理, 4晚, 3人' },
        { role: '车辆机器人', content: '搜索车辆: 7座, 5天' },
        { role: '导游机器人', content: '搜索导游: 云南, 5天' },
        { role: '餐饮机器人', content: '搜索餐厅: 大理+丽江, 5天' },
        { role: '景区机器人', content: '搜索景区: 玉龙雪山, 丽江古城' },
        { role: '计调机器人', content: '生成行程计划' },
        { role: '财务机器人', content: '计算费用明细' }
    ],

    // LangGraph 思考链
    thinkingTasks: [
        { id: '001', title: '🔍 意图识别', summary: '分析用户需求：云南旅游、3人、5天4晚' },
        { id: '002', title: '📋 订单创建', summary: '创建订单记录，生成订单号 ORD-20240315-001' },
        { id: '003', title: '🔎 资源匹配', summary: '并行查询酒店/车辆/导游/餐饮/景区资源' },
        { id: '004', title: '💰 费用计算', summary: '计算总费用：酒店2400+车1500+导800+门票1200=5900元' },
        { id: '005', title: '📝 行程生成', summary: '生成5天4晚详细行程安排' },
        { id: '006', title: '✅ 结果确认', summary: '汇总所有结果，生成最终回复' }
    ]
};

/**
 * 模拟消息数据生成器
 */
class SimulationDataGenerator {
    constructor() {
        this.stepIndex = 0;
        this.messageIndex = 0;
        this.timer = null;
    }

    /**
     * 开始模拟
     */
    start(callback) {
        this.stepIndex = 0;
        this.messageIndex = 0;
        this.sendMessage('USER_MESSAGE', SIMULATION_CONFIG.userMessages[0], callback);

        // 模拟思考过程
        setTimeout(() => this.sendThinking(0, callback), 1000);
    }

    /**
     * 发送聊天消息
     */
    sendMessage(type, content, callback) {
        const data = {
            type: type,
            content: content,
            timestamp: this.formatTime(new Date())
        };
        callback(data);

        if (type === 'USER_MESSAGE' || type === 'AI_FINAL_REPLY') {
            this.messageIndex++;
        }
    }

    /**
     * 发送思考日志
     */
    sendThinking(taskIndex, callback) {
        if (taskIndex >= SIMULATION_CONFIG.thinkingTasks.length) {
            // 思考完成，发送派发消息
            setTimeout(() => this.sendDispatch(0, callback), 500);
            return;
        }

        const task = SIMULATION_CONFIG.thinkingTasks[taskIndex];

        // 发送 pending 状态
        const pendingData = {
            type: 'AI_THINKING_LOG',
            subtask_id: task.id,
            title: task.title,
            status: 'running',
            output_summary: '处理中...',
            timestamp: this.formatTime(new Date())
        };
        callback(pendingData);

        // 1秒后变为完成状态
        setTimeout(() => {
            const completedData = {
                type: 'AI_THINKING_LOG',
                subtask_id: task.id,
                title: task.title,
                status: 'completed',
                output_summary: task.summary,
                timestamp: this.formatTime(new Date())
            };
            callback(completedData);

            // 继续下一个任务
            setTimeout(() => this.sendThinking(taskIndex + 1, callback), 800);
        }, 1000);
    }

    /**
     * 发送派发消息
     */
    sendDispatch(dispatchIndex, callback) {
        if (dispatchIndex >= SIMULATION_CONFIG.dispatchTargets.length) {
            // 派发完成，发送 AI 回复
            if (this.messageIndex < SIMULATION_CONFIG.aiReplies.length) {
                setTimeout(() => {
                    this.sendMessage('AI_FINAL_REPLY', SIMULATION_CONFIG.aiReplies[this.messageIndex], callback);

                    // 发送 SIMULATION_END
                    setTimeout(() => {
                        callback({
                            type: 'SIMULATION_END',
                            timestamp: this.formatTime(new Date())
                        });
                    }, 500);
                }, 1000);
            }
            return;
        }

        const target = SIMULATION_CONFIG.dispatchTargets[dispatchIndex];
        const data = {
            type: 'AI_DISPATCH_MESSAGE',
            target_role: target.role,
            content: target.content,
            timestamp: this.formatTime(new Date())
        };
        callback(data);

        // 每个派发间隔 800ms
        setTimeout(() => this.sendDispatch(dispatchIndex + 1, callback), 800);
    }

    /**
     * 格式化时间
     */
    formatTime(date) {
        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
    }
}

/**
 * WebSocket 消息处理器
 */
class WebSocketHandler {
    constructor(ws) {
        this.ws = ws;
        this.simulation = new SimulationDataGenerator();
    }

    /**
     * 处理客户端消息
     */
    handleMessage(message) {
        console.log('收到客户端消息:', message);

        if (message === 'START_SIMULATION') {
            this.startSimulation();
        }
    }

    /**
     * 开始模拟
     */
    startSimulation() {
        // 发送用户消息
        this.simulation.start((data) => {
            this.sendToClient(data);
        });
    }

    /**
     * 发送消息给客户端
     */
    sendToClient(data) {
        if (this.ws.readyState === 1) { // WebSocket.OPEN
            this.ws.send(JSON.stringify(data));
        }
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        SimulationDataGenerator,
        WebSocketHandler,
        SIMULATION_CONFIG
    };
}