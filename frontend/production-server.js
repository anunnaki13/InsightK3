const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const port = Number(process.env.PORT || 6969);
const backendTarget = process.env.BACKEND_TARGET || 'http://127.0.0.1:8001';
const buildDir = path.join(__dirname, 'build');

app.use((req, res, next) => {
  res.setHeader('Cache-Control', 'no-store');
  next();
});

app.use(
  '/api',
  createProxyMiddleware({
    target: backendTarget,
    changeOrigin: true,
    ws: false,
  })
);

app.use(express.static(buildDir));

app.get('*', (req, res) => {
  res.sendFile(path.join(buildDir, 'index.html'));
});

app.listen(port, '0.0.0.0', () => {
  console.log(`InsightK3 frontend serving on http://0.0.0.0:${port}`);
  console.log(`Proxying /api to ${backendTarget}`);
});
