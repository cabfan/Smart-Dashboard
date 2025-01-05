const express = require('express');
const cors = require('cors');
const WebSocket = require('ws');
const { OpenAI } = require('openai');
const sqlite3 = require('sqlite3').verbose();
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json());

// 数据库连接
const db = new sqlite3.Database('./database.sqlite', (err) => {
    if (err) {
        console.error('Error connecting to database:', err);
    } else {
        console.log('Connected to SQLite database');
        initDatabase();
    }
});

// 初始化数据库表
function initDatabase() {
    db.run(`CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
}

// WebSocket 服务器
const wss = new WebSocket.Server({ noServer: true });

wss.on('connection', (ws) => {
    console.log('New client connected');
    
    ws.on('message', async (message) => {
        try {
            const data = JSON.parse(message);
            // 处理消息
            ws.send(JSON.stringify({ type: 'response', content: 'Message received' }));
        } catch (error) {
            console.error('Error processing message:', error);
        }
    });

    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

// 基础路由
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok' });
});

// 启动服务器
const server = app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});

// 将 WebSocket 服务器附加到 HTTP 服务器
server.on('upgrade', (request, socket, head) => {
    wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit('connection', ws, request);
    });
});

module.exports = app;
