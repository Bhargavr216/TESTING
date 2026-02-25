# 🚀 DemoProjectSelenium - Comprehensive Selenium WebDriver Testing Framework

## 📋 Project Overview

This is a comprehensive Selenium WebDriver testing framework built with Java, TestNG, and Maven. The project demonstrates various web automation techniques, from basic browser operations to advanced UI interactions, making it an excellent learning resource for test automation engineers.

## 🎯 Key Features

- **Comprehensive Test Coverage**: 30+ test classes covering different aspects of web automation
- **Modern Tech Stack**: Java 17, Selenium 4.27.0, TestNG 7.10.2, Maven
- **Advanced Web Interactions**: Handles dropdowns, checkboxes, radio buttons, frames, alerts, and more
- **Mouse Operations**: Drag & drop, hover, slider interactions
- **TestNG Integration**: Grouping, dependencies, parameterized tests
- **Screenshot Capabilities**: Automated screenshot capture for test failures
- **Cross-browser Support**: Chrome WebDriver with configurable options

## 🏗️ Project Structure

```
DemoProjectSelenium/
├── src/test/java/
│   ├── basicPrograms/           # Fundamental Selenium concepts
│   │   ├── FirstPrograms.java   # Basic browser operations
│   │   ├── DemoXpath.java      # XPath locator strategies
│   │   └── VerifyTitleAndURL.java # Page validation
│   ├── basicTestngConcept/      # TestNG framework basics
│   │   ├── A1.java, A2.java, A3.java # Test execution order
│   │   ├── DependsOnMethod.java # Test dependencies
│   │   └── GroupingDemo.java    # Test grouping
│   ├── handlingVariousWebElements/ # Web element interactions
│   │   ├── HandlingDropdowns.java
│   │   ├── HandlingCheckbox.java
│   │   ├── HandlingRadioButton.java
│   │   └── HandlingFrames.java
│   ├── mouseRelated_And_OtherOperations/ # Advanced interactions
│   │   ├── DragAndDrop.java
│   │   ├── MouseHoverDemo.java
│   │   └── SliderDemo.java
│   ├── practiceWithTestng/     # Advanced TestNG features
│   │   ├── CapturingScreenshot.java
│   │   ├── HandlingNewTab.java
│   │   └── VerifyLogin.java
│   └── other/                  # Utility functions
│       ├── AlertDemo.java
│       └── ScrollDownPage.java
├── test-output/               # Test execution reports
├── pom.xml                   # Maven configuration
└── testng.xml               # TestNG suite configuration
```

## 🛠️ Technologies Used

- **Java 17**: Modern Java features and performance improvements
- **Selenium WebDriver 4.27.0**: Latest Selenium for web automation
- **TestNG 7.10.2**: Advanced testing framework with reporting
- **Maven**: Dependency management and build automation
- **Chrome WebDriver**: Primary browser for testing
- **Commons IO**: File operations and utilities

## 🚀 Getting Started

### Prerequisites

- Java 17 or higher
- Maven 3.6+
- Chrome browser installed
- ChromeDriver (automatically managed by WebDriverManager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DemoProjectSelenium
   ```

2. **Install dependencies**
   ```bash
   mvn clean install
   ```

3. **Run tests**
   ```bash
   # Run all tests
   mvn test
   
   # Run specific test groups
   mvn test -Dgroups="smoke"
   
   # Run with specific browser
   mvn test -Dbrowser=chrome
   ```

## 📊 Test Categories

### 🔧 Basic Programs
- **Browser Operations**: Launch, navigate, maximize, close
- **Element Location**: ID, class, XPath, CSS selectors
- **Page Validation**: Title verification, URL checking

### 🧪 TestNG Concepts
- **Test Execution Order**: Priority-based execution
- **Dependencies**: Test method dependencies
- **Grouping**: Logical test grouping
- **Parameters**: Data-driven testing

### 🎛️ Web Element Handling
- **Form Elements**: Text inputs, dropdowns, checkboxes
- **Interactive Elements**: Radio buttons, sliders, frames
- **Navigation**: Links, buttons, tabs

### 🖱️ Advanced Interactions
- **Mouse Operations**: Hover, drag & drop, click actions
- **Keyboard Operations**: Text input, special keys
- **Window Management**: Multiple windows, tabs

### 📸 Reporting & Utilities
- **Screenshot Capture**: Automatic failure screenshots
- **Test Reports**: HTML and XML reports
- **Logging**: Comprehensive test logging

## 🎯 Key Test Scenarios

### 1. **Basic Browser Operations**
```java
// Launch browser and navigate
WebDriver driver = new ChromeDriver();
driver.get("https://example.com");
driver.manage().window().maximize();
```

### 2. **Element Interactions**
```java
// Handle dropdowns
Select dropdown = new Select(driver.findElement(By.id("dropdown")));
dropdown.selectByVisibleText("Option 1");
```

### 3. **Mouse Operations**
```java
// Drag and drop
Actions actions = new Actions(driver);
actions.dragAndDrop(source, target).perform();
```

### 4. **TestNG Features**
```java
@Test(priority = 1, groups = "smoke")
@BeforeMethod
@AfterMethod
```

## 📈 Test Execution

### Running Individual Test Classes
```bash
# Run specific test class
mvn test -Dtest=FirstPrograms

# Run test groups
mvn test -Dgroups="smoke,regression"

# Run with parallel execution
mvn test -Dparallel=methods -DthreadCount=4
```

### TestNG XML Configuration
```xml
<suite name="DemoProjectSelenium Suite">
    <test name="Basic Tests">
        <classes>
            <class name="basicPrograms.FirstPrograms"/>
        </classes>
    </test>
</suite>
```

## 📊 Test Reports

The project generates comprehensive test reports in the `test-output/` directory:

- **HTML Reports**: Visual test execution results
- **XML Reports**: Machine-readable test results
- **Screenshots**: Automatic capture on test failures
- **Logs**: Detailed execution logs

## 🔧 Configuration

### Chrome Options
```java
ChromeOptions options = new ChromeOptions();
options.addArguments("--disable-notifications");
options.addArguments("--disable-popup-blocking");
```

### TestNG Configuration
- **Parallel Execution**: Methods and classes
- **Data Providers**: Parameterized testing
- **Listeners**: Custom test listeners
- **Groups**: Test categorization

## 🚨 Common Issues & Solutions

### 1. **ChromeDriver Issues**
```bash
# Update ChromeDriver
mvn clean install -U
```

### 2. **Element Not Found**
- Check element locators
- Add explicit waits
- Verify page load completion

### 3. **Test Failures**
- Check browser compatibility
- Verify test data
- Review test logs

## 📚 Learning Path

1. **Start with Basic Programs**: Understand fundamental concepts
2. **Explore TestNG Features**: Learn test framework capabilities
3. **Practice Web Elements**: Master element interactions
4. **Advanced Operations**: Mouse, keyboard, window management
5. **Reporting & Utilities**: Screenshots, logging, reports

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your test cases
4. Submit a pull request

## 📄 License

This project is for educational purposes and demonstrates best practices in Selenium WebDriver automation.

## 👨‍💻 Author

**Bhargav Reddy** - Test Automation Engineer & Project Creator
- Comprehensive Selenium WebDriver framework
- Modern Java and TestNG implementation
- Production-ready test automation patterns
- Created and developed this complete testing framework

---

*This framework serves as a comprehensive learning resource for Selenium WebDriver automation, covering everything from basic browser operations to advanced testing scenarios.*