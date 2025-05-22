import express from 'express';

const app = express();
const port = process.env.PORT || 8081;

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/tools', (req, res) => {
  res.json([
    {
      name: 'test_tool',
      description: 'A test tool',
      input_schema: {}
    }
  ]);
});

app.listen(port, () => {
  console.log(`Simple test server running at http://localhost:${port}`);
});