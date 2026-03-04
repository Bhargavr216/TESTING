package com.idea1.automation.utils;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class ReportUtils {

    public static String getHtmlHeader(String jiraBaseUrl, String jiraProjectKey) {
        return "<html>\n" +
                "<head>\n" +
                "<meta charset=\"UTF-8\">\n" +
                "<title>Azure Automation Test Report</title>\n" +
                "<style>\n" +
                ":root {\n" +
                "  --bg: #f3f7fb;\n" +
                "  --panel: #ffffff;\n" +
                "  --panel-soft: #f8fbff;\n" +
                "  --line: #d9e4f1;\n" +
                "  --text: #1f2a37;\n" +
                "  --warn: #797670;\n" +
                "  --muted: #5b6b80;\n" +
                "  --accent: #0078d4;\n" +
                "  --accent-soft: #eef7ff;\n" +
                "  --ok: #107c10;\n" +
                "  --ok-soft: #dff6dd;\n" +
                "  --err: #a4262c;\n" +
                "  --err-soft: #fed9cc;\n" +
                "}\n" +
                "* { box-sizing: border-box; }\n" +
                "html { scroll-behavior: smooth; }\n" +
                "body {\n" +
                "  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\n" +
                "  background-color: var(--bg);\n" +
                "  margin: 0;\n" +
                "  color: var(--text);\n" +
                "}\n" +
                ".header {\n" +
                "  background-color: var(--accent);\n" +
                "  color: white;\n" +
                "  padding: 20px 40px;\n" +
                "  display: flex;\n" +
                "  justify-content: space-between;\n" +
                "  align-items: center;\n" +
                "  box-shadow: 0 2px 4px rgba(0,0,0,0.1);\n" +
                "}\n" +
                ".header h1 { margin: 0; font-size: 24px; }\n" +
                ".filters { display:flex; gap:8px; align-items:center; }\n" +
                ".filter-btn { background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.3); padding:8px 16px; border-radius:8px; cursor:pointer; color:white; font-weight:600; transition:all 0.2s; }\n" +
                ".filter-btn:hover { background:rgba(255,255,255,0.25); }\n" +
                ".filter-btn.active { background:white; color:var(--accent); border-color:white; box-shadow:0 2px 8px rgba(0,0,0,0.2); }\n" +
                ".summary-cards {\n" +
                "  display: grid;\n" +
                "  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));\n" +
                "  gap: 20px;\n" +
                "  padding: 20px 40px;\n" +
                "}\n" +
                ".card {\n" +
                "  background: var(--panel);\n" +
                "  padding: 20px;\n" +
                "  border-radius: 8px;\n" +
                "  box-shadow: 0 2px 8px rgba(0,0,0,0.05);\n" +
                "  border-left: 5px solid var(--accent);\n" +
                "}\n" +
                ".step-controls { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; background:var(--panel-soft); padding:10px; border-radius:10px; border:1px solid var(--line); }\n" +
                ".step-toggle { background:var(--accent); color:white; border:none; padding:8px 16px; border-radius:8px; cursor:pointer; font-weight:600; transition:all 0.2s; }\n" +
                ".step-toggle:hover { background:var(--accent); opacity:0.9; transform:translateY(-1px); }\n" +
                ".step-filters { display:flex; gap:6px; background:white; padding:4px; border-radius:8px; border:1px solid var(--line); }\n" +
                ".step-filter { background:transparent; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; font-size:12px; font-weight:700; color:var(--muted); transition:all 0.2s; }\n" +
                ".step-filter:hover { background:var(--accent-soft); color:var(--accent); }\n" +
                ".step-filter.active { background:var(--accent); color:white; }\n" +
                ".card.pass { border-left-color: var(--ok); }\n" +
                ".card.fail { border-left-color: var(--err); }\n" +
                ".card h3 { margin: 0 0 10px 0; color: var(--muted); font-size: 14px; text-transform: uppercase; }\n" +
                ".card .value { font-size: 28px; font-weight: bold; }\n" +
                ".layout { display: grid; grid-template-columns: 300px 1fr; gap: 20px; padding: 0 40px 40px 40px; }\n" +
                ".sidebar {\n" +
                "  background: var(--panel);\n" +
                "  padding: 20px;\n" +
                "  border-radius: 8px;\n" +
                "  box-shadow: 0 2px 8px rgba(0,0,0,0.05);\n" +
                "  position: sticky;\n" +
                "  top: 20px;\n" +
                "  max-height: calc(100vh - 160px);\n" +
                "  overflow-y: auto;\n" +
                "}\n" +
                ".case-link {\n" +
                "  display: block;\n" +
                "  padding: 10px 15px;\n" +
                "  margin-bottom: 5px;\n" +
                "  border-radius: 4px;\n" +
                "  text-decoration: none;\n" +
                "  color: var(--text);\n" +
                "  transition: background 0.2s;\n" +
                "  font-size: 14px;\n" +
                "}\n" +
                ".case-link:hover { background: var(--accent-soft); }\n" +
                ".case-link.fail { color: var(--err); font-weight: bold; }\n" +
                ".case-link.pass { color: var(--ok); }\n" +
                ".case {\n" +
                "  background: var(--panel);\n" +
                "  margin-bottom: 20px;\n" +
                "  border-radius: 8px;\n" +
                "  box-shadow: 0 2px 8px rgba(0,0,0,0.05);\n" +
                "  overflow: hidden;\n" +
                "}\n" +
                ".case summary {\n" +
                "  padding: 15px 20px;\n" +
                "  cursor: pointer;\n" +
                "  background: var(--panel-soft);\n" +
                "  display: flex;\n" +
                "  justify-content: space-between;\n" +
                "  align-items: center;\n" +
                "  border-bottom: 1px solid var(--line);\n" +
                "}\n" +
                ".case-id { font-weight: bold; color: var(--accent); }\n" +
                ".case-title { flex-grow: 1; margin-left: 20px; font-weight: 600; }\n" +
                ".case-body { padding: 20px; }\n" +
                ".step {\n" +
                "  margin-bottom: 15px;\n" +
                "  padding: 10px 15px;\n" +
                "  border-radius: 6px;\n" +
                "  background: #fdfdfd;\n" +
                "  border: 1px solid var(--line);\n" +
                "}\n" +
                ".step-title { font-weight: bold; margin-bottom: 5px; color: var(--muted); font-size: 13px; }\n" +
                ".box {\n" +
                "  border: 1px solid var(--line);\n" +
                "  border-radius: 6px;\n" +
                "  margin-bottom: 15px;\n" +
                "  overflow: hidden;\n" +
                "}\n" +
                ".box h3 {\n" +
                "  margin: 0;\n" +
                "  padding: 10px 15px;\n" +
                "  background: var(--accent-soft);\n" +
                "  font-size: 15px;\n" +
                "  border-bottom: 1px solid var(--line);\n" +
                "}\n" +
                ".box-content { padding: 15px; }\n" +
                ".pass { color: var(--ok); }\n" +
                ".fail { color: var(--err); }\n" +
                ".fail-block {\n" +
                "  background: var(--err-soft);\n" +
                "  padding: 10px;\n" +
                "  border-radius: 4px;\n" +
                "  margin-top: 10px;\n" +
                "  font-family: monospace;\n" +
                "  font-size: 13px;\n" +
                "}\n" +
                ".fail-table { width:100%; border-collapse: collapse; margin-top:8px; }\n" +
                ".fail-table th, .fail-table td { border:1px solid var(--line); padding:8px; text-align:left; font-size:13px; }\n" +
                ".fail-table th { background: var(--panel-soft); font-weight:600; }\n" +
                ".validation-table { width:100%; border-collapse: collapse; margin:15px 0; }\n" +
                ".validation-table th { background:linear-gradient(135deg, var(--accent-soft) 0%, var(--panel-soft) 100%); padding:12px; border:1px solid var(--line); font-weight:600; text-align:left; color:var(--accent); }\n" +
                ".validation-table td { padding:10px 12px; border:1px solid var(--line); font-size:13px; }\n" +
                ".validation-table tr:nth-child(even) { background:var(--panel-soft); }\n" +
                ".validation-table tr:hover { background:var(--accent-soft); }\n" +
                ".validation-table .pass { color:var(--ok); font-weight:600; }\n" +
                ".validation-table .fail { color:var(--err); font-weight:600; }\n" +
                ".validation-table .skip { color:var(--warn); font-weight:600; }\n" +
                ".btn-jira { background: var(--err); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 10px; transition: all 0.2s; }\n" +
                ".btn-jira:hover { opacity: 0.9; transform: translateY(-1px); }\n" +
                ".modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }\n" +
                ".modal-content { background: white; margin: 15% auto; padding: 25px; border-radius: 12px; width: 400px; box-shadow: 0 5px 20px rgba(0,0,0,0.2); }\n" +
                ".modal-header { font-size: 18px; font-weight: bold; margin-bottom: 20px; color: var(--text); }\n" +
                ".severity-opts { display: flex; flex-direction: column; gap: 10px; }\n" +
                ".sev-btn { padding: 12px; border: 1px solid var(--line); border-radius: 8px; cursor: pointer; text-align: left; background: white; transition: all 0.2s; font-weight: 500; }\n" +
                ".sev-btn:hover { background: var(--accent-soft); border-color: var(--accent); }\n" +
                ".sev-extreme { border-left: 5px solid var(--err); }\n" +
                ".sev-high { border-left: 5px solid #e67e22; }\n" +
                ".sev-medium { border-left: 5px solid #f1c40f; }\n" +
                "</style>\n" +
                "</head>\n" +
                "<body>\n" +
                "<div id=\"jiraModal\" class=\"modal\">\n" +
                "  <div class=\"modal-content\">\n" +
                "    <div class=\"modal-header\">Select Severity for Defect</div>\n" +
                "    <div class=\"severity-opts\">\n" +
                "      <button class=\"sev-btn sev-extreme\" onclick=\"submitJira('Extreme')\">Extreme (Blocker)</button>\n" +
                "      <button class=\"sev-btn sev-high\" onclick=\"submitJira('High')\">High (Critical)</button>\n" +
                "      <button class=\"sev-btn sev-medium\" onclick=\"submitJira('Medium')\">Medium (Major)</button>\n" +
                "      <button class=\"sev-btn\" style=\"margin-top:10px; text-align:center; background:#eee;\" onclick=\"closeModal()\">Cancel</button>\n" +
                "    </div>\n" +
                "  </div>\n" +
                "</div>\n" +
                "<div class=\"header\">\n" +
                "  <h1>Azure Automation Test Report</h1>\n" +
                "  <div class=\"filters\">\n" +
                "    <button class=\"filter-btn active\" data-filter=\"all\">All</button>\n" +
                "    <button class=\"filter-btn\" data-filter=\"pass\">Passed</button>\n" +
                "    <button class=\"filter-btn\" data-filter=\"fail\">Failed</button>\n" +
                "    <button class=\"filter-btn\" data-filter=\"skip\">Skipped</button>\n" +
                "  </div>\n" +
                "  <div id=\"timestamp\"></div>\n" +
                "</div>\n" +
                "<script>\n" +
                "  var currentDefect = {};\n" +
                "  var JIRA_BASE_URL = '" + jiraBaseUrl + "';\n" +
                "  var JIRA_PROJECT = '" + jiraProjectKey + "';\n" +
                "  \n" +
                "  function raiseJiraDefect(caseId, title, details){\n" +
                "    currentDefect = { id: caseId, title: title, details: details };\n" +
                "    document.getElementById('jiraModal').style.display = 'block';\n" +
                "  }\n" +
                "  \n" +
                "  function closeModal(){ document.getElementById('jiraModal').style.display = 'none'; }\n" +
                "  \n" +
                "  function submitJira(severity){\n" +
                "    var summary = encodeURIComponent('[Automation] ' + currentDefect.title + ' (' + currentDefect.id + ')');\n" +
                "    var description = encodeURIComponent('Scenario: ' + currentDefect.title + '\\n' + \n" +
                "                                       'Case ID: ' + currentDefect.id + '\\n' + \n" +
                "                                       'Severity: ' + severity + '\\n\\n' + \n" +
                "                                       'Failure Details:\\n' + currentDefect.details);\n" +
                "    \n" +
                "    var url = JIRA_BASE_URL + '/secure/CreateIssueDetails!init.jspa?project=' + JIRA_PROJECT + \n" +
                "              '&issuetype=1&summary=' + summary + '&description=' + description + '&priority=' + severity;\n" +
                "    \n" +
                "    window.open(url, '_blank');\n" +
                "    closeModal();\n" +
                "  }\n" +
                "  \n" +
                "  document.addEventListener('DOMContentLoaded', function(){ \n" +
                "    document.getElementById('timestamp').innerText = new Date().toLocaleString(); \n" +
                "  });\n" +
                "</script>\n" +
                "<script>\n" +
                "document.addEventListener('DOMContentLoaded', function(){\n" +
                "  function buildSidebar(){\n" +
                "    var sidebar = document.querySelector('.sidebar'); if(!sidebar) return; sidebar.innerHTML = '<h3>Test Scenarios</h3>';\n" +
                "    var cases = document.querySelectorAll('.case');\n" +
                "    cases.forEach(function(c){ if(c.style.display==='none') return; var id = c.id.replace('case-',''); var titleEl = c.querySelector('.case-title'); var title = titleEl ? titleEl.innerText : id; var statusEl = c.querySelector('.status'); var status = 'pass'; if(statusEl){ if(statusEl.classList.contains('fail')) status='fail'; else if(statusEl.classList.contains('pass')) status='pass'; else status='skip'; } var a = document.createElement('a'); a.className = 'case-link ' + status; a.id = 'link-' + id; a.href = '#case-' + id; a.innerText = title + ' ('+id+')'; a.addEventListener('click', function(e){ e.preventDefault(); var d = document.getElementById('case-' + id); if(d) d.open = true; d.scrollIntoView({behavior:'smooth', block:'start'}); }); sidebar.appendChild(a); });\n" +
                "  }\n" +
                "  function applyFilter(filter){\n" +
                "    document.querySelectorAll('.case').forEach(function(c){ var statusEl = c.querySelector('.status'); var status = 'pass'; if(statusEl){ if(statusEl.classList.contains('fail')) status='fail'; else if(statusEl.classList.contains('pass')) status='pass'; else status='skip'; } c.style.display = (filter==='all' || filter===status) ? '' : 'none'; });\n" +
                "    document.querySelectorAll('.filter-btn').forEach(function(b){ b.classList.toggle('active', b.getAttribute('data-filter')===filter); });\n" +
                "    buildSidebar();\n" +
                "  }\n" +
                "  document.querySelectorAll('.filter-btn').forEach(function(b){ b.addEventListener('click', function(){ applyFilter(b.getAttribute('data-filter')); }); });\n" +
                "\n" +
                "  // Step-level controls: toggle and per-step filters\n" +
                "  document.addEventListener('click', function(e){\n" +
                "    try {\n" +
                "      if(e.target && e.target.classList && e.target.classList.contains('step-toggle')){\n" +
                "        var target = e.target.getAttribute('data-target');\n" +
                "        var el = document.getElementById(target);\n" +
                "        if(el) el.style.display = (el.style.display==='none' || el.style.display==='') ? 'block' : 'none';\n" +
                "        e.preventDefault();\n" +
                "      }\n" +
                "      if(e.target && e.target.classList && e.target.classList.contains('step-filter')){\n" +
                "        var target = e.target.getAttribute('data-target');\n" +
                "        var filter = e.target.getAttribute('data-filter');\n" +
                "        var parent = e.target.parentElement;\n" +
                "        if(parent){ parent.querySelectorAll('.step-filter').forEach(function(b){ b.classList.toggle('active', b===e.target); }); }\n" +
                "        applyStepFilter(target, filter);\n" +
                "        e.preventDefault();\n" +
                "      }\n" +
                "    } catch(err) { console.error(err); }\n" +
                "  });\n" +
                "\n" +
                "  function applyStepFilter(containerId, filter){\n" +
                "    var container = document.getElementById(containerId);\n" +
                "    if(!container) return;\n" +
                "    container.querySelectorAll('table.validation-table tbody tr').forEach(function(tr){\n" +
                "      var lastTd = tr.querySelector('td:last-child');\n" +
                "      var cls = lastTd ? lastTd.className : '';\n" +
                "      var status = 'pass';\n" +
                "      if(cls.indexOf('fail')!==-1) status='fail'; else if(cls.indexOf('skip')!==-1) status='skip';\n" +
                "      tr.style.display = (filter==='all' || filter===status) ? '' : 'none';\n" +
                "    });\n" +
                "  }\n" +
                "\n" +
                "  buildSidebar();\n" +
                "});\n" +
                "</script>\n";
    }

    public static String getHtmlFailureBlock(String table, String check, Object expected, Object actual, String details) {
        String exp = expected == null ? "null" : expected.toString();
        String act = actual == null ? "null" : actual.toString();
        boolean pass = exp.equals(act);
        String result = pass ? "PASS" : "FAIL";
        String resultClass = pass ? "pass" : "fail";
        String detailsHtml = details != null && !details.isEmpty() ? "<tr><td colspan='4'><b>Details:</b> " + details + "</td></tr>" : "";
        return String.format("<table class='fail-table'>" +
                "<tr><th>Field</th><th>Expected</th><th>Actual</th><th>Result</th></tr>" +
                "<tr><td>%s</td><td>%s</td><td>%s</td><td class='%s'>%s</td></tr>" +
                "%s</table>", check, exp, act, resultClass, result, detailsHtml);
    }
}