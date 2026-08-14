/* ── STATE ─────────────────────────────────────────────────── */
let emails      = [];   // all uploaded emails
let activeId    = null; // currently viewed email id
let emailCount  = 0;

/* ── REASON METADATA ────────────────────────────────────────── */
const REASON_META = {
  "URL detected in email":                       { title: "URL Detected",            desc: "One or more URLs were found in the email body." },
  "Possible brand impersonation detected in URL":{ title: "Brand Impersonation",     desc: "A URL appears to impersonate a known brand domain." },
  "Suspicious domain detected":                  { title: "Suspicious Domain",        desc: "The link domain uses suspicious keywords or TLDs." },
  "Sender identity and email domain do not match":{ title: "Suspicious Sender",       desc: "The sender name claims to be a brand but the email domain doesn't match." },
  "Reply-To address differs from sender":        { title: "Reply-To Mismatch",        desc: "Replies will go to a different address than the sender — a classic phishing trick." },
  "Return-Path differs from sender":             { title: "Return-Path Mismatch",     desc: "Bounces go to a different domain, suggesting the sender is spoofed." },
  "Suspicious subject line detected":            { title: "Urgent Subject Line",      desc: "The subject uses alarming language to provoke immediate action." },
  "Executable attachment detected":              { title: "Dangerous Attachment",     desc: "An attachment with an executable extension (.exe, .bat, etc.) was found." },
  "Double extension attachment detected":        { title: "Double Extension",         desc: "Attachment disguises its true type using a double extension (e.g. invoice.pdf.exe)." },
  "Urgency tactic detected":                     { title: "Urgency Language",         desc: "Uses urgent or threatening language to provoke immediate action." },
  "Identity verification request detected":      { title: "Verification Request",     desc: "Asks you to verify your identity or account — a common phishing hook." },
  "Account threat detected":                     { title: "Account Threat",           desc: "Claims your account has been suspended or blocked." },
  "Password reset request detected":             { title: "Password Reset",           desc: "Requests a password reset — verify through the official site directly." },
  "Security scare tactic detected":              { title: "Security Scare",           desc: "Reports suspicious activity to create panic." },
  "Suspicious link request detected":            { title: "Click-Here Link",          desc: "Uses 'click here' — a common phishing phrase." },
  "Payment information request detected":        { title: "Payment Request",          desc: "Requests payment details or reports a failed payment." },
  "Prize scam language detected":                { title: "Prize Scam",               desc: "Claims you've won something to lure you into clicking." },
  "Address verification request detected":       { title: "Address Request",          desc: "Asks you to confirm your address — used for identity theft." },
  "Multiple URLs detected":                      { title: "Multiple URLs",            desc: "Contains many links, increasing the attack surface." },
  "Raw IP address detected in URL":              { title: "Raw IP URL",               desc: "A URL uses a raw IP address instead of a domain — very suspicious." },
};

const ICON_SVG = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>`;

/* ── HELPERS ────────────────────────────────────────────────── */
function $(id) { return document.getElementById(id); }

function showToast(msg, duration = 3000) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration);
}

function setProgress(pct) {
  const bar = $('progressBar');
  const wrap = $('uploadProgress');
  if (pct === null) { wrap.style.display = 'none'; return; }
  wrap.style.display = 'block';
  bar.style.width = pct + '%';
}

function riskClass(level) {
  return level === 'High' ? 'risk-high' : level === 'Medium' ? 'risk-medium' : 'risk-low';
}

function formatTime() {
  const now = new Date();
  return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

/* ── FILE UPLOAD ────────────────────────────────────────────── */
function triggerUpload() {
  $('emlUpload').click();
}

async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  await uploadFile(file);
  event.target.value = ''; // reset so same file can be re-uploaded
}

async function uploadFile(file) {
  if (!file.name.endsWith('.eml')) {
    showToast('⚠ Only .eml files are supported');
    return;
  }

  setProgress(30);
  showToast(`📨 Analyzing ${file.name}…`);

  const formData = new FormData();
  formData.append('file', file);

  try {
    setProgress(60);
    const resp = await fetch('/upload', { method: 'POST', body: formData });
    setProgress(90);

    if (!resp.ok) {
      const err = await resp.json();
      showToast('❌ ' + (err.error || 'Upload failed'));
      setProgress(null);
      return;
    }

    const email = await resp.json();
    email.time = formatTime();
    email.filename = file.name;

    emails.unshift(email);
    emailCount++;
    renderEmailList();
    updateBadge();
    openEmail(email.id);
    showToast(`✅ Analysis complete — ${email.risk_level} Risk`);
    setProgress(null);

  } catch (e) {
    showToast('❌ Could not reach server');
    setProgress(null);
  }
}

/* ── DRAG & DROP ────────────────────────────────────────────── */
const rows = $('emailRows');
const overlay = $('dropOverlay');

document.addEventListener('dragover', e => { e.preventDefault(); overlay.classList.add('active'); });
document.addEventListener('dragleave', e => { if (!e.relatedTarget) overlay.classList.remove('active'); });
document.addEventListener('drop', e => {
  e.preventDefault();
  overlay.classList.remove('active');
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

/* ── RENDER EMAIL LIST ──────────────────────────────────────── */
function renderEmailList() {
  const container = $('emailRows');
  const empty = $('emptyState');
  const dropZone = $('dropOverlay');

  if (emails.length === 0) {
    empty.style.display = 'flex';
    container.innerHTML = '';
    container.appendChild(empty);
    container.appendChild(dropZone);
    return;
  }

  empty.style.display = 'none';

  // Rebuild rows
  container.innerHTML = '';
  container.appendChild(dropZone);

  emails.forEach(email => {
    const div = document.createElement('div');
    div.className = `email-row unread ${activeId === email.id ? 'selected' : ''}`;
    div.id = 'row-' + email.id;
    div.onclick = () => openEmail(email.id);

    div.innerHTML = `
      <div class="row-check"><input type="checkbox" class="checkbox" onclick="e=>e.stopPropagation()"/></div>
      <span class="row-risk-badge ${riskClass(email.risk_level)}">${email.risk_level}</span>
      <div class="row-content">
        <div class="row-sender">${escHtml(email.sender_name || email.sender_email)}</div>
        <div class="row-subject-line">
          <span class="row-subject">${escHtml(email.subject)}</span>
        </div>
        <div class="row-snippet">${escHtml(email.snippet || '')}</div>
      </div>
      <div class="row-time">${email.time || ''}</div>
    `;
    container.appendChild(div);
  });
}

function updateBadge() {
  $('inboxBadge').textContent = emails.length;
}

/* ── OPEN EMAIL ─────────────────────────────────────────────── */
async function openEmail(id) {
  activeId = id;

  // Highlight row
  document.querySelectorAll('.email-row').forEach(r => r.classList.remove('selected'));
  const row = $('row-' + id);
  if (row) row.classList.add('selected');

  // Fetch full email from server
  let email = emails.find(e => e.id === id);

  try {
    const resp = await fetch(`/emails/${id}`);
    if (resp.ok) {
      const full = await resp.json();
      email = { ...email, ...full };
    }
  } catch(_) {}

  populateViewer(email);
  populatePanel(email);
}

function populateViewer(e) {
  // Subject
  $('viewerSubject').textContent = e.subject || '(no subject)';

  // Risk badge
  const badge = $('viewerRiskBadge');
  badge.textContent = e.risk_level + ' Risk';
  badge.className = 'risk-badge-large ' + riskClass(e.risk_level);

  // Sender
  const initials = (e.sender_name || e.sender_email || '?').charAt(0).toUpperCase();
  $('senderAvatar').textContent = initials;
  $('senderNameBig').textContent = e.sender_name || e.sender_email;
  $('senderEmailTag').textContent = '<' + (e.sender_email || '') + '>';
  $('viewerTime').textContent = e.time || formatTime();

  // Warning banner
  const banner = $('warningBanner');
  if (e.risk_level === 'High' || e.risk_level === 'Medium') {
    banner.style.display = 'flex';
    $('warningText').textContent =
      e.risk_level === 'High'
        ? 'This email has been flagged as potentially dangerous. Be careful with links and attachments.'
        : 'This email shows some suspicious signals. Proceed with caution.';
  } else {
    banner.style.display = 'none';
  }

  // Body
  const body = $('viewerBody');
  const rawBody = e.body || e.email_text || '';
  body.innerHTML = rawBody
    ? '<pre style="white-space:pre-wrap;font-family:inherit;font-size:14px;line-height:1.7">' + escHtml(rawBody) + '</pre>'
    : '<p style="color:#9aa0a6">No body content.</p>';

  // Viewer count
  const idx = emails.findIndex(em => em.id === activeId);
  $('viewerCount').textContent = `${idx + 1} of ${emails.length}`;

  // Show reply bar
  $('replyBar').style.display = 'flex';
}

function populatePanel(e) {
  // Risk card colours
  const card = $('riskCard');
  card.className = 'risk-card risk-' + e.risk_level.toLowerCase() + '-panel';

  $('riskLevelLabel').textContent = e.risk_level + ' Risk';
  $('riskScoreText').textContent  = `Risk Score: ${e.risk_score} / ${e.max_score}`;
  $('riskBarFill').style.width    = e.risk_pct + '%';

  // Reasons
  const list = $('reasonList');
  const reasons = e.reasons || [];

  if (!reasons.length) {
    list.innerHTML = '<p class="panel-placeholder">No suspicious signals detected.</p>';
  } else {
    list.innerHTML = reasons.map(r => {
      const meta = REASON_META[r] || { title: r, desc: '' };
      return `
        <div class="reason-item">
          <div class="reason-icon">${ICON_SVG}</div>
          <div>
            <div class="reason-title">${meta.title}</div>
            <div class="reason-desc">${meta.desc}</div>
          </div>
        </div>`;
    }).join('');
  }

  // Recommendations
  const recSection = $('recommendations');
  const recList    = $('recList');
  const recs = getRecommendations(e.risk_level);
  if (recs.length) {
    recSection.style.display = 'block';
    recList.innerHTML = recs.map(r => `<li>${r}</li>`).join('');
  } else {
    recSection.style.display = 'none';
  }

  // Report button
  $('reportBtn').style.display = e.risk_level !== 'Low' ? 'flex' : 'none';
}

function getRecommendations(level) {
  if (level === 'High') return [
    'Do not click on any links.',
    'Do not share any personal information.',
    'Do not open any attachments.',
    'Report this email to your admin.',
  ];
  if (level === 'Medium') return [
    'Verify the sender through official channels.',
    'Hover over links before clicking.',
    'Do not enter credentials on linked pages.',
  ];
  return ['No major threats detected. Stay vigilant.'];
}

/* ── CLOSE VIEWER ───────────────────────────────────────────── */
function closeViewer() {
  activeId = null;
  document.querySelectorAll('.email-row').forEach(r => r.classList.remove('selected'));
  $('viewerSubject').textContent = '—';
  $('viewerBody').innerHTML = '<p style="color:#9aa0a6;text-align:center;margin-top:60px">Select an email from the list to view it here.</p>';
  $('viewerRiskBadge').textContent = '';
  $('senderNameBig').textContent = '—';
  $('senderEmailTag').textContent = '—';
  $('warningBanner').style.display = 'none';
  $('replyBar').style.display = 'none';
  $('reasonList').innerHTML = '<p class="panel-placeholder">No email selected.</p>';
  $('riskCard').className = 'risk-card';
  $('riskLevelLabel').textContent = '—';
  $('riskScoreText').textContent = 'Risk Score: —';
  $('riskBarFill').style.width = '0%';
  $('recommendations').style.display = 'none';
  $('reportBtn').style.display = 'none';
}

/* ── REPORT PHISHING ────────────────────────────────────────── */
function reportPhishing() {
  showToast('🚩 Reported as phishing. Thank you!');
  $('reportBtn').disabled = true;
  $('reportBtn').textContent = '✓ Reported';
}

/* ── SCROLL PANEL ───────────────────────────────────────────── */
function scrollToPanel() {
  $('phishyPanel').scrollTop = 0;
  $('panelBody').scrollIntoView({ behavior: 'smooth' });
}

/* ── ESCAPE HTML ────────────────────────────────────────────── */
function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

/* ── INIT ───────────────────────────────────────────────────── */
renderEmailList();
updateBadge();
