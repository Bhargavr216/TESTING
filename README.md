# ðŸš€ Test Automation Portfolio — End-to-End Testing Stories

## Repository Overview
This repo collects a dozen practical automation projects spanning web UI, API, database, and service-level validation. Each folder contains a dedicated README, but this overview pulls the high-level flow for every project so you can quickly understand what it solves and how it works end to end.

## Table of Contents
- [Project Overviews](#project-overviews)
  - [DemoProjectSelenium](#demoprojectselenium)
  - [Shops2-Website](#shops2-website)
  - [EcommerceWebsiteAutomation](#ecommercewebsiteautomation)
  - [Social-Media-Platform](#social-media-platform)
  - [idea1_project](#idea1_project)
  - [idea1_project_java](#idea1_project_java)
  - [IDEA_TWO/automation_platform](#idea_twoautomation_platform)
  - [JAVA_IDEA1](#java_idea1)
  - [OTF](#otf)
  - [SeleniumAutomationFramework2025](#seleniumautomationframework2025)
  - [supermarket](#supermarket)
- [Getting Started](#getting-started)
- [Learning Path](#learning-path)

## Project Overviews

### DemoProjectSelenium
`DemoProjectSelenium/` is a hands-on Selenium/TestNG framework. Maven bootstraps the dependencies, TestNG suites execute the basic programs, TestNG concepts, and advanced web-element packages, and listeners capture screenshots + reports in `test-output/`. Every run imitates a browser journey: open Chrome → interact with dropdowns, frames, and actions → assert page state → produce logs/snapshots.

### Shops2-Website
`shops2-website/` holds the static e-commerce landing page plus Selenium verification (`HomePageTests.java`). The site delivers responsive sections (hero, features, pricing) while the test suite runs via Maven to validate navigation links, filter behavior, and mobile/desktop breakpoints before reporting via TestNG.

### EcommerceWebsiteAutomation
`EcommerceWebsiteAutomation/` executes the full shopper lifecycle. The orchestrator launches Chrome, runs sequential helpers (login, filtering, add-to-cart, checkout, logout), validates session and totals, and writes logs that detail each business step.

### Social-Media-Platform
`Social-Media-Platform/` targets the REST API layer for a social app. Node.js scripts log in (JWT), follow/unfollow users, exercise post CRUD, and use Chai/Chai-HTTP to validate every response payload plus error scenarios before printing structured console summaries.

### idea1_project
`idea1_project/` validates event-driven persistence with Python. A runner loads payloads, resolves lookup keys, compares PostgreSQL rows to expected JSON using schema-driven rules, and produces an interactive HTML report showing passes/fails per table.

### idea1_project_java
`idea1_project_java/` provides the same schema-driven validation for JVM shops. Maven executes Java helpers that read payloads/schemas, query PostgreSQL, enforce semantic rules (nullable checks + retry expectations), and generate HTML reports with SQL context.

### IDEA_TWO/automation_platform
`IDEA_TWO/automation_platform/` is a rule-driven engine that spans FSM, MFS, and FOS services. Python reads scenario JSON, fires events, validates multiple tables per service, and outputs a collapsible HTML dashboard summarizing every validation detail.

### JAVA_IDEA1
`JAVA_IDEA1/` validates Azure Event Hub to database flows. Event payloads are sent to Event Hub, the automation waits for downstream processing, queries Azure SQL, and compares actual rows to expected data while generating HTML/PDF reports.

### OTF
`OTF/` uses Cucumber + Allure to validate event processing for MySQL. The generator builds feature files from payloads, step definitions trigger events, `JsonCompare` validates rows, and Allure visualizes the final results.

### SeleniumAutomationFramework2025
`SeleniumAutomationFramework2025/` is an enterprise Selenium/ExtentReports suite with Excel-driven data, email notifications, and rich logging. Base tests initialize browsers, page objects execute login/user/product flows, and reports + screenshots document each run.

### supermarket
`supermarket/` is a PHP/MySQL e-commerce app served via XAMPP. Users register/login, manage carts, place orders, and admins maintain products. The code relies on PHP sessions and PDO prepared statements, with schema.sql seeding the database for local testing.

## Getting Started
- **Prerequisites**: Java 17+, Maven 3.6+, Node.js 14+, Chrome browser, Python 3.10+, PostgreSQL/MySQL, XAMPP for the PHP demo.  
- **Quick start**:  
  ```bash
  git clone https://github.com/Bhargavr216/TESTING.git
  cd TESTING
  ```
- **Sample runs**:  
  - Selenium suites: `cd DemoProjectSelenium && mvn clean install && mvn test`  
  - API suite: `cd Social-Media-Platform && npm install && npm test`  
  - Python validation: `cd idea1_project && python -m venv venv && .\\venv\\Scripts\\Activate.ps1 && pip install -r requirements.txt && python runner.py`  
- **Documentation**: Each subfolder contains its own README for detailed setup, theory, and interview preparation.

## Learning Path
1. Start with the Selenium basics (`DemoProjectSelenium`) to understand WebDriver and TestNG.  
2. Explore targeted UI flows (`EcommerceWebsiteAutomation`, `Shops2-Website`, `SeleniumAutomationFramework2025`).  
3. Dive into API testing (`Social-Media-Platform`).  
4. Study database validation via schema-driven runners (`idea1_project`, `idea1_project_java`, `IDEA_TWO/automation_platform`, `OTF`, `JAVA_IDEA1`).  
5. Inspect the PHP stack example (`supermarket`) for full-stack behavior and prepared-statement security.
