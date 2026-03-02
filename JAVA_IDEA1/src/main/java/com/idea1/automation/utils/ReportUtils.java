package com.idea1.automation.utils;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class ReportUtils {

    public static String getHtmlHeader() {
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
                "  --warn: #797670;\n" +
                "  --warn-soft: #f3f2f1;\n" +
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
                ".filter-btn { background:transparent; border:1px solid var(--line); padding:6px 10px; border-radius:6px; cursor:pointer; color:white; opacity:0.9; transition:all 0.2s; }\n" +
                ".filter-btn.active { background:var(--panel); color:var(--accent); border-color:var(--panel); }\n" +
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
                    ".step-controls { display:flex; gap:8px; align-items:center; margin-bottom:8px; }\n" +
                    ".step-toggle { background:transparent; border:1px solid var(--line); padding:6px 10px; border-radius:6px; cursor:pointer; }\n" +
                    ".step-filters { display:flex; gap:6px; }\n" +
                    ".step-filter { background:transparent; border:1px solid var(--line); padding:6px 8px; border-radius:6px; cursor:pointer; font-size:12px; }\n" +
                    ".step-filter.active { background:var(--panel); color:var(--accent); border-color:var(--panel); }\n" +
                "}\n" +
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
                "</style>\n" +
                "</head>\n" +
                "<body>\n" +
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
                "<script>document.addEventListener('DOMContentLoaded', function(){ document.getElementById('timestamp').innerText = new Date().toLocaleString(); });</script>\n" +
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
