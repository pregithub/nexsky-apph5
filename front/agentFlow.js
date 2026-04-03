/**
 * AI 智能计调流转监控大屏 - 前端脚本
 * 处理 WebSocket 连接、动态节点展示、数据流向可视化
 */

class AgentFlowMonitor {
    constructor() {
        this.ws = null;
        this.nodes = new Map();
        this.isConnected = false;
        this.messageCount = 0;
        this.taskCount = 0;
        this.activeNodes = new Set();

        // 机器人节点配置 - 只显示核心节点，其他动态展示
        this.nodeConfig = {
            // 核心调度中心 - 初始显示
            'AI大脑': {
                icon: '🤖',
                type: 'core',
                x: 0.5,
                y: 0.5,
                description: 'AI智能调度中心',
                initial: true
            },
            // 资源对接方 - 动态展示
            '地接方': {
                icon: '🏢',
                type: 'resource',
                x: 0.2,
                y: 0.3,
                description: '地接社资源对接',
                resourceType: 'ground'
            },
            '酒店方': {
                icon: '🏨',
                type: 'resource',
                x: 0.8,
                y: 0.3,
                description: '酒店资源匹配',
                resourceType: 'hotel'
            },
            '车辆方': {
                icon: '🚗',
                type: 'resource',
                x: 0.15,
                y: 0.6,
                description: '车队调度匹配',
                resourceType: 'vehicle'
            },
            '导游方': {
                icon: '🎤',
                type: 'resource',
                x: 0.85,
                y: 0.6,
                description: '导游资源匹配',
                resourceType: 'guide'
            },
            '餐饮方': {
                icon: '🍽️',
                type: 'resource',
                x: 0.3,
                y: 0.8,
                description: '餐厅资源匹配',
                resourceType: 'restaurant'
            }
        };

        // 数据流类型映射
        this.resourceTypeMap = {
            'ground': '地接方',
            'hotel': '酒店方',
            'vehicle': '车辆方',
            'guide': '导游方',
            'restaurant': '餐饮方'
        };

        this.init();
    }

    init() {
        this.bindEvents();
        this.initNetworkTopology();
        this.connect();
    }

    bindEvents() {
        // 开始模拟按钮
        document.getElementById('startBtn').addEventListener('click', () => {
            this.startSimulation();
        });

        // 清空按钮
        document.getElementById('clearBtn').addEventListener('click', () => {
            this.clearAll();
        });
    }

    // 初始化网络拓扑图 - 只显示初始节点
    initNetworkTopology() {
        const container = document.getElementById('networkNodes');
        const svg = document.getElementById('networkSvg');

        // 创建节点
        Object.entries(this.nodeConfig).forEach(([name, config]) => {
            const node = document.createElement('div');
            node.className = `network-node ${config.type}`;
            node.id = `node-${name}`;
            node.style.left = `${config.x * 100}%`;
            node.style.top = `${config.y * 100}%`;
            node.innerHTML = `
                <span class="node-icon">${config.icon}</span>
                <span class="node-name">${name}</span>
            `;
            node.title = config.description;

            // 只显示初始节点
            if (config.initial) {
                node.classList.add('visible');
                this.activeNodes.add(name);
            }

            container.appendChild(node);
            this.nodes.set(name, { ...config, element: node });
        });
    }

    // 动态显示节点
    showNode(nodeName) {
        const nodeData = this.nodes.get(nodeName);
        if (!nodeData || !nodeData.element) return;

        if (!this.activeNodes.has(nodeName)) {
            nodeData.element.classList.add('visible');
            this.activeNodes.add(nodeName);
        }
    }

    // 创建连线
    createEdge(fromName, toName) {
        const from = this.nodes.get(fromName);
        const to = this.nodes.get(toName);
        if (!from || !to) return;

        const svg = document.getElementById('networkSvg');
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');

        const x1 = from.x * 100;
        const y1 = from.y * 100;
        const x2 = to.x * 100;
        const y2 = to.y * 100;

        line.setAttribute('x1', `${x1}%`);
        line.setAttribute('y1', `${y1}%`);
        line.setAttribute('x2', `${x2}%`);
        line.setAttribute('y2', `${y2}%`);
        line.setAttribute('class', 'network-edge');
        line.setAttribute('id', `edge-${fromName}-${toName}`);

        svg.appendChild(line);
    }

    // 连接 WebSocket
    connect() {
        const wsUrl = `ws://192.168.1.73:8080/ws/monitor`;
        this.ws = new WebSocket(wsUrl);

        this.updateConnectionStatus('connecting');

        this.ws.onopen = () => {
            console.log('WebSocket 已连接');
            this.isConnected = true;
            this.updateConnectionStatus('connected');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket 已断开');
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            setTimeout(() => this.connect(), 3000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket 错误:', error);
            this.updateConnectionStatus('disconnected');
        };
    }

    // 处理收到的消息
    handleMessage(data) {
        console.log('收到消息:', data);

        switch (data.type) {
            case 'AI_DISPATCH_MESSAGE':
                this.handleDispatch(data);
                break;
            case 'SIMULATION_END':
                this.onSimulationEnd();
                break;
            case 'USER_MESSAGE':
            case 'AI_FINAL_REPLY':
            case 'AI_THINKING_LOG':
                // 这些消息不需要在新的UI中显示
                break;
        }
    }

    // 处理派发消息 - 动态展示节点和连线
    handleDispatch(data) {
        const { target_role, content, timestamp, resource_type } = data;

        // 确定目标节点名称
        let targetName = target_role;
        if (resource_type && this.resourceTypeMap[resource_type]) {
            targetName = this.resourceTypeMap[resource_type];
        }

        // 显示目标节点（如果还未显示）
        this.showNode(targetName);

        // 显示连接线
        setTimeout(() => {
            this.animateEdge('AI大脑', targetName);
        }, 300);

        // 激活目标节点动画
        setTimeout(() => {
            this.activateNode(targetName);
        }, 500);

        // 添加派发日志
        this.appendDispatchLog(targetName, content, timestamp);

        // 更新活跃机器人数
        document.getElementById('robotCount').textContent = `${this.activeNodes.size} 个机器人活跃`;
    }

    // 激活节点动画
    activateNode(nodeName) {
        const node = document.getElementById(`node-${nodeName}`);
        if (node) {
            node.classList.add('active');
            setTimeout(() => {
                node.classList.remove('active');
            }, 2000);
        }
    }

    // 动画连线
    animateEdge(from, to) {
        const edge = document.getElementById(`edge-${from}-${to}`);

        // 如果连线不存在，先创建
        if (!edge) {
            this.createEdge(from, to);
        }

        const newEdge = document.getElementById(`edge-${from}-${to}`);
        if (newEdge) {
            newEdge.classList.add('active');
            setTimeout(() => {
                newEdge.classList.remove('active');
            }, 1500);
        }
    }

    // 添加派发日志
    appendDispatchLog(target, content, time) {
        const logBox = document.getElementById('dispatchLog');
        const card = document.createElement('div');
        card.className = 'dispatch-card';
        card.innerHTML = `
            <div class="dispatch-card-header">
                <span class="target">➡️ ${target}</span>
                <span class="time">${time || this.getCurrentTime()}</span>
            </div>
            <pre>${this.escapeHtml(content ? content.substring(0, 100) + (content.length > 100 ? '...' : '') : '正在对接资源...')}</pre>
        `;
        logBox.insertBefore(card, logBox.firstChild);

        // 限制显示数量
        while (logBox.children.length > 10) {
            logBox.removeChild(logBox.lastChild);
        }
    }

    // 获取当前时间
    getCurrentTime() {
        const now = new Date();
        return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    }

    // 更新连接状态
    updateConnectionStatus(status) {
        const el = document.getElementById('wsStatus');
        el.className = `connection-status ${status}`;

        switch (status) {
            case 'connected':
                el.textContent = '● 已连接';
                break;
            case 'disconnected':
                el.textContent = '● 已断开';
                break;
            case 'connecting':
                el.textContent = '● 连接中...';
                break;
        }
    }

    // 开始模拟
    startSimulation() {
        // 清空日志
        document.getElementById('dispatchLog').innerHTML = '';

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send('START_SIMULATION');
        } else {
            alert('WebSocket 未连接，请确保服务已启动');
        }
    }

    // 清空所有
    clearAll() {
        // 隐藏所有非初始节点
        Object.entries(this.nodeConfig).forEach(([name, config]) => {
            if (!config.initial) {
                const node = document.getElementById(`node-${name}`);
                if (node) {
                    node.classList.remove('visible', 'active');
                }
            }
        });

        // 重置活跃节点
        this.activeNodes.clear();
        this.activeNodes.add('AI大脑');

        // 清空日志
        document.getElementById('dispatchLog').innerHTML = '';

        // 重置计数
        document.getElementById('robotCount').textContent = '1 个机器人活跃';
    }

    // 模拟结束
    onSimulationEnd() {
        console.log('模拟结束');
    }

    // HTML 转义
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', () => {
    window.agentFlow = new AgentFlowMonitor();
});

// 导出供调试
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AgentFlowMonitor;
}