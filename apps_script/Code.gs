/**
 * Karnataka Exams Daily: Drive -> GitHub ingestion.
 *
 * Reads finished editions (and audits) produced by the Gemini tasks and commits them to the repo.
 * Safe by design:
 *  - NEVER overwrites a file that already exists in the repo (so your review edits are never lost).
 *  - Only commits files whose names match YYYY-MM-DD_TOPICID or YYYY-MM-DD_TOPICID_audit.
 *  - Logs every action to the log sheet and emails you about problems.
 *
 * Script properties to set (Project Settings > Script properties):
 *   GITHUB_TOKEN        fine-grained token, Contents: read and write on this one repo only (YOU enter this)
 *   GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH (default main)
 *   EDITIONS_FOLDER_ID, AUDITS_FOLDER_ID, LOG_SHEET_ID, ALERT_EMAIL
 */
var TZ = 'Asia/Kolkata';
var EDITION_RE = /^(\d{4}-\d{2}-\d{2})_([A-Z]+-[0-9A-Za-z-]+)$/;
var AUDIT_RE = /^(\d{4}-\d{2}-\d{2})_([A-Z]+-[0-9A-Za-z-]+)_audit$/;

function cfg_() {
  var p = PropertiesService.getScriptProperties();
  var c = {
    token: p.getProperty('GITHUB_TOKEN'), owner: p.getProperty('GITHUB_OWNER'), repo: p.getProperty('GITHUB_REPO'),
    branch: p.getProperty('GITHUB_BRANCH') || 'main', editionsId: p.getProperty('EDITIONS_FOLDER_ID'),
    auditsId: p.getProperty('AUDITS_FOLDER_ID'), logId: p.getProperty('LOG_SHEET_ID'), email: p.getProperty('ALERT_EMAIL')
  };
  ['token', 'owner', 'repo', 'editionsId'].forEach(function (k) { if (!c[k]) throw new Error('Missing script property for ' + k); });
  return c;
}

function log_(c, name, kind, result, detail) {
  try {
    if (!c.logId) return;
    var sh = SpreadsheetApp.openById(c.logId).getSheets()[0];
    sh.appendRow([new Date(), name, kind, result, detail || '']);
  } catch (e) { console.error('log failed: ' + e); }
}

function alert_(c, subject, body) {
  if (c.email) MailApp.sendEmail(c.email, '[Exams Daily] ' + subject, body);
}

function gh_(c, method, path, payload) {
  var res = UrlFetchApp.fetch('https://api.github.com' + path, {
    method: method, muteHttpExceptions: true, contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + c.token, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' },
    payload: payload ? JSON.stringify(payload) : undefined
  });
  return { code: res.getResponseCode(), body: res.getContentText() };
}

function readText_(file) {
  var mt = file.getMimeType();
  var text;
  if (mt === 'application/vnd.google-apps.document') {
    // Export as markdown so headings, tables and lists written by Gemini keep their markers.
    var r = UrlFetchApp.fetch('https://www.googleapis.com/drive/v3/files/' + file.getId() + '/export?mimeType=text/markdown', {
      headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() }, muteHttpExceptions: true });
    text = r.getResponseCode() === 200 ? r.getContentText('UTF-8') : DocumentApp.openById(file.getId()).getBody().getText();
  } else text = file.getBlob().getDataAsString('UTF-8');
  return normalise_(text);
}

/** Undo what Google Docs does to markdown: escapes, bold in headings, trailing spaces, rule markers, shifted heading levels. */
function normalise_(text) {
  text = text.replace(/\r\n/g, '\n').replace(/^﻿/, '');
  text = text.replace(/\\([\\`*_{}\[\]()#+\-.!|<>~:])/g, '$1');
  text = text.split('\n').map(function (l) { return l.replace(/[ \t]+$/, ''); }).join('\n');
  text = text.replace(/^(#{1,6}) \*\*(.+?)\*\*$/gm, '$1 $2');
  text = text.replace(/^-{3,}$/gm, '---');
  // Docs drops or moves the closing rule and adds blank lines: rebuild the front matter block.
  var lines = text.trim().split('\n');
  if (lines[0] === '---') {
    var i = 1, keep = [];
    while (i < lines.length && (lines[i].trim() === '' || /^[a-z_]+:/.test(lines[i]))) { if (lines[i].trim()) keep.push(lines[i]); i++; }
    if (lines[i] === '---') i++;
    text = '---\n' + keep.join('\n') + '\n---\n\n' + lines.slice(i).join('\n');
  }
  var mm = text.match(/^(#{1,6}) .*ಇಂದಿನದ ವಿಷಯ/m);   // heading for the main lesson must be level 2
  if (mm && mm[1].length !== 2) {
    var shift = 2 - mm[1].length;
    text = text.replace(/^(#{1,6}) /gm, function (a, h) { return new Array(Math.max(1, Math.min(6, h.length + shift)) + 1).join('#') + ' '; });
  }
  text = text.trim();
  var m = text.match(/^\x60\x60\x60[a-zA-Z]*\n([\s\S]*)\n\x60\x60\x60$/);
  if (m) text = m[1].trim();
  return text + '\n';
}

function candidates_(c) {
  var seen = {}, out = [];
  function add(f) { if (!seen[f.getId()]) { seen[f.getId()] = 1; out.push(f); } }
  [c.editionsId, c.auditsId].forEach(function (id) {
    if (!id) return;
    var it = DriveApp.getFolderById(id).getFiles();
    while (it.hasNext()) add(it.next());
  });
  // Gemini sometimes saves to My Drive root: look for recent files with edition-like names.
  var since = Utilities.formatDate(new Date(Date.now() - 3 * 86400000), 'UTC', 'yyyy-MM-dd');
  var q = "trashed = false and modifiedDate > '" + since + "' and title contains '_' and (mimeType = 'application/vnd.google-apps.document' or mimeType = 'text/plain' or mimeType = 'text/markdown')";
  var it2 = DriveApp.searchFiles(q);
  while (it2.hasNext()) { var f = it2.next(); if (EDITION_RE.test(base_(f.getName())) || AUDIT_RE.test(base_(f.getName()))) add(f); }
  return out;
}

function base_(name) { return name.replace(/\.(md|txt)$/i, ''); }

function ingest() {
  var c = cfg_();
  var today = Utilities.formatDate(new Date(), TZ, 'yyyy-MM-dd');
  var haveToday = false;
  candidates_(c).forEach(function (f) {
    var name = base_(f.getName());
    var kind = EDITION_RE.test(name) ? 'edition' : (AUDIT_RE.test(name) ? 'audit' : null);
    if (!kind) return;
    if (kind === 'edition' && name.indexOf(today) === 0) haveToday = true;
    var path = 'content/' + (kind === 'edition' ? 'editions/' : 'audits/') + name + '.md';
    try {
      var text = readText_(f);
      if (text.length < 200 || text.indexOf('---') !== 0) { log_(c, name, kind, 'REJECTED', 'empty or no front matter'); alert_(c, 'Rejected ' + name, 'File is empty or has no front matter. Check the Gemini output.'); return; }
      var exists = gh_(c, 'get', '/repos/' + c.owner + '/' + c.repo + '/contents/' + path + '?ref=' + c.branch);
      if (exists.code === 200) { return; }               // never overwrite
      if (exists.code !== 404) { log_(c, name, kind, 'ERROR', 'GitHub ' + exists.code); alert_(c, 'GitHub error for ' + name, exists.body); return; }
      var put = gh_(c, 'put', '/repos/' + c.owner + '/' + c.repo + '/contents/' + path, {
        message: 'ingest: ' + name, branch: c.branch, content: Utilities.base64Encode(text, Utilities.Charset.UTF_8)
      });
      if (put.code === 201) { log_(c, name, kind, 'COMMITTED', path); }
      else { log_(c, name, kind, 'ERROR', 'PUT ' + put.code + ' ' + put.body.slice(0, 200)); alert_(c, 'Could not commit ' + name, put.body); }
    } catch (e) { log_(c, name, kind, 'ERROR', String(e)); alert_(c, 'Ingest error for ' + name, String(e)); }
  });
  if (!haveToday) {
    var chk = gh_(c, 'get', '/repos/' + c.owner + '/' + c.repo + '/contents/content/editions?ref=' + c.branch);
    var onGh = chk.code === 200 && chk.body.indexOf(today + '_') >= 0;
    if (!onGh) { log_(c, today, 'check', 'MISSING', 'no edition for today'); alert_(c, 'No edition for ' + today, 'The Gemini tasks produced no edition file for today. Check the scheduled tasks and the briefs folder.'); }
  }
}

/** Run once from the editor. Creates two daily triggers (05:00 and 06:00 IST) as a retry. */
function setupTriggers() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'ingest') ScriptApp.deleteTrigger(t); });
  [5, 6].forEach(function (h) { ScriptApp.newTrigger('ingest').timeBased().atHour(h).nearMinute(0).everyDays(1).inTimezone(TZ).create(); });
}

/** Run once after setting properties: checks the token and folder access without committing anything. */
function selfTest() {
  var c = cfg_();
  var r = gh_(c, 'get', '/repos/' + c.owner + '/' + c.repo);
  console.log('GitHub repo check: HTTP ' + r.code);
  console.log('Editions folder: ' + DriveApp.getFolderById(c.editionsId).getName());
  console.log('Candidate files: ' + candidates_(c).length);
}

/** Run once: stores the non-secret settings. Add GITHUB_TOKEN yourself in Project Settings > Script properties. */
function setProps() {
  PropertiesService.getScriptProperties().setProperties({
    GITHUB_OWNER: 'NaveenKoti',
    GITHUB_REPO: 'karnataka-exams-daily',
    GITHUB_BRANCH: 'main',
    EDITIONS_FOLDER_ID: '1Dg_ugQxciQNaii3eeOeOngt9gRD-9M7F',
    AUDITS_FOLDER_ID: '1qPetdUQ9N2_wBIyq6MvF70QCdrfg2kYv',
    LOG_SHEET_ID: '1jTkIyzYOojFhLGNdJtMkJk6zlJewUC35KCjosGKGM1g',
    ALERT_EMAIL: 'naveenkoti@gmail.com'
  });
}
