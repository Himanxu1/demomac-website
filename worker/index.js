// The site is static files. This Worker answers only the few /api/ routes the
// page needs; everything else falls through to the files in this folder.
//
//   GET  /api/seats                  launch-offer seats left, from Dodo
//   GET  /api/requests               approved feature requests, most votes first
//   POST /api/requests               submit one (held for approval)
//   POST /api/requests/:id/vote      +1, once per person
//   GET  /api/requests/:id/moderate  approve/reject, from the link in the email
//
// Needs, on the Worker:
//   DODO_API_KEY      secret  `wrangler secret put DODO_API_KEY`
//   ADMIN_SECRET      secret  `wrangler secret put ADMIN_SECRET` — signs the
//                             moderation links and salts voter hashes
//   DODO_DISCOUNT_ID  var     the EARLY39 discount's id (wrangler.jsonc)
//   SEAT_TOTAL        var     used only if the discount has no usage limit
//   DB                D1      screentoast-requests
//   NOTIFY            email   optional; without it requests are still saved

import { EmailMessage } from 'cloudflare:email';

const DODO = 'https://live.dodopayments.com';
const SITE = 'https://screentoast.com';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    try {
      if (path === '/api/seats') return await seats(url, env, ctx);
      if (path === '/api/requests') {
        if (request.method === 'GET') return await listRequests(env);
        if (request.method === 'POST') return await submitRequest(request, env, ctx);
        return json({ error: 'method' }, 405);
      }
      let m = path.match(/^\/api\/requests\/(\d+)\/vote$/);
      if (m && request.method === 'POST') return await vote(request, env, Number(m[1]));
      m = path.match(/^\/api\/requests\/(\d+)\/moderate$/);
      if (m) return await moderate(request, url, env, Number(m[1]));
      if (path.startsWith('/api/')) return json({ error: 'not found' }, 404);
    } catch (e) {
      console.error(path, e && e.stack || e);
      return json({ error: 'server' }, 500);
    }
    return env.ASSETS.fetch(request);
  },
};

// ── launch seats ────────────────────────────────────────────────────────────

async function seats(url, env, ctx) {
  // One Dodo call a minute at most, however many people are on the page.
  const cache = caches.default;
  const key = new Request(url.origin + '/api/seats');
  const hit = await cache.match(key);
  if (hit) return hit;

  if (!env.DODO_API_KEY || !env.DODO_DISCOUNT_ID) {
    console.error('seats not configured', { key: !!env.DODO_API_KEY, discount: !!env.DODO_DISCOUNT_ID });
    return json({ error: 'unavailable' }, 503);
  }
  const r = await fetch(`${DODO}/discounts/${env.DODO_DISCOUNT_ID}`, {
    headers: { Authorization: `Bearer ${env.DODO_API_KEY}` },
  });
  // The page treats any failure as "no number", never as "sold out".
  if (!r.ok) {
    console.error('dodo discount lookup', r.status, (await r.text()).slice(0, 300));
    return json({ error: 'unavailable' }, 503);
  }
  const d = await r.json();
  const total = d.usage_limit ?? Number(env.SEAT_TOTAL || 100);
  const used = d.times_used ?? 0;
  const expired = d.expires_at ? Date.parse(d.expires_at) <= Date.now() : false;

  const res = json({ total, left: Math.max(0, total - used), expired }, 200, 'public, max-age=60');
  ctx.waitUntil(cache.put(key, res.clone()));
  return res;
}

// ── feature requests ────────────────────────────────────────────────────────

const PUBLIC = "('approved', 'planned', 'shipped')";

async function listRequests(env) {
  const { results } = await env.DB.prepare(
    `SELECT id, title, detail, status, votes FROM requests
     WHERE status IN ${PUBLIC} ORDER BY status = 'shipped', votes DESC, id DESC LIMIT 100`
  ).all();
  return json({ requests: results }, 200, 'no-store');
}

async function submitRequest(request, env, ctx) {
  const body = await readJson(request);
  if (!body) return json({ error: 'Send the form as JSON.' }, 400);
  // Hidden field a person never sees. Anything filling it is a bot — tell it
  // it worked so it does not retry.
  if (body.website) return json({ ok: true }, 200);

  const title = clean(body.title, 120);
  const detail = clean(body.detail, 1000);
  const email = clean(body.email, 200);
  if (title.length < 4) return json({ error: 'Give the feature a short name.' }, 400);
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ error: 'That email address looks off.' }, 400);

  const ip = await who(request, env);
  const dayAgo = Date.now() - 86400e3;
  const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM requests WHERE ip_hash = ? AND created_at > ?')
    .bind(ip, dayAgo).first();
  if (n >= 5) return json({ error: 'That is plenty for one day — thank you. Try again tomorrow.' }, 429);

  const row = await env.DB.prepare(
    'INSERT INTO requests (title, detail, email, ip_hash, created_at) VALUES (?, ?, ?, ?, ?) RETURNING id'
  ).bind(title, detail, email, ip, Date.now()).first();
  await env.DB.prepare('INSERT OR IGNORE INTO votes (request_id, voter, created_at) VALUES (?, ?, ?)')
    .bind(row.id, ip, Date.now()).run();

  ctx.waitUntil(notify(env, row.id, title, detail, email).catch(e => console.error('notify', e)));
  return json({ ok: true }, 201);
}

async function vote(request, env, id) {
  const voter = await who(request, env);
  const live = await env.DB.prepare(`SELECT id FROM requests WHERE id = ? AND status IN ${PUBLIC}`).bind(id).first();
  if (!live) return json({ error: 'not found' }, 404);
  const ins = await env.DB.prepare('INSERT OR IGNORE INTO votes (request_id, voter, created_at) VALUES (?, ?, ?)')
    .bind(id, voter, Date.now()).run();
  if (ins.meta.changes) await env.DB.prepare('UPDATE requests SET votes = votes + 1 WHERE id = ?').bind(id).run();
  const { votes } = await env.DB.prepare('SELECT votes FROM requests WHERE id = ?').bind(id).first();
  return json({ votes, counted: !!ins.meta.changes }, 200);
}

// Opening the emailed link only shows a button; the change happens on the
// POST. Mail scanners and link previewers open links on their own, and a GET
// that approved or rejected would let them moderate before you ever read it.
// Links also carry an expiry inside the signature, so a leaked one goes dead.
const LINK_TTL = 14 * 86400;

async function moderate(request, url, env, id) {
  const action = url.searchParams.get('action');
  const exp = Number(url.searchParams.get('exp'));
  const status = { approve: 'approved', reject: 'rejected', planned: 'planned', shipped: 'shipped' }[action];
  const ok = status && exp > Date.now() / 1000 &&
    await verify(env, `${id}:${action}:${exp}`, url.searchParams.get('sig') || '');
  if (!ok) return page('That link is not valid, or it has expired.', 403);

  if (request.method !== 'POST') {
    const row = await env.DB.prepare('SELECT title, status FROM requests WHERE id = ?').bind(id).first();
    if (!row) return page('No such request.', 404);
    return page(`Request #${id}: <b>${esc(row.title)}</b> — currently ${esc(row.status)}.` +
      `<form method="post" style="margin-top:18px"><button style="font:inherit;padding:10px 18px;border-radius:8px;border:0;background:#ff5b04;color:#fff;cursor:pointer">Mark as ${status}</button></form>`, 200);
  }

  const r = await env.DB.prepare('UPDATE requests SET status = ? WHERE id = ?').bind(status, id).run();
  if (!r.meta.changes) return page('No such request.', 404);
  return page(`Request #${id} is now <b>${status}</b>.` +
    (status === 'rejected' ? '' : ` <a href="${SITE}/#requests">See the board</a>`), 200);
}

async function notify(env, id, title, detail, email) {
  if (!env.NOTIFY) return;
  const exp = Math.floor(Date.now() / 1000) + LINK_TTL;
  const link = async a => `${SITE}/api/requests/${id}/moderate?action=${a}&exp=${exp}&sig=${await sign(env, `${id}:${a}:${exp}`)}`;
  const text = [
    `New feature request #${id}`,
    '',
    title,
    detail ? `\n${detail}\n` : '',
    email ? `From: ${email}` : 'No email left.',
    '',
    `Approve (shows on the site): ${await link('approve')}`,
    `Reject:                      ${await link('reject')}`,
    `Mark planned:                ${await link('planned')}`,
    `Mark shipped:                ${await link('shipped')}`,
  ].join('\n');
  const from = env.NOTIFY_FROM || 'requests@screentoast.com';
  const raw = [
    `From: ScreenToast requests <${from}>`,
    `To: ${env.NOTIFY_TO || 'me'}`,
    email ? `Reply-To: ${email.replace(/[\r\n]/g, '')}` : null,
    `Subject: Feature request: ${title.replace(/[\r\n]/g, ' ')}`,
    `Message-ID: <request-${id}-${Date.now()}@screentoast.com>`,
    `Date: ${new Date().toUTCString()}`,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=utf-8',
    'Content-Transfer-Encoding: 8bit',
    '',
    text,
  ].filter(l => l !== null).join('\r\n');
  // destination_address is fixed in wrangler.jsonc, so the "to" here is ignored.
  await env.NOTIFY.send(new EmailMessage(from, env.NOTIFY_TO || 'unused@screentoast.com', raw));
}

// ── helpers ─────────────────────────────────────────────────────────────────

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

function clean(v, max) {
  return String(v ?? '').replace(/[\u0000-\u0008\u000b-\u001f\u007f]/g, '').trim().slice(0, max);
}

async function readJson(request) {
  try { return await request.json(); } catch { return null; }
}

// A salted hash of the visitor's IP — enough to stop double votes, never
// stored as the address itself.
async function who(request, env) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  return (await hmac(env, `voter:${ip}`)).slice(0, 32);
}

async function sign(env, msg) { return hmac(env, `moderate:${msg}`); }

async function verify(env, msg, sig) {
  const want = await sign(env, msg);
  if (want.length !== sig.length) return false;
  let diff = 0;
  for (let i = 0; i < want.length; i++) diff |= want.charCodeAt(i) ^ sig.charCodeAt(i);
  return diff === 0;
}

async function hmac(env, msg) {
  if (!env.ADMIN_SECRET) throw new Error('ADMIN_SECRET is not set');
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(env.ADMIN_SECRET),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(msg));
  return [...new Uint8Array(mac)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function json(body, status = 200, cacheControl = 'no-store') {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': cacheControl },
  });
}

function page(msg, status) {
  return new Response(
    `<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>ScreenToast requests</title>` +
    `<body style="font:16px system-ui;background:#08080a;color:#f2efe9;display:grid;place-items:center;min-height:90vh">` +
    `<p>${msg}</p>`,
    { status, headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
}
