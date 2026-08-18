/* ── STATE ────────────────────────────────────────────────── */
let inboxEmails = [];
let spamEmails  = [];   // kept for badge only — not rendered
let activeId    = null;
let currentTab  = 'inbox';
let inboxNextPage = null;
let spamNextPage  = null;
let _scrollFetch  = false;

function getEmails()   { return inboxEmails; }
function getNextPage() { return inboxNextPage; }

/* ── GMAIL AUTH ───────────────────────────────────────────── */
async function connectGmail() {
  const btn = $('connectGmailBtn');
  if (btn.classList.contains('connected')) {
    await fetch('/gmail/logout');
    btn.classList.remove('connected');
    $('gmailBtnText').textContent = 'Connect Gmail';
    inboxEmails = []; spamEmails = [];
    inboxNextPage = null; spamNextPage = null;
    renderEmailList(); updateBadges(); updateDashStats();
    showToast('Disconnected from Gmail');
    return;
  }
  showToast('Redirecting to Google...');
  const resp = await fetch('/gmail/auth');
  const data = await resp.json();
  window.location.href = data.auth_url;
}

async function checkGmailStatus() {
  try {
    const resp = await fetch('/gmail/status');
    const data = await resp.json();
    if (data.connected) {
      const btn = $('connectGmailBtn');
      btn.classList.add('connected');
      $('gmailBtnText').textContent = 'Gmail Connected';
      // Inbox only — no spam tab
      if (inboxEmails.length === 0) {
        loadGmailInbox();
      }
    }
  } catch (_) { }
}

/* ── LOAD INBOX ───────────────────────────────────────────── */
async function loadGmailInbox(pageToken = null) {
  showToast('Loading inbox...');
  setProgress(20);
  try {
    let url = '/gmail/inbox?max_results=100';
    if (pageToken) url += '&page_token=' + encodeURIComponent(pageToken);
    const resp = await fetch(url);
    setProgress(70);
    if (resp.status === 401) { showToast('Connect Gmail first'); setProgress(null); return; }
    if (!resp.ok) { const e = await resp.json(); showToast(e.error || 'Failed'); setProgress(null); return; }
    const data = await resp.json();
    inboxNextPage = data.next_page_token || null;
    (data.messages || []).forEach(e => { e.time = formatTime(); inboxEmails.push(e); });
    renderEmailList();
    updateBadges(); updateDashStats();
    setProgress(null);
    showToast('Loaded ' + (data.messages || []).length + ' inbox emails');
  } catch (err) {
    console.error(err);
    showToast('Could not reach server');
    setProgress(null);
  }
}

/* ── LOAD SPAM ────────────────────────────────────────────── */
async function loadGmailSpam(pageToken = null) {
  showToast('Loading spam...');
  setProgress(20);
  try {
    let url = '/gmail/inbox?label=SPAM&max_results=100';
    if (pageToken) url += '&page_token=' + encodeURIComponent(pageToken);
    const resp = await fetch(url);
    setProgress(70);
    if (resp.status === 401) { showToast('Connect Gmail first'); setProgress(null); return; }
    if (!resp.ok) { const e = await resp.json(); showToast(e.error || 'Failed'); setProgress(null); return; }
    const data = await resp.json();
    spamNextPage = data.next_page_token || null;
    (data.messages || []).forEach(e => { e.time = formatTime(); spamEmails.unshift(e); });
    if (currentTab === 'spam') renderEmailList();
    updateBadges(); updateDashStats();
    setProgress(null);
    showToast('Loaded ' + (data.messages || []).length + ' spam emails');
  } catch (err) {
    console.error(err);
    showToast('Could not reach server');
    setProgress(null);
  }
}


/* ── INFINITE SCROLL ──────────────────────────────────────── */
const _sentinel = new IntersectionObserver(entries => {
  if (entries[0].isIntersecting && getNextPage() && !_scrollFetch) {
    _scrollFetch = true;
    loadGmailInbox(getNextPage()).finally(() => { _scrollFetch = false; });
  }
}, { threshold: 0.5 });

/* ── MODALS ───────────────────────────────────────────────── */
function openGuidelines() { $('guidelinesBackdrop').style.display = 'flex'; }
function closeGuidelines() { $('guidelinesBackdrop').style.display = 'none'; }
function openWhyPhishy() { $('whyPhishyBackdrop').style.display = 'flex'; }
function closeWhyPhishy() { $('whyPhishyBackdrop').style.display = 'none'; }

/* ── DASHBOARD STATS ──────────────────────────────────────── */
function updateDashStats() {
  const all = [...inboxEmails];
  const total = all.length;
  const high = all.filter(e => e.risk_level === 'High').length;
  const medium = all.filter(e => e.risk_level === 'Medium').length;
  const safe = all.filter(e => e.risk_level === 'Low').length;

  $('statTotal').textContent = total;
  $('statHigh').textContent = high;
  $('statMedium').textContent = medium;
  $('statSafe').textContent = safe;

  // Animated risk distribution bar
  if (total > 0) {
    const bar = $('dashRiskBar');
    bar.style.display = 'flex';
    $('drbHigh').style.width = (high / total * 100).toFixed(1) + '%';
    $('drbMedium').style.width = (medium / total * 100).toFixed(1) + '%';
    $('drbLow').style.width = (safe / total * 100).toFixed(1) + '%';
  }
}

function updateBadges() {
  $('inboxBadge').textContent = inboxEmails.length;
}

/* ── STRIP HTML ───────────────────────────────────────────── */
function stripHtml(html) {
  const d = document.createElement('div');
  d.innerHTML = html;
  return (d.innerText || d.textContent || '').replace(/\s{3,}/g, '\n\n').trim();
}

/* ── HELPERS ──────────────────────────────────────────────── */
function $(id) { return document.getElementById(id); }

function showToast(msg, ms = 3000) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), ms);
}

function setProgress(pct) {
  const wrap = $('uploadProgress');
  const bar = $('progressBar');
  if (pct === null) { wrap.style.display = 'none'; return; }
  wrap.style.display = 'block';
  bar.style.width = pct + '%';
}

function riskClass(level) {
  return level === 'High' ? 'risk-high' : level === 'Medium' ? 'risk-medium' : 'risk-low';
}

function formatTime() {
  return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

/* ── FILE UPLOAD ──────────────────────────────────────────── */
function triggerUpload() { $('emlUpload').click(); }

async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  await uploadFile(file);
  event.target.value = '';
}

async function uploadFile(file) {
  if (!file.name.endsWith('.eml')) { showToast('Only .eml files supported'); return; }
  setProgress(30);
  showToast('Analyzing ' + file.name + '...');
  const fd = new FormData();
  fd.append('file', file);
  try {
    setProgress(60);
    const resp = await fetch('/upload', { method: 'POST', body: fd });
    setProgress(90);
    if (!resp.ok) { const e = await resp.json(); showToast(e.error || 'Upload failed'); setProgress(null); return; }
    const email = await resp.json();
    email.time = formatTime();
    email.filename = file.name;
    inboxEmails.unshift(email);
    renderEmailList();
    updateBadges(); updateDashStats();
    openEmail(email.id);
    showToast('Analysis complete — ' + email.risk_level + ' Risk');
    setProgress(null);
  } catch (e) {
    showToast('Could not reach server');
    setProgress(null);
  }
}

/* ── DRAG & DROP ──────────────────────────────────────────── */
document.addEventListener('dragover', e => { e.preventDefault(); $('dropOverlay').classList.add('active'); });
document.addEventListener('dragleave', e => { if (!e.relatedTarget) $('dropOverlay').classList.remove('active'); });
document.addEventListener('drop', e => {
  e.preventDefault();
  $('dropOverlay').classList.remove('active');
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

/* ── RENDER EMAIL LIST ────────────────────────────────────── */
function renderEmailList() {
  const list   = $('emailRowsList');   // JS-owned container — safe to clear
  const empty  = $('emptyState');
  const emails = inboxEmails;

  // Wipe the list cleanly — no shared nodes live here
  list.innerHTML = '';

  if (emails.length === 0) {
    empty.style.display = 'flex';
    return;
  }
  empty.style.display = 'none';

  emails.forEach(email => {
    const div = document.createElement('div');
    div.className = 'email-row unread' + (activeId === email.id ? ' selected' : '');
    div.id = 'row-' + email.id;
    div.onclick = () => openEmail(email.id);
    div.innerHTML = `
      <span class="row-risk-badge ${riskClass(email.risk_level)}">${email.risk_level}</span>
      <div class="row-content">
        <div class="row-sender">${escHtml(email.sender_name || email.sender_email)}</div>
        <div class="row-subject">${escHtml(email.subject)}</div>
        <div class="row-snippet">${escHtml(email.snippet || '')}</div>
      </div>
      <div class="row-time">${email.time || ''}</div>`;
    list.appendChild(div);
  });

  // Load-more button
  if (inboxNextPage) {
    const btn = document.createElement('button');
    btn.className = 'load-more-btn';
    btn.id = 'loadMoreBtn';
    btn.innerHTML = `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/></svg>
      Load next 100 emails`;
    btn.onclick = () => loadMoreInbox(btn);
    list.appendChild(btn);
  }
}



function loadMoreInbox(btn) {
  if (!inboxNextPage) return;
  if (btn) { btn.disabled = true; btn.textContent = 'Loading...'; }
  loadGmailInbox(inboxNextPage);
}

/* ── OPEN EMAIL ───────────────────────────────────────────── */
async function openEmail(id) {
  activeId = id;
  $('app').classList.add('email-open'); // mobile: switch to viewer panel
  document.querySelectorAll('.email-row').forEach(r => r.classList.remove('selected'));
  const row = $('row-' + id);
  if (row) row.classList.add('selected');

  let email = getEmails().find(e => e.id === id);
  try {
    const resp = await fetch('/emails/' + id);
    if (resp.ok) email = { ...email, ...(await resp.json()) };
  } catch (_) { }

  populateViewer(email);
  populatePanel(email);

  const idx = getEmails().findIndex(e => e.id === id);
  $('viewerCount').textContent = (idx + 1) + ' of ' + getEmails().length;
}

function populateViewer(e) {
  $('viewerSubject').textContent = e.subject || '(no subject)';

  const badge = $('viewerRiskBadge');
  badge.textContent = e.risk_level + ' Risk';
  badge.className = 'risk-badge-large ' + riskClass(e.risk_level);

  const initials = (e.sender_name || e.sender_email || '?').charAt(0).toUpperCase();
  $('senderAvatar').textContent = initials;
  $('senderNameBig').textContent = e.sender_name || e.sender_email;
  $('senderEmailTag').textContent = '<' + (e.sender_email || '') + '>';
  $('viewerTime').textContent = e.time || formatTime();

  const banner = $('warningBanner');
  if (e.risk_level === 'High' || e.risk_level === 'Medium') {
    banner.style.display = 'flex';
    $('warningText').textContent = e.risk_level === 'High'
      ? 'This email has been flagged as potentially dangerous. Do not click links or open attachments.'
      : 'This email shows suspicious signals. Proceed with caution.';
  } else {
    banner.style.display = 'none';
  }

  // Show plain text — strip any residual HTML
  const rawBody = e.body || e.email_text || '';
  const plainBody = rawBody.includes('<') ? stripHtml(rawBody) : rawBody;
  $('viewerBody').innerHTML = plainBody
    ? '<pre style="white-space:pre-wrap;font-family:inherit;font-size:14px;line-height:1.75">' + escHtml(plainBody) + '</pre>'
    : '<p style="color:#9aa0a6">No body content.</p>';
}

function populatePanel(e) {
  const card = $('riskCard');
  card.className = 'risk-card risk-' + e.risk_level.toLowerCase() + '-panel';

  $('riskLevelLabel').textContent = e.risk_level + ' Risk';
  $('riskScoreText').textContent = 'Risk Score: ' + e.risk_score + ' / ' + e.max_score;
  $('riskBarFill').style.width = e.risk_pct + '%';

  const list = $('reasonList');
  const reasons = e.reasons || [];
  if (!reasons.length) {
    list.innerHTML = '<p class="panel-placeholder">No suspicious signals detected.</p>';
  } else {
    list.innerHTML = reasons.map(r => {
      const meta = REASON_META[r] || { title: r, desc: '' };
      return `<div class="reason-item">
        <div class="reason-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg></div>
        <div><div class="reason-title">${meta.title}</div><div class="reason-desc">${meta.desc}</div></div>
      </div>`;
    }).join('');
  }

  const recSection = $('recommendations');
  const recList = $('recList');
  const recs = getRecommendations(e.risk_level);
  if (recs.length) {
    recSection.style.display = 'block';
    recList.innerHTML = recs.map(r => '<li>' + r + '</li>').join('');
  } else {
    recSection.style.display = 'none';
  }

  $('reportBtn').style.display = e.risk_level !== 'Low' ? 'flex' : 'none';
}

function getRecommendations(level) {
  if (level === 'High') return [
    'Do not click any links in this email.',
    'Do not open any attachments.',
    'Do not reply or share personal information.',
    'Report this to your IT / security team.',
  ];
  if (level === 'Medium') return [
    'Verify the sender through official channels.',
    'Hover over links before clicking.',
    'Do not enter credentials on linked pages.',
  ];
  return ['No major threats detected. Stay vigilant.'];
}

function closeViewer() {
  activeId = null;
  // Mobile: navigate back to email list
  $('app').classList.remove('email-open');
  document.querySelectorAll('.email-row').forEach(r => r.classList.remove('selected'));
  $('viewerSubject').textContent = '\u2014';
  $('viewerBody').innerHTML = '<p style="color:#9aa0a6;text-align:center;margin-top:60px">Select an email to view it here.</p>';
  $('viewerRiskBadge').textContent = '';
  $('senderNameBig').textContent = '\u2014';
  $('senderEmailTag').textContent = '\u2014';
  $('senderAvatar').textContent = '?';
  $('viewerTime').textContent = '\u2014';
  $('warningBanner').style.display = 'none';
  $('reasonList').innerHTML = '<p class="panel-placeholder">No email selected.</p>';
  $('riskCard').className = 'risk-card';
  $('riskLevelLabel').textContent = '\u2014';
  $('riskScoreText').textContent = 'Risk Score: \u2014';
  $('riskBarFill').style.width = '0%';
  $('recommendations').style.display = 'none';
  const rb = $('reportBtn');
  rb.style.display = 'none';
  rb.disabled = false;
  rb.style.background = '';
  rb.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"/></svg> Report as Phishing';
  $('viewerCount').textContent = '';
  $('phishyPanel').style.display = '';
  const reopen = $('reopenPanelBtn');
  if (reopen) reopen.style.display = 'none';
}

/* ── MOBILE SIDEBAR TOGGLE ────────────────────────────────── */
function toggleSidebar() {
  const sidebar  = $('sidebar');
  const overlay  = $('sidebarOverlay');
  const isOpen   = sidebar.classList.toggle('open');
  overlay.classList.toggle('show', isOpen);
}
function closeSidebar() {
  $('sidebar').classList.remove('open');
  $('sidebarOverlay').classList.remove('show');
}

/* ── PANEL-ONLY CLOSE (keeps email body visible) ─────────── */
function closePanel() {
  $('phishyPanel').style.display = 'none';
  const reopen = $('reopenPanelBtn');
  if (reopen) reopen.style.display = 'flex';
}

function openPanel() {
  $('phishyPanel').style.display = '';
  const reopen = $('reopenPanelBtn');
  if (reopen) reopen.style.display = 'none';
}

function reportPhishing() {
  showToast('Reported as phishing. Thank you!');
  const btn = $('reportBtn');
  btn.disabled = true;
  btn.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg> Reported';
  btn.style.background = 'var(--green)';
}

function scrollToPanel() {
  $('phishyPanel').scrollTop = 0;
  $('panelBody').scrollIntoView({ behavior: 'smooth' });
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/* ── REASON METADATA ──────────────────────────────────────── */
const REASON_META = {
  "URL detected in email": { title: "URL Detected", desc: "One or more URLs were found in the email body." },
  "Possible brand impersonation detected in URL": { title: "Brand Impersonation", desc: "A URL appears to impersonate a known brand domain." },
  "Suspicious domain detected": { title: "Suspicious Domain", desc: "The link domain uses suspicious keywords or TLDs." },
  "Sender identity and email domain do not match": { title: "Suspicious Sender", desc: "The sender name claims to be a brand but the email domain doesn't match." },
  "Reply-To address differs from sender": { title: "Reply-To Mismatch", desc: "Replies will go to a different address — a classic phishing trick." },
  "Return-Path differs from sender": { title: "Return-Path Mismatch", desc: "Bounces go to a different domain, suggesting the sender is spoofed." },
  "Suspicious subject line detected": { title: "Urgent Subject Line", desc: "The subject uses alarming language to provoke immediate action." },
  "Executable attachment detected": { title: "Dangerous Attachment", desc: "An attachment with an executable extension was found." },
  "Double extension attachment detected": { title: "Double Extension", desc: "Attachment disguises its true type using a double extension." },
  "Urgency tactic detected": { title: "Urgency Language", desc: "Uses urgent or threatening language to provoke immediate action." },
  "Identity verification request detected": { title: "Verification Request", desc: "Asks you to verify your identity — a common phishing hook." },
  "Account threat detected": { title: "Account Threat", desc: "Claims your account has been suspended or blocked." },
  "Password reset request detected": { title: "Password Reset", desc: "Requests a password reset — verify through the official site directly." },
  "Security scare tactic detected": { title: "Security Scare", desc: "Reports suspicious activity to create panic." },
  "Suspicious link request detected": { title: "Click-Here Link", desc: "Uses 'click here' — a common phishing phrase." },
  "Payment information request detected": { title: "Payment Request", desc: "Requests payment details or reports a failed payment." },
  "Prize scam language detected": { title: "Prize Scam", desc: "Claims you've won something to lure you into clicking." },
  "Address verification request detected": { title: "Address Request", desc: "Asks you to confirm your address — used for identity theft." },
  "Multiple URLs detected": { title: "Multiple URLs", desc: "Contains many links, increasing the attack surface." },
  "Raw IP address detected in URL": { title: "Raw IP URL", desc: "A URL uses a raw IP address instead of a domain — very suspicious." },
};

/* ── INIT ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Observe scroll sentinel
  const sentinel = $('scrollSentinel');
  if (sentinel) _sentinel.observe(sentinel);

  // Close modals on backdrop click
  ['guidelinesBackdrop', 'whyPhishyBackdrop'].forEach(id => {
    const el = $(id);
    if (el) el.addEventListener('click', e => { if (e.target === el) el.style.display = 'none'; });
  });
});

renderEmailList();
updateBadges();
setTimeout(checkGmailStatus, 500);
