package com.idea1.automation.utils;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class ReportUtils {

    public static String getHtmlHeader() {
        return "<html>\n" +
                "<head>\n" +
                "<meta charset=\"UTF-8\">\n" +
                "<title>Idea 1 Automation Report</title>\n" +
                "<style>\n" +
                ":root {\n" +
                "  --bg: #f3f7fb;\n" +
                "  --panel: #ffffff;\n" +
                "  --panel-soft: #f8fbff;\n" +
                "  --line: #d9e4f1;\n" +
                "  --text: #1f2a37;\n" +
                "  --muted: #5b6b80;\n" +
                "  --accent: #0f5cab;\n" +
                "  --accent-soft: #e7f1ff;\n" +
                "  --ok: #0f7a43;\n" +
                "  --ok-soft: #ddf7e8;\n" +
                "  --warn: #9a6600;\n" +
                "  --warn-soft: #fff4d6;\n" +
                "  --err: #b12235;\n" +
                "  --err-soft: #ffe6ea;\n" +
                "}\n" +
                "* { box-sizing: border-box; }\n" +
                "html { scroll-behavior: smooth; }\n" +
                "body {\n" +
                "  font-family: \"Manrope\", \"Segoe UI\", Arial, sans-serif;\n" +
                "  background:\n" +
                "    radial-gradient(circle at 5% 5%, #e8f1ff 0%, transparent 32%),\n" +
                "    radial-gradient(circle at 95% 0%, #f0f7ff 0%, transparent 28%),\n" +
                "    var(--bg);\n" +
                "  margin: 0;\n" +
                "  color: var(--text);\n" +
                "}\n" +
                "h1 { margin: 0; color: #0f1a2b; font-size: 22px; letter-spacing: 0.2px; }\n" +
                ".topbar {\n" +
                "  position: sticky;\n" +
                "  top: 0;\n" +
                "  z-index: 100;\n" +
                "  background: rgba(255, 255, 255, 0.92);\n" +
                "  backdrop-filter: blur(6px);\n" +
                "  border-bottom: 1px solid var(--line);\n" +
                "  padding: 14px 20px;\n" +
                "  display: flex;\n" +
                "  align-items: center;\n" +
                "  justify-content: space-between;\n" +
                "}\n" +
                ".toolbar { display: flex; gap: 8px; }\n" +
                ".toolbar button {\n" +
                "  border: 1px solid var(--line);\n" +
                "  background: linear-gradient(180deg, #ffffff 0%, #f6faff 100%);\n" +
                "  color: #0f2842;\n" +
                "  border-radius: 10px;\n" +
                "  padding: 7px 12px;\n" +
                "  font-weight: 700;\n" +
                "  cursor: pointer;\n" +
                "  transition: all 0.18s ease;\n" +
                "}\n" +
                ".toolbar button:hover {\n" +
                "  transform: translateY(-1px);\n" +
                "  box-shadow: 0 6px 14px rgba(15, 92, 171, 0.12);\n" +
                "  border-color: #bcd3ec;\n" +
                "}\n" +
                ".layout { display: grid; grid-template-columns: 260px 1fr; gap: 16px; padding: 16px; }\n" +
                ".sidebar {\n" +
                "  background: var(--panel);\n" +
                "  border: 1px solid var(--line);\n" +
                "  border-radius: 14px;\n" +
                "  padding: 12px;\n" +
                "  height: calc(100vh - 110px);\n" +
                "  position: sticky;\n" +
                "  top: 82px;\n" +
                "  overflow: auto;\n" +
                "  box-shadow: 0 10px 24px rgba(16, 38, 68, 0.07);\n" +
                "}\n" +
                ".sidebar h3 {\n" +
                "  margin: 0 0 12px 0;\n" +
                "  font-size: 12px;\n" +
                "  text-transform: uppercase;\n" +
                "  letter-spacing: 0.7px;\n" +
                "  color: var(--muted);\n" +
                "}\n" +
                ".case-link {\n" +
                "  display: block;\n" +
                "  text-decoration: none;\n" +
                "  color: #0f2842;\n" +
                "  background: var(--panel-soft);\n" +
                "  border: 1px solid var(--line);\n" +
                "  border-radius: 10px;\n" +
                "  padding: 9px 10px;\n" +
                "  margin-bottom: 8px;\n" +
                "  font-size: 13px;\n" +
                "  font-weight: 600;\n" +
                "  transition: all 0.15s ease;\n" +
                "}\n" +
                ".case-link:hover {\n" +
                "  background: #eef5ff;\n" +
                "  border-color: #bfd5ef;\n" +
                "  transform: translateX(2px);\n" +
                "}\n" +
                ".content { min-width: 0; }\n" +
                ".case {\n" +
                "  background: var(--panel);\n" +
                "  border: 1px solid var(--line);\n" +
                "  border-radius: 14px;\n" +
                "  margin-bottom: 16px;\n" +
                "  box-shadow: 0 10px 28px rgba(18, 40, 70, 0.08);\n" +
                "  overflow: hidden;\n" +
                "}\n" +
                ".case summary {\n" +
                "  list-style: none;\n" +
                "  cursor: pointer;\n" +
                "  padding: 14px 16px;\n" +
                "  background: linear-gradient(180deg, #fcfeff 0%, #f4f8fd 100%);\n" +
                "  border-bottom: 1px solid var(--line);\n" +
                "  display: flex;\n" +
                "  gap: 12px;\n" +
                "  align-items: center;\n" +
                "  flex-wrap: wrap;\n" +
                "}\n" +
                ".case summary::-webkit-details-marker { display:none; }\n" +
                ".case-id {\n" +
                "  font-weight: 800;\n" +
                "  color: #0f2842;\n" +
                "  background: #e2edf9;\n" +
                "  border: 1px solid #c8dbee;\n" +
                "  border-radius: 999px;\n" +
                "  padding: 4px 10px;\n" +
                "  font-size: 12px;\n" +
                "}\n" +
                ".case-title { font-weight: 700; color: #0f1f34; }\n" +
                ".case-meta { color: var(--muted); font-size: 13px; }\n" +
                ".case-body { padding: 14px 16px 16px 16px; }\n" +
                ".case-overview {\n" +
                "  background: linear-gradient(180deg, #f8fbff 0%, #f3f8ff 100%);\n" +
                "  border: 1px solid var(--line);\n" +
                "  border-radius: 12px;\n" +
                "  padding: 10px 12px;\n" +
                "  margin-bottom: 12px;\n" +
                "}\n" +
                ".case-overview p { margin: 4px 0; }\n" +
                ".box {\n" +
                "  background: var(--panel);\n" +
                "  border: 1px solid var(--line);\n" +
                "  padding: 12px;\n" +
                "  margin-bottom: 12px;\n" +
                "  border-radius: 12px;\n" +
                "}\n" +
                ".box h3 {\n" +
                "  margin: 0 0 8px 0;\n" +
                "  color: #0f1f34;\n" +
                "  font-size: 15px;\n" +
                "}\n" +
                ".pass {\n" +
                "  color: var(--ok);\n" +
                "  font-weight: 600;\n" +
                "  background: var(--ok-soft);\n" +
                "  border: 1px solid #b9ebcd;\n" +
                "  padding: 8px 10px;\n" +
                "  border-radius: 8px;\n" +
                "}\n" +
                ".fail {\n" +
                "  color: var(--err);\n" +
                "  font-weight: 600;\n" +
                "}\n" +
                ".fail pre {\n" +
                "  margin: 0 0 8px 0;\n" +
                "  background: linear-gradient(180deg, #fff7f8 0%, #fff0f3 100%);\n" +
                "  border: 1px solid #ffc7d0;\n" +
                "  padding: 10px;\n" +
                "  border-radius: 10px;\n" +
                "  white-space: pre-wrap;\n" +
                "  line-height: 1.35;\n" +
                "  font-weight: 500;\n" +
                "}\n" +
                "h2, h3 { color: #0f1f34; margin-top: 0; }\n" +
                ".case-footer {\n" +
                "  border-top: 1px dashed var(--line);\n" +
                "  margin-top: 10px;\n" +
                "  padding-top: 10px;\n" +
                "  display: flex;\n" +
                "  gap: 8px;\n" +
                "  align-items: center;\n" +
                "  flex-wrap: wrap;\n" +
                "}\n" +
                ".chip {\n" +
                "  border-radius: 999px;\n" +
                "  padding: 4px 10px;\n" +
                "  font-size: 12px;\n" +
                "  font-weight: 800;\n" +
                "  border: 1px solid transparent;\n" +
                "}\n" +
                ".chip-pass { background: var(--ok-soft); color: var(--ok); border-color: #b9ebcd; }\n" +
                ".chip-fail { background: var(--err-soft); color: var(--err); border-color: #ffcad2; }\n" +
                ".chip-skip { background: var(--warn-soft); color: var(--warn); border-color: #f2d99a; }\n" +
                "@media (max-width: 960px) {\n" +
                "  .layout { grid-template-columns:1fr; }\n" +
                "  .sidebar { position:relative; top:0; height:auto; }\n" +
                "}\n" +
                "</style>\n" +
                "<script>\n" +
                "function expandAllCases() {\n" +
                "  document.querySelectorAll('details.case').forEach(function(el) { el.open = true; });\n" +
                "}\n" +
                "function collapseAllCases() {\n" +
                "  document.querySelectorAll('details.case').forEach(function(el) { el.open = false; });\n" +
                "}\n" +
                "</script>\n" +
                "</head>\n" +
                "<body>\n" +
                "<div class=\"topbar\">\n" +
                "  <h1>Idea 1 Automation Execution Report</h1>\n" +
                "  <div class=\"toolbar\">\n" +
                "    <button type=\"button\" onclick=\"expandAllCases()\">Expand All</button>\n" +
                "    <button type=\"button\" onclick=\"collapseAllCases()\">Collapse All</button>\n" +
                "  </div>\n" +
                "</div>\n";
    }

    public static String getHtmlFooter() {
        return "</main></div></body></html>";
    }

    public static String getHtmlFailureBlock(String table, String column, Object expected, Object actual, String path) {
        StringBuilder sb = new StringBuilder();
        sb.append("<div class='fail'><pre>");
        sb.append("Table   : ").append(table).append("\n");
        sb.append("Column  : ").append(column).append("\n");
        if (path != null && !path.isEmpty()) {
            sb.append("Path    : ").append(path).append("\n");
        }
        if (expected != null) {
            sb.append("Expected: ").append(expected).append("\n");
        }
        if (actual != null) {
            sb.append("Actual  : ").append(actual).append("\n");
        }
        sb.append("</pre></div>");
        return sb.toString();
    }

    public static void saveReport(String htmlContent) throws IOException {
        File dir = new File("reports");
        if (!dir.exists()) {
            dir.mkdirs();
        }
        try (FileWriter writer = new FileWriter("reports/idea1_report.html")) {
            writer.write(htmlContent);
        }
    }
}
