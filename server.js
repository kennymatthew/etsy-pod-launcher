require('dotenv').config();

const express = require('express');
const cors = require('cors');

// node-fetch v3 is ESM-only, so we load it via dynamic import from CommonJS.
const fetch = (...args) => import('node-fetch').then(({ default: f }) => f(...args));

const app = express();
app.use(cors());
app.use(express.json({ limit: '25mb' }));

const { PRINTIFY_API_TOKEN, PRINTIFY_SHOP_ID } = process.env;
const PORT = process.env.PORT || 3333;
const PRINTIFY_BASE = 'https://api.printify.com/v1';

// Shared helper: proxy a request to the Printify API and forward the response.
async function proxyToPrintify(req, res, { method, path, body }) {
  try {
    const options = {
      method,
      headers: {
        Authorization: `Bearer ${PRINTIFY_API_TOKEN}`,
        'Content-Type': 'application/json',
        'User-Agent': 'printify-bridge',
      },
    };

    if (body !== undefined) {
      options.body = JSON.stringify(body);
    }

    const printifyRes = await fetch(`${PRINTIFY_BASE}${path}`, options);

    // Read the raw text first so we can forward it even if it isn't valid JSON.
    const text = await printifyRes.text();
    let payload;
    try {
      payload = text ? JSON.parse(text) : null;
    } catch {
      payload = text;
    }

    // Forward Printify's status code (including non-2xx) and body to the caller.
    return res.status(printifyRes.status).json(payload);
  } catch (err) {
    return res.status(502).json({
      error: 'Bridge failed to reach Printify',
      detail: err.message,
    });
  }
}

// --- Health check ---
app.get('/health', (req, res) => {
  res.json({ status: 'ok', shop_id: PRINTIFY_SHOP_ID });
});

// --- Shops ---
app.get('/api/shops', (req, res) => {
  return proxyToPrintify(req, res, {
    method: 'GET',
    path: '/shops.json',
  });
});

// --- Orders ---
app.get('/api/orders', (req, res) => {
  const params = new URLSearchParams();
  if (req.query.status) params.set('status', req.query.status);
  if (req.query.page) params.set('page', req.query.page);
  const qs = params.toString();

  return proxyToPrintify(req, res, {
    method: 'GET',
    path: `/shops/${PRINTIFY_SHOP_ID}/orders.json${qs ? `?${qs}` : ''}`,
  });
});

app.get('/api/orders/:id', (req, res) => {
  return proxyToPrintify(req, res, {
    method: 'GET',
    path: `/shops/${PRINTIFY_SHOP_ID}/orders/${req.params.id}.json`,
  });
});

app.post('/api/orders/:id/produce', (req, res) => {
  return proxyToPrintify(req, res, {
    method: 'POST',
    path: `/shops/${PRINTIFY_SHOP_ID}/orders/${req.params.id}/send_to_production.json`,
    body: {},
  });
});

// --- Products ---
app.get('/api/products', (req, res) => {
  return proxyToPrintify(req, res, {
    method: 'GET',
    path: `/shops/${PRINTIFY_SHOP_ID}/products.json`,
  });
});

app.post('/api/products', (req, res) => {
  return proxyToPrintify(req, res, {
    method: 'POST',
    path: `/shops/${PRINTIFY_SHOP_ID}/products.json`,
    body: req.body,
  });
});

// Publish a product to the connected sales channel.
// Body is optional; defaults to publishing all properties.
app.post('/api/products/:id/publish', (req, res) => {
  const body =
    req.body && Object.keys(req.body).length > 0
      ? req.body
      : {
          title: true,
          description: true,
          images: true,
          variants: true,
          tags: true,
          keyFeatures: true,
          shipping_template: true,
        };

  return proxyToPrintify(req, res, {
    method: 'POST',
    path: `/shops/${PRINTIFY_SHOP_ID}/products/${req.params.id}/publish.json`,
    body,
  });
});

// --- Uploads ---
// Accepts { file_name, url } or { file_name, contents } in the request body.
app.post('/api/upload', (req, res) => {
  return proxyToPrintify(req, res, {
    method: 'POST',
    path: '/uploads/images.json',
    body: req.body,
  });
});

// --- Catalog (blueprint-level, not shop-scoped) ---
// List all available blueprints (product types).
app.get('/api/catalog', (req, res) => {
  return proxyToPrintify(req, res, {
    method: 'GET',
    path: '/catalog/blueprints.json',
  });
});

// List the print providers that can produce a given blueprint.
app.get('/api/catalog/:blueprintId/providers', (req, res) => {
  return proxyToPrintify(req, res, {
    method: 'GET',
    path: `/catalog/blueprints/${req.params.blueprintId}/print_providers.json`,
  });
});

// List the variants a given provider offers for a given blueprint.
app.get('/api/catalog/:blueprintId/providers/:providerId/variants', (req, res) => {
  return proxyToPrintify(req, res, {
    method: 'GET',
    path: `/catalog/blueprints/${req.params.blueprintId}/print_providers/${req.params.providerId}/variants.json`,
  });
});

app.listen(PORT, () => {
  console.log(`printify-bridge listening on http://localhost:${PORT}`);
  if (!PRINTIFY_API_TOKEN) {
    console.warn('⚠️  PRINTIFY_API_TOKEN is not set — fill it in your .env file.');
  }
  if (!PRINTIFY_SHOP_ID) {
    console.warn('⚠️  PRINTIFY_SHOP_ID is not set — fill it in your .env file.');
  }
});
