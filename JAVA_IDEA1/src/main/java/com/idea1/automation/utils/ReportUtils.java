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
                "  height: fit-content;\n" +
                "  position: sticky;\n" +
                "  top: 20px;\n" +
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
                "</style>\n" +
                "</head>\n" +
                "<body>\n" +
                "<div class=\"header\">\n" +
                "  <h1>Azure Automation Test Report</h1>\n" +
                "  <div id=\"timestamp\"></div>\n" +
                "</div>\n" +
                "<script>document.getElementById('timestamp').innerText = new Date().toLocaleString();</script>\n";
    }

    public static String getHtmlFailureBlock(String table, String check, Object expected, Object actual, String details) {
        return String.format("<div class='fail-block'>\n" +
                "  <b>Check:</b> %s<br>\n" +
                "  <b>Expected:</b> %s<br>\n" +
                "  <b>Actual:</b> %s<br>\n" +
                "  %s\n" +
                "</div>", check, expected, actual, details != null ? "<b>Details:</b> " + details : "");
    }
}
