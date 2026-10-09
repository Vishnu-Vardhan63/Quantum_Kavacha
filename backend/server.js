const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// In-memory fraud intelligence nodes database
const nodes = [
  { id: "NODE-HUB", name: "Central Fraud Intelligence Hub", status: "online", role: "FRAUD_HUB", trust_score: 1.0, lat: 19.0760, lon: 72.8777 },
  { id: "NODE-GATEWAY", name: "UPI Payment Gateway Alpha", status: "online", role: "GATEWAY", trust_score: 0.98, lat: 19.0810, lon: 72.8820 },
  { id: "NODE-RISK-ENG", name: "Adaptive Risk Engine Bravo", status: "online", role: "RISK_ENGINE", trust_score: 0.95, lat: 19.0710, lon: 72.8710 },
  { id: "NODE-MULE-DET", name: "Mule Network Detector Charlie", status: "online", role: "DETECTOR", trust_score: 0.99, lat: 19.0790, lon: 72.8750 },
  { id: "NODE-QENGINE", name: "Qiskit Quantum Escalation Node", status: "online", role: "QUANTUM_ENGINE", trust_score: 1.0, lat: 19.0760, lon: 72.8777 }
];

const messages = [];

// GET /api/nodes - Node mesh topology and health status
app.get('/api/nodes', (req, res) => {
  res.json({
    total_nodes: nodes.length,
    online_nodes: nodes.filter(n => n.status === "online").length,
    bandwidth_mode: "NORMAL",
    nodes: nodes
  });
});

// GET /api/stats - Live delivery success rate & mesh statistics
app.get('/api/stats', (req, res) => {
  const onlineCount = nodes.filter(n => n.status === "online").length;
  const deliveryRate = onlineCount > 2 ? 98.5 : (onlineCount > 1 ? 75.0 : 40.0);
  
  res.json({
    delivery_success_rate: deliveryRate,
    online_nodes: onlineCount,
    total_nodes: nodes.length,
    messages_processed: messages.length + 1240,
    low_bandwidth_mode: onlineCount < 3
  });
});

// POST /api/messages - Log incoming mesh message / transaction alert
app.post('/api/messages', (req, res) => {
  const msg = {
    id: `MSG-${Date.now()}`,
    timestamp: new Date().toISOString(),
    ...req.body
  };
  messages.unshift(msg);
  if (messages.length > 200) messages.pop();
  res.status(201).json({ status: "stored", message: msg });
});

// GET /api/messages - Retrieve recent messages
app.get('/api/messages', (req, res) => {
  res.json(messages);
});

// GET /api/express-health - Express Auxiliary Gateway health check
app.get('/api/express-health', (req, res) => {
  res.json({
    status: "healthy",
    stack: "Q-FraudShield Auxiliary Gateway",
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`[Auxiliary Gateway] Express server running on http://127.0.0.1:${PORT}`);
});
