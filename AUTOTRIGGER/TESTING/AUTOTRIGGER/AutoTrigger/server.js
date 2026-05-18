const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const { EventHubProducerClient } = require('@azure/event-hubs');
const config = require('./config.json');
const path = require('path');

const app = express();

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Store Event Hub clients (keyed by connectionString+eventHubName)
const producerClients = new Map();

function isUnsafePathSegment(segment) {
  return segment === '__proto__' || segment === 'prototype' || segment === 'constructor';
}

function deepSet(target, dottedPath, value) {
  if (typeof dottedPath !== 'string' || dottedPath.trim() === '') return;

  const segments = dottedPath.split('.').map(s => s.trim()).filter(Boolean);
  if (segments.length === 0) return;
  if (segments.some(isUnsafePathSegment)) {
    throw new Error(`Unsafe field path: ${dottedPath}`);
  }

  let cursor = target;
  for (let i = 0; i < segments.length - 1; i++) {
    const segment = segments[i];
    if (cursor[segment] === undefined || cursor[segment] === null || typeof cursor[segment] !== 'object') {
      cursor[segment] = {};
    }
    cursor = cursor[segment];
  }

  cursor[segments[segments.length - 1]] = value;
}

function applyOverrides(payloadTemplate, overrides) {
  if (!overrides || typeof overrides !== 'object') return payloadTemplate;

  for (const [key, value] of Object.entries(overrides)) {
    if (key.includes('.')) {
      deepSet(payloadTemplate, key, value);
    } else {
      payloadTemplate[key] = value;
    }
  }

  return payloadTemplate;
}

function getProducerClientKey(connectionString, eventHubName) {
  return `${connectionString}::${eventHubName || ''}`;
}

function getProducerClientForService(service) {
  const connectionString = service.connectionString || config?.eventHubConfig?.connectionString;
  const eventHubName = service.eventHubName;

  if (!connectionString) {
    throw new Error('Missing connectionString in service config');
  }

  const key = getProducerClientKey(connectionString, eventHubName);
  let client = producerClients.get(key);

  if (!client) {
    client = eventHubName
      ? new EventHubProducerClient(connectionString, eventHubName)
      : new EventHubProducerClient(connectionString);
    producerClients.set(key, client);
  }

  return client;
}

function getTemplateForService(service) {
  return service.eventPayload || service.payload || {};
}

// API Routes

// Get configuration
app.get('/api/config', (req, res) => {
  res.json(config);
});

// Get specific service config
app.get('/api/services/:serviceId', (req, res) => {
  const service = config.services.find(s => s.id === req.params.serviceId);
  if (!service) {
    return res.status(404).json({ error: 'Service not found' });
  }
  res.json(service);
});

// Trigger single payload
app.post('/api/trigger/single', async (req, res) => {
  try {
    const { serviceId, payload } = req.body;

    if (!serviceId || !payload) {
      return res.status(400).json({ error: 'Missing serviceId or payload' });
    }

    const service = config.services.find(s => s.id === serviceId);
    if (!service) {
      return res.status(404).json({ error: 'Service not found' });
    }

    const producerClient = getProducerClientForService(service);

    const template = getTemplateForService(service);
    const finalPayload = applyOverrides(JSON.parse(JSON.stringify(template)), payload);
    finalPayload.timestamp = new Date().toISOString();

    const partitionKey =
      finalPayload.id === undefined || finalPayload.id === null ? 'default' : String(finalPayload.id);

    const batch = await producerClient.createBatch({ partitionKey });
    batch.tryAdd({ body: finalPayload });
    await producerClient.sendBatch(batch);

    res.json({
      success: true,
      message: 'Payload triggered successfully',
      eventHubName: service.eventHubName,
      payload: finalPayload
    });
  } catch (error) {
    console.error('Error triggering payload:', error);
    res.status(500).json({
      error: 'Failed to trigger payload',
      details: error.message
    });
  }
});

// Trigger multiple payloads
app.post('/api/trigger/multiple', async (req, res) => {
  try {
    const { serviceId, payloads } = req.body;

    if (!serviceId || !payloads || !Array.isArray(payloads)) {
      return res.status(400).json({ error: 'Missing serviceId or invalid payloads' });
    }

    const service = config.services.find(s => s.id === serviceId);
    if (!service) {
      return res.status(404).json({ error: 'Service not found' });
    }

    const producerClient = getProducerClientForService(service);
    const template = getTemplateForService(service);

    let successCount = 0;
    const results = [];

    for (const payload of payloads) {
      try {
        const finalPayload = applyOverrides(JSON.parse(JSON.stringify(template)), payload);
        finalPayload.timestamp = new Date().toISOString();

        const partitionKey =
          finalPayload.id === undefined || finalPayload.id === null ? 'default' : String(finalPayload.id);

        const batch = await producerClient.createBatch({ partitionKey });
        batch.tryAdd({ body: finalPayload });
        await producerClient.sendBatch(batch);

        successCount++;
        results.push({ success: true, payload: finalPayload });
      } catch (error) {
        results.push({ success: false, error: error.message });
      }
    }

    res.json({
      success: true,
      message: `${successCount}/${payloads.length} payloads triggered successfully`,
      eventHubName: service.eventHubName,
      results: results
    });
  } catch (error) {
    console.error('Error triggering multiple payloads:', error);
    res.status(500).json({
      error: 'Failed to trigger payloads',
      details: error.message
    });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    eventHubConnected: producerClients.size > 0,
    initializedClients: producerClients.size
  });
});

// Serve index.html for root path
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Event Hub Trigger Server running on http://localhost:${PORT}`);
  console.log(`Configuration loaded: ${config.services.length} services`);
});

// Graceful shutdown
async function shutdown() {
  await Promise.allSettled(Array.from(producerClients.values()).map(client => client.close()));
  process.exit(0);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

