# Bhargav's Advanced Selenium Automation Framework

A comprehensive, enterprise-grade Selenium automation framework created by **Bhargav** for end-to-end web application testing. This framework provides robust testing capabilities with advanced reporting, data-driven testing, and extensive test coverage.

## 🚀 Key Features

### Core Framework Features
- **🏗️ Page Object Model (POM)**: Clean, maintainable, and scalable test architecture
- **📊 Advanced Reporting**: ExtentReports with detailed HTML reports, screenshots, and analytics
- **📈 Data-Driven Testing**: Excel integration for comprehensive test data management
- **📧 Email Notifications**: Automated test report distribution via email
- **📸 Screenshot Capture**: Automatic failure screenshots with detailed error information
- **📝 Comprehensive Logging**: Log4j2 integration for detailed execution logs
- **⚡ TestNG Integration**: Advanced test execution, parallel testing, and reporting
- **🔒 Browser Management**: Automatic browser lifecycle management with proper cleanup
- **🎯 End-to-End Testing**: Complete user journey testing scenarios

### Testing Capabilities
- **🔐 Authentication Testing**: Login, logout, session management
- **👥 User Management**: User registration, profile management, security testing
- **🛍️ Product Management**: Product catalog, search, admin product management
- **📊 Data Validation**: Comprehensive data-driven test scenarios
- **🔄 Cross-Browser Testing**: Chrome, Firefox, Edge support (configurable)
- **📱 Responsive Testing**: Mobile and desktop viewport testing

## 📁 Framework Architecture

```
SeleniumAutomationFramework2025/
├── src/
│   ├── main/java/com/bhargav/automation/
│   │   ├── base/                    # Base test classes
│   │   │   └── BaseTest.java        # Main test base with setup/teardown
│   │   ├── pages/                   # Page Object Model classes
│   │   │   └── LoginPage.java       # Login page interactions
│   │   └── utils/                   # Utility classes
│   │       ├── ExtentReportManager.java  # Report management
│   │       ├── ExcelUtils.java           # Excel operations
│   │       ├── EmailUtils.java           # Email functionality
│   │       └── Log.java                  # Logging utilities
│   └── test/java/com/bhargav/automation/tests/
│       ├── LoginTest.java           # Login functionality tests
│       ├── UserManagementTest.java  # User management tests
│       └── ProductManagementTest.java # Product management tests
├── testdata/
│   └── TestData.xlsx               # Test data file
├── reports/                        # Generated test reports
├── screenshots/                    # Failure screenshots
├── logs/                          # Application logs
├── test-output/                   # TestNG reports
├── testng.xml                     # TestNG suite configuration
├── testng1.xml                    # End-to-end test suite
└── pom.xml                        # Maven configuration
```

## 🛠️ Prerequisites

### Required Software
- **Java**: JDK 8 or higher (JDK 11+ recommended)
- **Maven**: 3.6 or higher
- **Chrome Browser**: Latest version
- **IDE**: IntelliJ IDEA, Eclipse, or VS Code (optional)

### System Requirements
- **OS**: Windows 10/11, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 500MB free space
- **Internet**: Required for downloading dependencies and test execution

## 🚀 Quick Start Guide

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd SeleniumAutomationFramework2025

# Verify Java installation
java -version

# Verify Maven installation
mvn -version
```

### 2. Install Dependencies
```bash
# Clean and install all dependencies
mvn clean install

# Or just compile
mvn clean compile
```

### 3. Run Tests
```bash
# Run all tests
mvn test

# Run specific test suite
mvn test -DsuiteXmlFile=testng.xml

# Run end-to-end tests
mvn test -DsuiteXmlFile=testng1.xml
```

## 🧪 Test Execution Options

### Complete Test Suite Execution
```bash
# Run all test classes
mvn test

# Run with specific browser
mvn test -Dbrowser=chrome

# Run with parallel execution
mvn test -Dparallel=true
```

### Individual Test Execution
```bash
# Run only login tests
mvn test -Dtest=LoginTest

# Run user management tests
mvn test -Dtest=UserManagementTest

# Run product management tests
mvn test -Dtest=ProductManagementTest
```

### TestNG Suite Execution
```bash
# Run main test suite
mvn test -DsuiteXmlFile=testng.xml

# Run end-to-end suite
mvn test -DsuiteXmlFile=testng1.xml
```

## 📊 Test Coverage

### Login Functionality Tests
- ✅ **Valid Login Test**: Successful authentication with correct credentials
- ✅ **Invalid Password Test**: Authentication failure with wrong password
- ✅ **Invalid Username Test**: Authentication failure with wrong username
- ✅ **Empty Fields Test**: Validation of empty input fields
- ✅ **Data-Driven Login Test**: Multiple credential combinations
- ✅ **End-to-End User Journey**: Complete login workflow

### User Management Tests
- ✅ **User Registration Flow**: New user registration process
- ✅ **User Profile Management**: Profile update and management
- ✅ **Authentication Security**: Session management and security testing

### Product Management Tests
- ✅ **Product Catalog Navigation**: Product browsing and navigation
- ✅ **Product Search Functionality**: Search feature testing
- ✅ **Admin Product Management**: Product administration
- ✅ **Category Management**: Product category administration

## 📈 Reports and Analytics

### ExtentReports
- **Location**: `reports/ExtentReport_*.html`
- **Features**: 
  - Interactive HTML reports
  - Test execution timeline
  - Screenshot attachments
  - Pass/fail statistics
  - Detailed test steps

### TestNG Reports
- **Location**: `test-output/index.html`
- **Features**:
  - Test execution summary
  - Method-level results
  - Execution time analysis
  - Failure analysis

### Screenshots
- **Location**: `screenshots/`
- **Features**:
  - Automatic failure screenshots
  - Timestamped naming
  - High-resolution captures
  - Error context information

## ⚙️ Configuration

### Email Configuration
Update email settings in `EmailUtils.java`:
```java
final String senderEmail = "bhargav.automation@gmail.com";
final String appPassword = "your_app_password_here";
final String recipientEmail = "bhargav.automation@gmail.com";
```

### Test Data Configuration
Update `testdata/TestData.xlsx`:
- **Column A**: Username
- **Column B**: Password
- **Column C**: Test Description (optional)

### Browser Configuration
Modify browser settings in `BaseTest.java`:
```java
// For Chrome
driver = new ChromeDriver();

// For Firefox
// driver = new FirefoxDriver();

// For Edge
// driver = new EdgeDriver();
```

## 🔧 Framework Components

### Base Classes
- **`BaseTest`**: 
  - WebDriver initialization
  - Browser lifecycle management
  - Screenshot capture on failures
  - Report integration
  - Proper cleanup and teardown

### Page Objects
- **`LoginPage`**: 
  - Username/password input
  - Login button interaction
  - Form validation
  - Error handling

### Utility Classes
- **`ExtentReportManager`**: 
  - Report generation
  - Screenshot capture
  - Test step logging
  - Report configuration

- **`ExcelUtils`**: 
  - Excel file operations
  - Data reading/writing
  - Cell value extraction
  - File management

- **`EmailUtils`**: 
  - Email sending functionality
  - Report attachment
  - SMTP configuration
  - Error handling

- **`Log`**: 
  - Log4j2 integration
  - Multiple log levels
  - File and console logging
  - Error tracking

## 🎯 Best Practices

### Test Design
- **Page Object Model**: Maintains clean separation between test logic and page interactions
- **Data-Driven Testing**: Uses Excel files for test data management
- **Proper Assertions**: Comprehensive validation of expected outcomes
- **Error Handling**: Robust error handling and recovery mechanisms

### Code Quality
- **Clean Code**: Well-structured, readable, and maintainable code
- **Documentation**: Comprehensive inline documentation
- **Logging**: Detailed logging for debugging and monitoring
- **Exception Handling**: Proper exception handling throughout the framework

## 🚀 Advanced Features

### Parallel Execution
```bash
# Run tests in parallel
mvn test -Dparallel=true -DthreadCount=3
```

### Cross-Browser Testing
```bash
# Run with different browsers
mvn test -Dbrowser=chrome
mvn test -Dbrowser=firefox
mvn test -Dbrowser=edge
```

### CI/CD Integration
```bash
# For Jenkins/GitHub Actions
mvn clean test -DsuiteXmlFile=testng.xml
```

## 📞 Support and Maintenance

### Author Information
- **Name**: Bhargav
- **Email**: bhargav.automation@gmail.com
- **Framework Version**: 1.0.0
- **Last Updated**: 2025

### Maintenance
- Regular updates for browser compatibility
- Framework enhancements based on testing needs
- Bug fixes and performance optimizations
- Documentation updates

## 📄 License

This project is proprietary software created by **Bhargav** for automation testing purposes. All rights reserved.

---

**🎉 Ready to start testing!** This framework provides everything you need for comprehensive web application testing with professional-grade reporting and analysis capabilities.
