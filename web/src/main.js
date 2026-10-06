const API_BASE_URL = localStorage.getItem('fur_api_base_url') || 'http://localhost:8000';
const ACCESS_TOKEN_KEY = 'fur_access_token';
const app = document.querySelector('#app');

function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}
function setAccessToken(token) {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}
function clearAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
  const token = getAccessToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.error?.message || payload.detail?.reason || message;
    } catch {}
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

function fmtDate(value) {
  return new Date(value).toLocaleString();
}

function navigate(hash) {
  window.location.hash = hash;
}

function lifecycleStatusMeta(status) {
  const map = {
    open: { label: 'OPEN', className: 'status-open' },
    due_today: { label: 'DUE TODAY', className: 'status-due-today' },
    overdue: { label: 'OVERDUE', className: 'status-overdue' },
    done: { label: 'DONE', className: 'status-done' },
    lost: { label: 'LOST', className: 'status-lost' },
    archived: { label: 'ARCHIVED', className: 'status-archived' },
  };
  return map[status] || { label: String(status).toUpperCase(), className: 'status-archived' };
}

function renderLifecycleBadge(status) {
  const meta = lifecycleStatusMeta(status);
  return `<span class="status-badge ${meta.className}">${meta.label}</span>`;
}

function paymentTextLabel(paymentStatus) {
  const labels = {
    unpaid: 'Payment: unpaid',
    paid: 'Payment: paid',
    not_applicable: 'Payment: n/a',
  };
  return labels[paymentStatus] || `Payment: ${paymentStatus}`;
}

function renderPaymentText(paymentStatus) {
  return `<span class="payment-text">${escapeHtml(paymentTextLabel(paymentStatus))}</span>`;
}

function isActiveStatus(status) {
  return ['open', 'due_today', 'overdue'].includes(status);
}

function isTerminalStatus(status) {
  return ['done', 'lost', 'archived'].includes(status);
}

function defaultCasesState() {
  return {
    scope: 'all',
    q: '',
    sort_by: 'due_at',
    sort_dir: 'asc',
    status: '',
    payment_status: '',
    item_type: '',
    due_bucket: '',
    due_from: '',
    due_to: '',
    amount_min: '',
    amount_max: '',
    review_signal: '',
  };
}

function parseCasesState(hash) {
  const state = defaultCasesState();
  const [, queryString = ''] = (hash || '#/cases').split('?');
  const query = new URLSearchParams(queryString);
  for (const key of Object.keys(state)) {
    const value = query.get(key);
    if (value !== null) {
      state[key] = value;
    }
  }
  return state;
}

function buildCasesHash(state) {
  const params = new URLSearchParams();
  const withDefaults = { ...defaultCasesState(), ...state };
  for (const [key, value] of Object.entries(withDefaults)) {
    if (value === '' || value === null || value === undefined) continue;
    if (key === 'scope' && value === 'all') {
      params.set('scope', value);
      continue;
    }
    params.set(key, String(value));
  }
  const queryString = params.toString();
  return queryString ? `#/cases?${queryString}` : '#/cases';
}

function registryApiPath(state) {
  const params = new URLSearchParams();
  const withDefaults = { ...defaultCasesState(), ...state };
  for (const [key, value] of Object.entries(withDefaults)) {
    if (value === '' || value === null || value === undefined) continue;
    params.set(key, String(value));
  }
  return `/items/registry?${params.toString()}`;
}

function activeFilterEntries(state) {
  const entries = [];
  if (state.q) entries.push({ key: 'q', label: `Search: ${state.q}` });
  if (state.status) entries.push({ key: 'status', label: `Status: ${prettyCaseStatus(state.status)}` });
  if (state.payment_status) entries.push({ key: 'payment_status', label: `Payment: ${prettyPaymentStatus(state.payment_status)}` });
  if (state.item_type) entries.push({ key: 'item_type', label: `Type: ${prettyItemType(state.item_type)}` });
  if (state.due_bucket) entries.push({ key: 'due_bucket', label: `Due bucket: ${prettyDueBucket(state.due_bucket)}` });
  if (state.due_from) entries.push({ key: 'due_from', label: `Due from: ${state.due_from}` });
  if (state.due_to) entries.push({ key: 'due_to', label: `Due to: ${state.due_to}` });
  if (state.amount_min) entries.push({ key: 'amount_min', label: `Amount min: ${state.amount_min}` });
  if (state.amount_max) entries.push({ key: 'amount_max', label: `Amount max: ${state.amount_max}` });
  if (state.review_signal) entries.push({ key: 'review_signal', label: `Review signal: ${prettyReviewSignal(state.review_signal)}` });
  return entries;
}

function prettyCaseStatus(value) {
  return {
    open: 'Open',
    due_today: 'Due today',
    overdue: 'Overdue',
    done: 'Done',
    lost: 'Lost',
  }[value] || value;
}

function prettyPaymentStatus(value) {
  return {
    unpaid: 'Unpaid',
    paid: 'Paid',
    not_applicable: 'N/A',
  }[value] || value;
}

function prettyItemType(value) {
  return {
    invoice: 'Invoice',
    proposal: 'Proposal',
    lead: 'Lead',
    promised_reply: 'Promised reply',
    renewal: 'Renewal',
  }[value] || value;
}

function prettyDueBucket(value) {
  return {
    overdue: 'Overdue',
    due_today: 'Due today',
    scheduled: 'Scheduled',
  }[value] || value;
}

function prettyReviewSignal(value) {
  return {
    needs_action: 'Needs action',
    paid_but_open: 'Paid but open',
    stale_case: 'No activity 7+ days',
    reminder_failed: 'Reminder failed',
    overdue_without_reminder: 'Overdue without reminder',
    reminder_issue: 'Reminder issue',
  }[value] || value;
}


function countAppliedFilters(state) {
  return activeFilterEntries(state).length;
}

function renderShell(content) {
  const hash = window.location.hash || '#/';
  const onDashboard = hash === '#/' || hash === '';
  const onCases = hash.startsWith('#/cases');
  const onBilling = hash.startsWith('#/billing');
  app.innerHTML = `
    <div class="container grid" style="gap:20px">
      <div class="header">
        <div>
          <div class="kicker">Follow-Up Radar</div>
          <h1 style="margin:0">High-end follow-up control surface</h1>
        </div>
        <div class="inline-actions">
          <button class="${onDashboard ? '' : 'ghost'}" id="home-link">Dashboard</button>
          <button class="${onCases ? '' : 'ghost'}" id="cases-link">Cases</button>
          <button class="${onBilling ? '' : 'ghost'}" id="billing-link">Billing</button>
          <button class="ghost" id="logout-link">Log out</button>
        </div>
      </div>
      ${content}
    </div>
  `;
  document.querySelector('#home-link')?.addEventListener('click', () => { navigate('#/'); render(); });
  document.querySelector('#cases-link')?.addEventListener('click', () => { navigate('#/cases?scope=all'); render(); });
  document.querySelector('#billing-link')?.addEventListener('click', () => { navigate('#/billing'); render(); });
  document.querySelector('#logout-link')?.addEventListener('click', () => {
    clearAccessToken();
    navigate('#/login');
    render();
  });
}

function renderPublicShell(content, active = '') {
  app.innerHTML = `
    <div class="container grid" style="gap:20px">
      <div class="header">
        <div>
          <div class="kicker">Follow-Up Radar</div>
          <h1 style="margin:0">No client case goes invisible.</h1>
        </div>
        <div class="inline-actions">
          <button class="${active === 'pricing' ? '' : 'ghost'}" id="public-pricing-link">Pricing</button>
          <button class="${active === 'onboarding' ? '' : 'ghost'}" id="public-onboarding-link">Onboarding</button>
          <button class="${active === 'support' ? '' : 'ghost'}" id="public-support-link">Support</button>
          <button class="ghost" id="public-login-link">Sign in</button>
        </div>
      </div>
      ${content}
    </div>
  `;
  document.querySelector('#public-pricing-link')?.addEventListener('click', () => { navigate('#/pricing'); render(); });
  document.querySelector('#public-onboarding-link')?.addEventListener('click', () => { navigate('#/onboarding'); render(); });
  document.querySelector('#public-support-link')?.addEventListener('click', () => { navigate('#/support'); render(); });
  document.querySelector('#public-login-link')?.addEventListener('click', () => { navigate('#/login'); render(); });
}

async function render() {
  const hash = window.location.hash || '#/';
  const token = getAccessToken();
  if (!token) {
    if (hash.startsWith('#/verify')) {
      renderVerify();
      return;
    }
    if (hash.startsWith('#/login')) {
      renderLogin();
      return;
    }
    if (hash.startsWith('#/pricing')) {
      await renderPricing();
      return;
    }
    if (hash.startsWith('#/support')) {
      await renderSupport();
      return;
    }
    if (hash.startsWith('#/privacy')) {
      await renderPrivacy();
      return;
    }
    if (hash.startsWith('#/terms')) {
      await renderTerms();
      return;
    }
    if (hash.startsWith('#/onboarding')) {
      await renderOnboarding(false);
      return;
    }
    await renderPublicHome();
    return;
  }
  if (hash.startsWith('#/verify')) {
    renderVerify();
    return;
  }
  if (hash.startsWith('#/cases')) {
    await renderCases(hash);
    return;
  }
  if (hash.startsWith('#/billing')) {
    await renderBilling();
    return;
  }
  if (hash.startsWith('#/onboarding')) {
    await renderOnboarding(true);
    return;
  }
  if (hash.startsWith('#/item/')) {
    const itemId = hash.replace('#/item/', '').split('?')[0];
    await renderItemDetail(itemId);
    return;
  }
  await renderDashboard();
}

async function renderPublicHome() {
  const site = await api('/v1/system/public-site-config');
  renderPublicShell(`
    <div class="card grid" style="gap:16px">
      <div class="kicker">${escapeHtml(site.product_name)}</div>
      <h2 style="margin:0">${escapeHtml(site.tagline)}</h2>
      <div class="small">Track every client follow-up, payment state, and risk signal in one control surface. Start with a ${site.beta_trial_days}-day beta trial, then upgrade when the workflow proves itself.</div>
      <div class="inline-actions">
        <button id="start-trial-link">Start beta trial</button>
        <button class="ghost" id="see-pricing-link">See pricing</button>
        <button class="ghost" id="see-onboarding-link">How it works</button>
      </div>
    </div>
  `, 'home');
  document.querySelector('#start-trial-link')?.addEventListener('click', () => { navigate('#/login'); render(); });
  document.querySelector('#see-pricing-link')?.addEventListener('click', () => { navigate('#/pricing'); render(); });
  document.querySelector('#see-onboarding-link')?.addEventListener('click', () => { navigate('#/onboarding'); render(); });
}

async function renderPricing() {
  const site = await api('/v1/system/public-site-config');
  renderPublicShell(`
    <div class="grid grid-2">
      <div class="card grid" style="gap:12px">
        <div class="kicker">Free</div>
        <h2 style="margin:0">Control the core workflow</h2>
        <div class="small">Create cases, review board, registry, item detail, and activity history.</div>
        <div class="small">Best for evaluating the workflow before the beta upgrade.</div>
      </div>
      <div class="card grid" style="gap:12px">
        <div class="kicker">Pro beta</div>
        <h2 style="margin:0">$${site.pro_monthly_price_usd}/month after ${site.beta_trial_days}-day trial</h2>
        <div class="small">${escapeHtml(site.beta_message)}</div>
        <label>Email
          <input id="beta-interest-email" type="email" placeholder="you@example.com" />
        </label>
        <label>What will you use Radar for?
          <textarea id="beta-interest-note" placeholder="Invoice follow-ups, renewals, proposal nudges..."></textarea>
        </label>
        <div class="inline-actions">
          <button id="beta-interest-submit">Request beta access</button>
          <button class="ghost" id="pricing-login-link">Sign in</button>
        </div>
        <div class="small">Support: ${escapeHtml(site.support_email)}</div>
        <div id="beta-interest-feedback"></div>
      </div>
    </div>
  `, 'pricing');
  document.querySelector('#pricing-login-link')?.addEventListener('click', () => { navigate('#/login'); render(); });
  document.querySelector('#beta-interest-submit')?.addEventListener('click', async () => {
    const email = document.querySelector('#beta-interest-email').value.trim();
    const note = document.querySelector('#beta-interest-note').value.trim();
    try {
      await api('/v1/system/beta-interest', { method: 'POST', body: JSON.stringify({ email, note, source: 'pricing_page' }) });
      document.querySelector('#beta-interest-feedback').innerHTML = '<div class="notice">Beta interest recorded. We will contact you with onboarding details.</div>';
    } catch (error) {
      document.querySelector('#beta-interest-feedback').innerHTML = `<div class="error">${error.message}</div>`;
    }
  });
}

async function renderSupport() {
  const site = await api('/v1/system/public-site-config');
  renderPublicShell(`
    <div class="card grid" style="gap:12px">
      <h2 style="margin:0">Support</h2>
      <div class="small">For product questions, onboarding help, and beta support contact ${escapeHtml(site.support_email)}.</div>
      <div class="inline-actions">
        <button id="support-pricing-link">Pricing</button>
        <button class="ghost" id="support-login-link">Sign in</button>
      </div>
    </div>
  `, 'support');
  document.querySelector('#support-pricing-link')?.addEventListener('click', () => { navigate('#/pricing'); render(); });
  document.querySelector('#support-login-link')?.addEventListener('click', () => { navigate('#/login'); render(); });
}

async function renderPrivacy() {
  const site = await api('/v1/system/public-site-config');
  renderPublicShell(`
    <div class="card grid" style="gap:12px">
      <h2 style="margin:0">Privacy</h2>
      <div class="small">Radar stores case metadata, event history, reminder state, and minimal account data required to run the service.</div>
      <div class="small">Support contact: ${escapeHtml(site.support_email)}</div>
    </div>
  `, 'support');
}

async function renderTerms() {
  renderPublicShell(`
    <div class="card grid" style="gap:12px">
      <h2 style="margin:0">Terms</h2>
      <div class="small">Beta access is provided as a lightweight self-serve subscription for evaluating the workflow. Do not use the service for unlawful or harmful purposes.</div>
    </div>
  `, 'support');
}

async function renderOnboarding(isAuthenticated) {
  const site = await api('/v1/system/public-site-config');
  const content = `
    <div class="card grid" style="gap:12px">
      <h2 style="margin:0">Onboarding</h2>
      <ol class="small" style="margin:0; padding-left:18px; display:grid; gap:8px;">
        <li>Create a case with a clear title, due date, and next action.</li>
        <li>Review the Dashboard daily to process Overdue, Due today, and Scheduled work.</li>
        <li>Use Cases for search, sorting, filters, and quick review views.</li>
        <li>Use Item detail to manage payment state, terminal outcomes, and full activity history.</li>
        <li>Use review signals to catch stale, risky, or paid-but-open cases before they go invisible.</li>
      </ol>
      <div class="small">Need help? ${escapeHtml(site.support_email)}</div>
    </div>
  `;
  if (isAuthenticated) {
    renderShell(content);
  } else {
    renderPublicShell(content, 'onboarding');
  }
}

async function renderBilling() {
  const [summary, site] = await Promise.all([api('/billing/summary'), api('/v1/system/public-site-config')]);
  const trialLine = summary.trial_ends_at
    ? `<div class="small">Trial ends: ${fmtDate(summary.trial_ends_at)}${summary.trial_days_left !== null ? ` • ${summary.trial_days_left} day(s) left` : ''}</div>`
    : '<div class="small">No active trial.</div>';
  const renewLine = summary.renews_at ? `<div class="small">Next billing boundary: ${fmtDate(summary.renews_at)}</div>` : '<div class="small">No renewal date scheduled.</div>';
  const cancelLine = summary.cancel_reason ? `<div class="small">Last cancel reason: ${escapeHtml(summary.cancel_reason)}</div>` : '';
  renderShell(`
    <div class="notice">Plan: <strong>${escapeHtml(summary.plan)}</strong> • Status: <strong>${escapeHtml(summary.plan_status)}</strong> • Billing mode: <strong>${escapeHtml(summary.billing_mode)}</strong></div>
    <div class="grid grid-2">
      <div class="card grid" style="gap:12px">
        <h2 style="margin:0">Billing summary</h2>
        <div class="small">Current plan: ${escapeHtml(summary.plan)}</div>
        ${trialLine}
        ${renewLine}
        ${cancelLine}
        <div class="small">Pro beta price: $${summary.pro_monthly_price_usd}/month after ${summary.beta_trial_days}-day trial.</div>
        <div class="small">Use the self-serve controls below to start a trial, convert it, or cancel it. Contact ${escapeHtml(summary.support_email)} if you need manual support.</div>
      </div>
      <div class="card grid" style="gap:12px">
        <h2 style="margin:0">Plan actions</h2>
        <div class="inline-actions">
          ${summary.can_start_trial ? '<button id="billing-start-trial">Start beta trial</button>' : ''}
          ${summary.can_upgrade ? '<button id="billing-upgrade">Upgrade to Pro</button>' : ''}
          ${summary.can_cancel ? '<button class="secondary" id="billing-cancel">Cancel plan</button>' : ''}
          <button class="ghost" id="billing-onboarding-link">Onboarding</button>
        </div>
        <label>Cancellation reason
          <textarea id="billing-cancel-reason" placeholder="Why are you canceling the beta plan?">${escapeHtml(summary.cancel_reason || '')}</textarea>
        </label>
        <div class="small">Support: ${escapeHtml(summary.support_email)}</div>
        <div id="billing-feedback"></div>
      </div>
    </div>
  `);
  document.querySelector('#billing-onboarding-link')?.addEventListener('click', () => { navigate('#/onboarding'); render(); });
  document.querySelector('#billing-start-trial')?.addEventListener('click', async () => {
    try {
      await api('/billing/start-trial', { method: 'POST' });
      await renderBilling();
    } catch (error) {
      document.querySelector('#billing-feedback').innerHTML = `<div class="error">${error.message}</div>`;
    }
  });
  document.querySelector('#billing-upgrade')?.addEventListener('click', async () => {
    try {
      await api('/billing/upgrade', { method: 'POST' });
      await renderBilling();
    } catch (error) {
      document.querySelector('#billing-feedback').innerHTML = `<div class="error">${error.message}</div>`;
    }
  });
  document.querySelector('#billing-cancel')?.addEventListener('click', async () => {
    const reason = document.querySelector('#billing-cancel-reason').value.trim();
    try {
      await api('/billing/cancel', { method: 'POST', body: JSON.stringify({ reason }) });
      await renderBilling();
    } catch (error) {
      document.querySelector('#billing-feedback').innerHTML = `<div class="error">${error.message}</div>`;
    }
  });
}


function renderLogin(message = '') {
  app.innerHTML = `
    <div class="container grid" style="max-width:720px">
      <div class="card grid" style="gap:16px">
        <div class="kicker">Follow-Up Radar</div>
        <h1 style="margin:0">Request a sign-in link</h1>
        ${message ? `<div class="notice">${message}</div>` : ''}
        <label>Email
          <input id="request-email" type="email" placeholder="you@example.com" />
        </label>
        <div class="inline-actions">
          <button id="request-link">Request magic link</button>
        </div>
        <div class="small">
          In development mode, the link is written to the file outbox configured by <span class="mono">DEV_EMAIL_OUTBOX_PATH</span>.
        </div>
      </div>
      <div class="card grid" style="gap:16px">
        <h2 style="margin:0">Verify token manually</h2>
        <label>Email
          <input id="verify-email" type="email" placeholder="you@example.com" />
        </label>
        <label>Token
          <input id="verify-token" type="text" placeholder="paste token here" />
        </label>
        <div class="inline-actions">
          <button class="secondary" id="verify-link">Verify and sign in</button>
        </div>
      </div>
    </div>
  `;
  document.querySelector('#request-link').addEventListener('click', async () => {
    const email = document.querySelector('#request-email').value.trim();
    try {
      await api('/auth/request-magic-link', { method: 'POST', body: JSON.stringify({ email }) });
      renderLogin('Magic link requested. Check the development outbox file, then paste the token below or open the delivered URL.');
    } catch (error) {
      renderLogin(`<span class="error">${error.message}</span>`);
    }
  });
  document.querySelector('#verify-link').addEventListener('click', verifyManual);
}

async function verifyManual() {
  const email = document.querySelector('#verify-email').value.trim();
  const token = document.querySelector('#verify-token').value.trim();
  try {
    const payload = await api('/auth/verify', { method: 'POST', body: JSON.stringify({ email, token }) });
    setAccessToken(payload.access_token);
    navigate('#/');
    await render();
  } catch (error) {
    renderLogin(`<span class="error">${error.message}</span>`);
  }
}

function renderVerify() {
  const [, queryString = ''] = window.location.hash.split('?');
  const query = new URLSearchParams(queryString);
  const email = query.get('email') || '';
  const token = query.get('token') || '';
  app.innerHTML = `
    <div class="container" style="max-width:720px">
      <div class="card grid" style="gap:16px">
        <div class="kicker">Follow-Up Radar</div>
        <h1 style="margin:0">Verify sign-in link</h1>
        <div class="notice">The email and token below were taken from the delivered magic link. Press verify to create a session.</div>
        <label>Email
          <input id="verify-email" type="email" value="${email}" />
        </label>
        <label>Token
          <input id="verify-token" type="text" value="${token}" />
        </label>
        <div class="inline-actions">
          <button id="verify-link">Verify and sign in</button>
          <button class="ghost" id="back-link">Back</button>
        </div>
      </div>
    </div>
  `;
  document.querySelector('#verify-link').addEventListener('click', verifyManual);
  document.querySelector('#back-link').addEventListener('click', () => { navigate('#/login'); render(); });
}

function renderScopeButton(value, selected, label) {
  const cls = value === selected ? '' : 'ghost';
  return `<button class="${cls}" data-scope="${value}">${label}</button>`;
}

function renderSelectOptions(options, selectedValue) {
  return options.map(([value, label]) => `<option value="${value}" ${value === selectedValue ? 'selected' : ''}>${label}</option>`).join('');
}

function renderSignalChip(signal) {
  return `<span class="signal-chip signal-${signal.severity}">${escapeHtml(signal.label)}</span>`;
}

function registryContextLine(item) {
  const parts = [escapeHtml(item.type), `due ${fmtDate(item.due_at)}`];
  return parts.join(' • ');
}

function registryNextActionMarkup(item) {
  if (!item.next_action || !isActiveStatus(item.status)) return '';
  return `<div class="small"><strong>Next action:</strong> ${escapeHtml(item.next_action)}</div>`;
}

function registrySecondarySummary(item) {
  if (item.status === 'done' && item.done_reason) {
    return `Done reason: ${escapeHtml(item.done_reason)}`;
  }
  if (item.status === 'lost' && item.lost_reason) {
    return `Lost reason: ${escapeHtml(item.lost_reason)}`;
  }
  return escapeHtml(item.last_event_summary || 'No case events yet.');
}

function casesToolbarMarkup(state) {
  const appliedCount = countAppliedFilters(state);
  return `
    <div class="card grid" style="gap:14px">
      <div class="section-title">
        <h3 style="margin:0">Search and sorting</h3>
        <div class="inline-actions">
          <button class="ghost" id="toggle-filters">Filters${appliedCount ? ` (${appliedCount})` : ''}</button>
        </div>
      </div>
      <div class="grid cases-toolbar-grid">
        <label>Search
          <input id="cases-q" placeholder="Client, title, or next action" value="${escapeHtml(state.q)}" />
        </label>
        <label>Sort by
          <select id="cases-sort-by">
            ${renderSelectOptions([
              ['due_at', 'Due date'],
              ['last_activity', 'Last activity'],
              ['created_at', 'Created date'],
              ['amount', 'Amount'],
              ['client_name', 'Client name'],
            ], state.sort_by)}
          </select>
        </label>
        <label>Order
          <select id="cases-sort-dir">
            ${renderSelectOptions([
              ['asc', 'Ascending'],
              ['desc', 'Descending'],
            ], state.sort_dir)}
          </select>
        </label>
      </div>
      <div class="inline-actions">
        <button id="cases-toolbar-apply">Apply</button>
      </div>
    </div>
  `;
}

function casesDrawerMarkup(state) {
  return `
    <div class="card grid hidden" id="cases-filter-drawer" style="gap:16px">
      <div class="section-title">
        <h3 style="margin:0">Filters</h3>
        <button class="ghost" id="close-filters">Close</button>
      </div>
      <div class="grid grid-3 filter-grid">
        <label>Case status
          <select id="cases-status">
            ${renderSelectOptions([
              ['', 'Any'],
              ['open', 'Open'],
              ['due_today', 'Due today'],
              ['overdue', 'Overdue'],
              ['done', 'Done'],
              ['lost', 'Lost'],
            ], state.status)}
          </select>
        </label>
        <label>Payment status
          <select id="cases-payment-status">
            ${renderSelectOptions([
              ['', 'Any'],
              ['unpaid', 'Unpaid'],
              ['paid', 'Paid'],
              ['not_applicable', 'N/A'],
            ], state.payment_status)}
          </select>
        </label>
        <label>Type
          <select id="cases-type">
            ${renderSelectOptions([
              ['', 'Any'],
              ['invoice', 'Invoice'],
              ['proposal', 'Proposal'],
              ['lead', 'Lead'],
              ['promised_reply', 'Promised reply'],
              ['renewal', 'Renewal'],
            ], state.item_type)}
          </select>
        </label>
        <label>Due bucket
          <select id="cases-due-bucket">
            ${renderSelectOptions([
              ['', 'Any'],
              ['overdue', 'Overdue'],
              ['due_today', 'Due today'],
              ['scheduled', 'Scheduled'],
            ], state.due_bucket)}
          </select>
        </label>
        <label>Review signal
          <select id="cases-review-signal">
            ${renderSelectOptions([
              ['', 'Any'],
              ['paid_but_open', 'Paid but open'],
              ['stale_case', 'No activity 7+ days'],
              ['reminder_failed', 'Reminder failed'],
              ['overdue_without_reminder', 'Overdue without reminder'],
            ], state.review_signal)}
          </select>
        </label>
        <div></div>
        <label>Due from
          <input id="cases-due-from" type="date" value="${escapeHtml(state.due_from)}" />
        </label>
        <label>Due to
          <input id="cases-due-to" type="date" value="${escapeHtml(state.due_to)}" />
        </label>
        <div></div>
        <label>Amount min
          <input id="cases-amount-min" type="number" step="0.01" value="${escapeHtml(state.amount_min)}" />
        </label>
        <label>Amount max
          <input id="cases-amount-max" type="number" step="0.01" value="${escapeHtml(state.amount_max)}" />
        </label>
      </div>
      <div class="inline-actions">
        <button id="cases-apply">Apply filters</button>
        <button class="ghost" id="cases-reset">Reset</button>
      </div>
    </div>
  `;
}

function reviewViewsMarkup(state) {
  const views = [
    { key: 'needs_action', label: 'Needs action', next: { scope: 'active', review_signal: 'needs_action' } },
    { key: 'paid_but_open', label: 'Paid but open', next: { scope: 'active', review_signal: 'paid_but_open' } },
    { key: 'stale_case', label: 'Stale', next: { scope: 'all', review_signal: 'stale_case' } },
    { key: 'reminder_issue', label: 'Reminder issues', next: { scope: 'all', review_signal: 'reminder_issue' } },
  ];
  return `
    <div class="card grid" style="gap:12px">
      <div class="section-title"><h3 style="margin:0">Review views</h3></div>
      <div class="inline-actions">
        ${views.map((view) => {
          const selected = state.review_signal === view.next.review_signal;
          return `<button class="${selected ? '' : 'ghost'}" data-review-view="${view.key}">${view.label}</button>`;
        }).join('')}
      </div>
    </div>
  `;
}

function appliedFilterChipsMarkup(state) {
  const entries = activeFilterEntries(state);
  if (entries.length === 0) {
    return '';
  }
  return `
    <div class="card applied-filters-card">
      <div class="section-title">
        <div class="small"><strong>Applied filters</strong></div>
        <button class="ghost" id="cases-clear-all">Clear all</button>
      </div>
      <div class="inline-actions">
        ${entries.map((entry) => `<button class="chip-button ghost" data-clear-filter="${entry.key}">${escapeHtml(entry.label)} ✕</button>`).join('')}
      </div>
    </div>
  `;
}

function reminderStatusLabel(item) {
  if (!item.last_reminder_status) return 'No reminder recorded yet';
  const base = {
    pending: 'Pending',
    sent: 'Sent',
    failed: 'Failed',
    canceled: 'Canceled',
  }[item.last_reminder_status] || item.last_reminder_status;
  const at = item.last_reminder_at ? fmtDate(item.last_reminder_at) : null;
  if (item.last_reminder_status === 'failed' && item.last_reminder_error) {
    return `${base} — ${escapeHtml(item.last_reminder_error)}`;
  }
  return at ? `${base} at ${at}` : base;
}

async function renderCases(path) {
  try {
    const state = parseCasesState(path || '#/cases?scope=all');
    const [me, registry, activation] = await Promise.all([
      api('/auth/me'),
      api(registryApiPath(state)),
      api('/v1/system/activation-summary'),
    ]);
    const emptyRegistryState = registry.items.length === 0 ? `
      <div class="card grid" style="gap:12px">
        <h3 style="margin:0">No cases match this view</h3>
        <div class="small">${activation.total_cases === 0 ? 'Start with a sample case or create your first real case.' : 'Clear filters or change the review view to widen the registry.'}</div>
        <div class="inline-actions">
          ${activation.total_cases === 0 ? '<button id="cases-create-sample">Create sample case</button>' : ''}
          <button class="ghost" id="cases-open-dashboard">Dashboard</button>
          ${countAppliedFilters(state) ? '<button class="ghost" id="cases-empty-clear">Clear filters</button>' : ''}
        </div>
      </div>
    ` : '';
    renderShell(`
      <div class="notice">Signed in as <strong>${me.email}</strong>. Registry scope: <span class="mono">${registry.scope}</span></div>
      ${casesToolbarMarkup(state)}
      ${casesDrawerMarkup(state)}
      ${appliedFilterChipsMarkup(state)}
      ${reviewViewsMarkup(state)}
      ${emptyRegistryState}
      <div class="card grid" style="gap:16px">
        <div class="section-title">
          <h2 style="margin:0">Cases</h2>
          <div class="inline-actions">
            ${renderScopeButton('all', registry.scope, `All (${registry.counts.all})`)}
            ${renderScopeButton('active', registry.scope, `Active (${registry.counts.active})`)}
            ${renderScopeButton('closed', registry.scope, `Closed (${registry.counts.closed})`)}
          </div>
        </div>
        <div class="registry-list">
          ${registry.items.length === 0 ? '<div class="kicker">No cases in this view.</div>' : registry.items.map((item) => `
            <div class="registry-row">
              <div class="registry-main">
                <strong>${escapeHtml(item.client_name)} — ${escapeHtml(item.title)}</strong>
                <div class="inline-actions case-meta-line">
                  ${renderLifecycleBadge(item.status)}
                  ${renderPaymentText(item.payment_status)}
                </div>
                ${item.review_signals?.length ? `<div class="inline-actions case-signal-line">${item.review_signals.map(renderSignalChip).join('')}</div>` : ''}
                <div class="kicker">${registryContextLine(item)}</div>
                ${registryNextActionMarkup(item)}
                <div class="kicker">Created ${fmtDate(item.created_at)} • Last activity ${item.last_event_at ? fmtDate(item.last_event_at) : '—'}</div>
                <div class="small">${registrySecondarySummary(item)}</div>
              </div>
              <div class="registry-meta">
                <div class="badge">${item.amount ? `${escapeHtml(String(item.amount))} ${escapeHtml(item.currency || '')}`.trim() : '—'}</div>
                <button class="ghost" data-open-item="${item.id}">Open</button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `);

    const drawer = document.querySelector('#cases-filter-drawer');
    const hideDrawer = () => drawer.classList.add('hidden');

    document.querySelector('#toggle-filters')?.addEventListener('click', () => {
      drawer.classList.toggle('hidden');
    });
    document.querySelector('#close-filters')?.addEventListener('click', hideDrawer);

    const collectState = () => ({
      scope: state.scope,
      q: document.querySelector('#cases-q').value.trim(),
      sort_by: document.querySelector('#cases-sort-by').value,
      sort_dir: document.querySelector('#cases-sort-dir').value,
      status: document.querySelector('#cases-status').value,
      payment_status: document.querySelector('#cases-payment-status').value,
      item_type: document.querySelector('#cases-type').value,
      due_bucket: document.querySelector('#cases-due-bucket').value,
      due_from: document.querySelector('#cases-due-from').value,
      due_to: document.querySelector('#cases-due-to').value,
      amount_min: document.querySelector('#cases-amount-min').value,
      amount_max: document.querySelector('#cases-amount-max').value,
      review_signal: document.querySelector('#cases-review-signal').value,
    });

    const applyFromUi = () => {
      navigate(buildCasesHash(collectState()));
      render();
    };

    document.querySelector('#cases-toolbar-apply')?.addEventListener('click', applyFromUi);
    document.querySelector('#cases-apply')?.addEventListener('click', () => {
      applyFromUi();
      hideDrawer();
    });
    document.querySelector('#cases-reset')?.addEventListener('click', () => {
      navigate('#/cases?scope=all');
      render();
    });
    document.querySelector('#cases-clear-all')?.addEventListener('click', () => {
      navigate(`#/cases?scope=${state.scope || 'all'}`);
      render();
    });
    document.querySelector('#cases-empty-clear')?.addEventListener('click', () => {
      navigate('#/cases?scope=all');
      render();
    });
    document.querySelector('#cases-open-dashboard')?.addEventListener('click', () => {
      navigate('#/');
      render();
    });
    document.querySelector('#cases-create-sample')?.addEventListener('click', async () => {
      try {
        const item = await api('/v1/system/bootstrap-sample-case', { method: 'POST' });
        navigate(`#/item/${item.id}`);
        await render();
      } catch (error) {
        app.insertAdjacentHTML('afterbegin', `<div class="error">${error.message}</div>`);
      }
    });
    for (const button of document.querySelectorAll('[data-clear-filter]')) {
      button.addEventListener('click', () => {
        const nextState = { ...state, [button.dataset.clearFilter]: '' };
        navigate(buildCasesHash(nextState));
        render();
      });
    }
    for (const button of document.querySelectorAll('[data-review-view]')) {
      button.addEventListener('click', () => {
        const map = {
          needs_action: { scope: 'active', review_signal: 'needs_action' },
          paid_but_open: { scope: 'active', review_signal: 'paid_but_open' },
          stale_case: { scope: 'all', review_signal: 'stale_case' },
          reminder_issue: { scope: 'all', review_signal: 'reminder_issue' },
        };
        navigate(buildCasesHash({ ...defaultCasesState(), ...map[button.dataset.reviewView] }));
        render();
      });
    }
    for (const button of document.querySelectorAll('[data-scope]')) {
      button.addEventListener('click', () => {
        const nextState = { ...state, scope: button.dataset.scope };
        navigate(buildCasesHash(nextState));
        render();
      });
    }
    for (const button of document.querySelectorAll('[data-open-item]')) {
      button.addEventListener('click', () => navigate(`#/item/${button.dataset.openItem}`));
    }
  } catch (error) {
    renderShell(`<div class="error">${error.message}</div>`);
  }
}


async function renderDashboard() {
  try {
    const [me, board, activation, billing] = await Promise.all([
      api('/auth/me'),
      api('/items/board'),
      api('/v1/system/activation-summary'),
      api('/billing/summary'),
    ]);
    const totalBoardItems = board.overdue.length + board.due_today.length + board.scheduled.length;
    const trialNotice = billing.plan_status === 'trialing'
      ? `<div class="notice">Pro beta trial active${billing.trial_days_left !== null ? ` — ${billing.trial_days_left} day(s) left` : ''}. Review Billing when you are ready to convert.</div>`
      : '';
    const freePlanNotice = billing.plan === 'free'
      ? `<div class="notice">You are on the Free plan. When the workflow feels reliable, start a beta trial from <button class="ghost inline-link-button" id="dashboard-open-billing">Billing</button>.</div>`
      : '';
    const activationCard = activation.should_show_activation ? `
      <div class="card grid" style="gap:14px">
        <div class="section-title">
          <h2 style="margin:0">Activation checklist</h2>
          <span class="badge">${activation.total_cases} case(s)</span>
        </div>
        <div class="small">${escapeHtml(activation.suggested_next_step)}</div>
        <div class="grid" style="gap:10px">
          ${activation.milestones.map((milestone) => `
            <div class="activation-row">
              <span class="activation-check ${milestone.completed ? 'activation-done' : 'activation-pending'}">${milestone.completed ? '✓' : '•'}</span>
              <span>${escapeHtml(milestone.label)}</span>
            </div>
          `).join('')}
        </div>
        <div class="inline-actions">
          <button id="activation-create-sample">Create sample case</button>
          <button class="ghost" id="activation-open-onboarding">Onboarding</button>
          <button class="ghost" id="activation-open-cases">Open Cases</button>
        </div>
      </div>
    ` : '';
    const emptyBoardState = totalBoardItems === 0 ? `
      <div class="card grid" style="gap:12px">
        <h2 style="margin:0">Start with one case</h2>
        <div class="small">Radar becomes useful when one real or sample case moves through create, review, payment, and close.</div>
        <div class="inline-actions">
          <button id="board-create-sample">Create sample case</button>
          <button class="ghost" id="board-open-onboarding">View onboarding</button>
        </div>
      </div>
    ` : '';
    renderShell(`
      <div class="notice">Signed in as <strong>${me.email}</strong>. API base: <span class="mono">${API_BASE_URL}</span></div>
      ${trialNotice}
      ${freePlanNotice}
      ${activationCard}
      <div class="grid grid-2">
        <div class="card grid" style="gap:14px">
          <div class="section-title"><h2 style="margin:0">Create follow-up</h2></div>
          <label>Title<input id="create-title" placeholder="Follow up on invoice 1024" /></label>
          <label>Client name<input id="create-client" placeholder="Client A" /></label>
          <label>Type
            <select id="create-type">
              <option value="invoice">Invoice</option>
              <option value="proposal">Proposal</option>
              <option value="lead">Lead</option>
              <option value="promised_reply">Promised reply</option>
              <option value="renewal">Renewal</option>
            </select>
          </label>
          <label>Due at<input id="create-due" type="datetime-local" /></label>
          <label>Amount<input id="create-amount" type="number" step="0.01" placeholder="250.00" /></label>
          <label>Currency<input id="create-currency" value="USD" /></label>
          <label>Source URL<input id="create-url" placeholder="https://example.com/invoice/1024" /></label>
          <label>Next action<input id="create-next-action" placeholder="Confirm payment receipt" /></label>
          <label>Note<textarea id="create-note" placeholder="Sent yesterday, follow up tomorrow."></textarea></label>
          <div class="inline-actions">
            <button id="create-submit">Create item</button>
          </div>
          <div id="create-feedback"></div>
        </div>
        <div class="grid" style="gap:16px">
          ${emptyBoardState}
          ${renderBoardSection('Overdue', board.overdue)}
          ${renderBoardSection('Due today', board.due_today)}
          ${renderBoardSection('Scheduled', board.scheduled)}
        </div>
      </div>
    `);
    const createSample = async () => {
      try {
        const item = await api('/v1/system/bootstrap-sample-case', { method: 'POST' });
        navigate(`#/item/${item.id}`);
        await render();
      } catch (error) {
        document.querySelector('#create-feedback').innerHTML = `<div class="error">${error.message}</div>`;
      }
    };
    document.querySelector('#dashboard-open-billing')?.addEventListener('click', () => { navigate('#/billing'); render(); });
    document.querySelector('#activation-create-sample')?.addEventListener('click', createSample);
    document.querySelector('#board-create-sample')?.addEventListener('click', createSample);
    document.querySelector('#activation-open-onboarding')?.addEventListener('click', () => { navigate('#/onboarding'); render(); });
    document.querySelector('#board-open-onboarding')?.addEventListener('click', () => { navigate('#/onboarding'); render(); });
    document.querySelector('#activation-open-cases')?.addEventListener('click', () => { navigate('#/cases?scope=all'); render(); });
    document.querySelector('#create-submit').addEventListener('click', async () => {
      const dueLocal = document.querySelector('#create-due').value;
      try {
        await api('/items', {
          method: 'POST',
          body: JSON.stringify({
            title: document.querySelector('#create-title').value.trim(),
            client_name: document.querySelector('#create-client').value.trim(),
            type: document.querySelector('#create-type').value,
            due_at: new Date(dueLocal).toISOString(),
            amount: document.querySelector('#create-amount').value || null,
            currency: document.querySelector('#create-currency').value.trim() || null,
            source_url: document.querySelector('#create-url').value.trim() || null,
            next_action: document.querySelector('#create-next-action').value.trim() || null,
            note: document.querySelector('#create-note').value.trim() || null,
          }),
        });
        await renderDashboard();
      } catch (error) {
        document.querySelector('#create-feedback').innerHTML = `<div class="error">${error.message}</div>`;
      }
    });
    for (const button of document.querySelectorAll('[data-open-item]')) {
      button.addEventListener('click', () => navigate(`#/item/${button.dataset.openItem}`));
    }
  } catch (error) {
    clearAccessToken();
    renderLogin(`<span class="error">${error.message}</span>`);
  }
}

function renderBoardSection(title, items) {
  return `
    <div class="card">
      <div class="section-title">
        <h2 style="margin:0">${title}</h2>
        <span class="badge">${items.length}</span>
      </div>
      <div class="item-list">
        ${items.length === 0 ? `<div class="kicker">No cases in ${title.toLowerCase()}.</div>` : items.map((item) => `
          <div class="item-row">
            <div>
              <strong>${escapeHtml(item.client_name)} — ${escapeHtml(item.title)}</strong>
              <div class="inline-actions case-meta-line">
                ${renderLifecycleBadge(item.status)}
                ${renderPaymentText(item.payment_status)}
              </div>
              <div class="kicker">${item.type} • due ${fmtDate(item.due_at)}</div>
              ${item.next_action ? `<div class="small">Next: ${escapeHtml(item.next_action)}</div>` : ''}
            </div>
            <div class="inline-actions">
              <button class="ghost" data-open-item="${item.id}">Open</button>
            </div>
          </div>`).join('')}
      </div>
    </div>
  `;
}


function classifyItemEvents(events) {
  const stateEventTypes = new Set(['item_created', 'item_status_changed', 'item_payment_status_changed', 'item_archived']);
  return {
    stateEvents: events.filter((event) => stateEventTypes.has(event.event_type)),
    operationalEvents: events.filter((event) => !stateEventTypes.has(event.event_type)),
  };
}

function lastEventSummary(events, preferredEventTypes, emptyLabel) {
  const found = events.find((event) => preferredEventTypes.includes(event.event_type));
  if (!found) return emptyLabel;
  return `${fmtDate(found.created_at)} — ${escapeHtml(found.summary)}`;
}

function renderEventList(events, emptyLabel) {
  if (events.length === 0) {
    return `<div class="kicker">${escapeHtml(emptyLabel)}</div>`;
  }
  return events.map((event) => `
    <div class="item-row">
      <div>
        <strong>${escapeHtml(event.summary)}</strong>
        <div class="kicker">${fmtDate(event.created_at)} • ${escapeHtml(event.event_type)}</div>
      </div>
    </div>
  `).join('');
}

function outcomeReasonLabel(item) {
  if (item.status === 'done' && item.done_reason) {
    return `Outcome reason: ${item.done_reason}`;
  }
  if (item.status === 'lost' && item.lost_reason) {
    return `Outcome reason: ${item.lost_reason}`;
  }
  return null;
}

async function renderItemDetail(itemId) {
  try {
    const [item, events] = await Promise.all([
      api(`/items/${itemId}`),
      api(`/items/${itemId}/events`),
    ]);
    const { stateEvents, operationalEvents } = classifyItemEvents(events);
    const lastLifecycleChange = lastEventSummary(
      events,
      ['item_status_changed', 'item_created', 'item_archived'],
      'No lifecycle changes recorded yet.',
    );
    const lastPaymentUpdate = item.payment_status === 'not_applicable'
      ? 'Payment is not applicable for this case.'
      : lastEventSummary(events, ['item_payment_status_changed'], 'No payment updates recorded yet.');
    const paymentAction = item.payment_status === 'not_applicable'
      ? ''
      : `<button class="secondary" id="mark-paid" ${item.payment_status === 'paid' ? 'disabled' : ''}>${item.payment_status === 'paid' ? 'Payment marked' : 'Mark paid'}</button>`;
    const canMutate = !isTerminalStatus(item.status);
    const canReopen = ['done', 'lost'].includes(item.status);
    renderShell(`
      <div class="grid grid-2">
        <div class="card grid" style="gap:14px">
          <div class="kicker">Item detail</div>
          <h2 style="margin:0">${escapeHtml(item.client_name)} — ${escapeHtml(item.title)}</h2>
          <div class="state-block">
            <div class="inline-actions case-meta-line">
              ${renderLifecycleBadge(item.status)}
              ${renderPaymentText(item.payment_status)}
            </div>
            ${item.review_signals?.length ? `<div class="inline-actions case-signal-line">${item.review_signals.map(renderSignalChip).join('')}</div>` : ''}
            <div class="state-summary-grid">
              <div>
                <div class="kicker">Last case status change</div>
                <div class="state-summary-value">${lastLifecycleChange}</div>
              </div>
              <div>
                <div class="kicker">Last payment update</div>
                <div class="state-summary-value">${lastPaymentUpdate}</div>
              </div>
              <div>
                <div class="kicker">Last reminder state</div>
                <div class="state-summary-value">${reminderStatusLabel(item)}</div>
              </div>
              <div>
                <div class="kicker">Next action</div>
                <div class="state-summary-value">${escapeHtml(item.next_action || 'No next action set')}</div>
              </div>
            </div>
          </div>
          <div class="grid" style="gap:8px">
            <div><strong>Type:</strong> ${item.type}</div>
            <div><strong>Due at:</strong> ${fmtDate(item.due_at)}</div>
            <div><strong>Amount:</strong> ${item.amount || '—'} ${item.currency || ''}</div>
            <div><strong>Source URL:</strong> ${item.source_url ? `<a href="${item.source_url}" target="_blank">open</a>` : '—'}</div>
            <div><strong>Next action:</strong> ${escapeHtml(item.next_action || '—')}</div>
            ${outcomeReasonLabel(item) ? `<div><strong>${escapeHtml(outcomeReasonLabel(item))}</strong></div>` : ''}
            <div><strong>Note:</strong><br/>${escapeHtml(item.note || '—')}</div>
          </div>
        </div>
        <div class="card grid" style="gap:14px">
          <div class="section-title"><h2 style="margin:0">Actions</h2></div>
          <label>Reschedule
            <input id="reschedule-due" type="datetime-local" ${canMutate ? '' : 'disabled'} />
          </label>
          <label>Next action
            <input id="next-action-input" placeholder="Confirm payment receipt" value="${escapeHtml(item.next_action || '')}" ${canMutate ? '' : 'disabled'} />
          </label>
          <label>Outcome reason
            <textarea id="outcome-reason" placeholder="Why is this case done or lost?" ${canMutate ? '' : 'disabled'}></textarea>
          </label>
          <div class="inline-actions">
            <button id="reschedule-submit" ${canMutate ? '' : 'disabled'}>Reschedule</button>
            <button class="secondary" id="save-next-action" ${canMutate ? '' : 'disabled'}>Save next action</button>
            ${paymentAction}
            <button class="secondary" id="mark-done" ${canMutate ? '' : 'disabled'}>Mark done</button>
            <button class="secondary" id="mark-lost" ${canMutate ? '' : 'disabled'}>Mark lost</button>
            ${canReopen ? '<button class="ghost" id="reopen-case">Reopen case</button>' : ''}
            <button class="ghost" id="back-dashboard">Back to dashboard</button>
          </div>
          <div id="detail-feedback"></div>
        </div>
      </div>
      <div class="card grid" style="gap:14px; margin-top:16px">
        <div class="section-title"><h2 style="margin:0">Activity</h2></div>
        <div class="grid" style="gap:16px">
          <div>
            <div class="kicker">State changes</div>
            <div class="item-list">${renderEventList(stateEvents, 'No state changes recorded yet.')}</div>
          </div>
          <div>
            <div class="kicker">Operational activity</div>
            <div class="item-list">${renderEventList(operationalEvents, 'No operational activity recorded yet.')}</div>
          </div>
        </div>
      </div>
    `);
    document.querySelector('#reschedule-submit').addEventListener('click', () => completeAction(async () => {
      const dueLocal = document.querySelector('#reschedule-due').value;
      await api(`/items/${itemId}/reschedule`, { method: 'POST', body: JSON.stringify({ due_at: new Date(dueLocal).toISOString() }) });
      await renderItemDetail(itemId);
    }));
    document.querySelector('#save-next-action').addEventListener('click', () => completeAction(async () => {
      const nextAction = document.querySelector('#next-action-input').value.trim();
      await api(`/items/${itemId}`, { method: 'PATCH', body: JSON.stringify({ next_action: nextAction || null }) });
      await renderItemDetail(itemId);
    }));
    document.querySelector('#mark-paid')?.addEventListener('click', () => completeAction(async () => {
      await api(`/items/${itemId}/mark-paid`, { method: 'POST' });
      await renderItemDetail(itemId);
    }));
    document.querySelector('#mark-done').addEventListener('click', () => outcomeAction(itemId, 'done'));
    document.querySelector('#mark-lost').addEventListener('click', () => outcomeAction(itemId, 'lost'));
    document.querySelector('#reopen-case')?.addEventListener('click', () => completeAction(async () => {
      await api(`/items/${itemId}/reopen`, { method: 'POST' });
      await renderItemDetail(itemId);
    }));
    document.querySelector('#back-dashboard').addEventListener('click', () => { navigate('#/'); render(); });
  } catch (error) {
    renderShell(`<div class="error">${error.message}</div>`);
  }
}

function completeAction(fn) {
  fn().catch((error) => {
    document.querySelector('#detail-feedback').innerHTML = `<div class="error">${error.message}</div>`;
  });
}

function outcomeAction(itemId, outcome) {
  completeAction(async () => {
    const reason = document.querySelector('#outcome-reason').value.trim();
    if (!reason) {
      throw new Error(`Reason is required when marking case ${outcome}`);
    }
    await api(`/items/${itemId}/complete`, { method: 'POST', body: JSON.stringify({ outcome, reason }) });
    await renderItemDetail(itemId);
  });
}


function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

window.addEventListener('hashchange', () => render());
render();
