# 🛒 EcommerceWebsiteAutomation - Complete E-commerce Testing Suite

## 📋 Project Overview

EcommerceWebsiteAutomation is a comprehensive test automation framework designed to validate the complete e-commerce user journey. Built with Java, Selenium WebDriver, and TestNG, this project demonstrates end-to-end testing of an e-commerce platform including login, product filtering, cart management, and checkout processes.

## 🎯 Key Features

- **Complete E-commerce Testing**: End-to-end user journey validation
- **Modular Architecture**: Page Object Model with separate classes for each functionality
- **Comprehensive Test Coverage**: Login, filtering, cart, checkout, and logout
- **Chrome WebDriver Integration**: Optimized browser automation
- **Detailed Logging**: Step-by-step test execution logging
- **Maven Build System**: Dependency management and test execution

## 🏗️ Project Structure

```
EcommerceWebsiteAutomation/
├── src/
│   ├── EcommerceWebsiteAutomation.java    # Main test orchestrator
│   ├── LoginPage.java                    # Login functionality
│   ├── ApplyFilter.java                   # Product filtering
│   ├── AddToCart.java                     # Cart management
│   ├── CheckoutPage.java                  # Checkout process
│   └── LogoutPage.java                    # Logout functionality
├── target/                               # Compiled classes
├── pom.xml                              # Maven configuration
└── README.md                            # Project documentation
```

## 🛠️ Technologies Used

- **Java 17**: Modern Java features and performance
- **Selenium WebDriver 4.13.0**: Latest web automation framework
- **TestNG 7.4.0**: Advanced testing framework
- **Maven**: Build automation and dependency management
- **Chrome WebDriver**: Primary browser for testing
- **ChromeOptions**: Browser configuration and optimization

## 🧪 Test Scenarios

### 1. **Login Functionality** (`TestCase01`)
```java
public static Boolean TestCase01(ChromeDriver driver) {
    LoginPage loginPage = new LoginPage(driver);
    loginPage.navigateToLoginPage();
    status = loginPage.PerformLogin("standard_user", "secret_sauce");
    return status;
}
```

**Features Tested:**
- User authentication
- Credential validation
- Login page navigation
- Session management

### 2. **Product Filtering** (`TestCase02`)
```java
public static Boolean TestCase02(ChromeDriver driver) {
    ApplyFilter filter = new ApplyFilter(driver);
    filter.navigateToHomePage();
    status = filter.PerformFilterAction();
    return status;
}
```

**Features Tested:**
- Product category filtering
- Price range filtering
- Brand filtering
- Sort functionality

### 3. **Add to Cart** (`TestCase03`)
```java
public static Boolean TestCase03(ChromeDriver driver) {
    AddToCart cart = new AddToCart(driver);
    cart.navigateToHomePage();
    status = cart.PerformAddToCartFunctionality("Sauce Labs Onesie");
    status = cart.PerformAddToCartFunctionality("Sauce Labs Fleece Jacket");
    return status;
}
```

**Features Tested:**
- Product selection
- Cart addition
- Multiple item handling
- Cart validation

### 4. **Checkout Process** (`TestCase04`)
```java
public static Boolean TestCase04(ChromeDriver driver) {
    CheckoutPage checkout = new CheckoutPage(driver);
    checkout.navigateToCartPage();
    status = checkout.PerformCheckoutFunctionality("Chanchal", "Korsewada", "492222");
    return status;
}
```

**Features Tested:**
- Customer information input
- Address validation
- Payment processing
- Order confirmation

### 5. **Logout Functionality** (`TestCase05`)
```java
public static Boolean TestCase05(ChromeDriver driver) {
    LogoutPage logoutPage = new LogoutPage(driver);
    logoutPage.navigateToLogoutPage();
    status = logoutPage.PerformLogout();
    return status;
}
```

**Features Tested:**
- Session termination
- Logout confirmation
- Return to login page

## 🚀 Getting Started

### Prerequisites
- Java 17 or higher
- Maven 3.6+
- Chrome browser installed
- ChromeDriver (automatically managed)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd EcommerceWebsiteAutomation
   ```

2. **Install dependencies**
   ```bash
   mvn clean install
   ```

3. **Run the complete test suite**
   ```bash
   mvn test
   ```

4. **Run individual test cases**
   ```bash
   # Run specific test case
   mvn test -Dtest=TestCase01
   ```

## 🔧 Configuration

### Chrome Options Setup
```java
ChromeOptions options = new ChromeOptions();
Map<String, Object> prefs = new HashMap<>();
prefs.put("credentials_enable_service", false);
prefs.put("profile.password_manager_enabled", false);
prefs.put("profile.password_manager_leak_detection", false);

options.setExperimentalOption("prefs", prefs);
options.setExperimentalOption("excludeSwitches", 
    new String[] { "enable-automation" });
options.addArguments("--disable‑infobars");
```

### Maven Configuration
```xml
<dependencies>
    <dependency>
        <groupId>org.seleniumhq.selenium</groupId>
        <artifactId>selenium-java</artifactId>
        <version>4.13.0</version>
    </dependency>
    <dependency>
        <groupId>org.testng</groupId>
        <artifactId>testng</artifactId>
        <version>7.4.0</version>
    </dependency>
</dependencies>
```

## 📊 Test Execution Flow

### Complete Test Suite Execution
```java
public static void main(String[] args) throws Exception {
    ChromeDriver driver = createDriver(options);
    
    // Execute all test cases in sequence
    status = TestCase01(driver);  // Login
    status = TestCase02(driver);  // Filter
    status = TestCase03(driver);  // Add to Cart
    status = TestCase04(driver);  // Checkout
    status = TestCase05(driver);  // Logout
    
    driver.quit();
}
```

### Individual Test Execution
```java
// Run specific test case
Boolean result = TestCase01(driver);
System.out.println("Login Test: " + (result ? "PASS" : "FAIL"));
```

## 📈 Logging and Reporting

### Detailed Logging
```java
public static void logStatus(String type, String message, String status) {
    System.out.println(String.format("%s | %s | %s | %s", 
        String.valueOf(java.time.LocalDateTime.now()), 
        type, message, status));
}
```

### Test Execution Logs
```
2024-01-15T10:30:00 | Start TestCase | Test Case 1: Verify Login functionality | DONE
2024-01-15T10:30:05 | TestCase 1 | Test Case Pass. Login functionality | PASS
2024-01-15T10:30:10 | Start TestCase | Test Case 2: Applying filter functionality | DONE
```

## 🎯 Page Object Model Implementation

### Login Page
```java
public class LoginPage {
    private ChromeDriver driver;
    
    public void navigateToLoginPage() {
        // Navigate to login page
    }
    
    public Boolean PerformLogin(String username, String password) {
        // Perform login operation
        // Return success/failure status
    }
}
```

### Cart Management
```java
public class AddToCart {
    private ChromeDriver driver;
    
    public void navigateToHomePage() {
        // Navigate to product listing
    }
    
    public Boolean PerformAddToCartFunctionality(String productName) {
        // Add specific product to cart
        // Return success/failure status
    }
}
```

## 🚨 Error Handling

### Test Failure Management
```java
if (!status) {
    logStatus("End TestCase", "Test Case Failed", "FAIL");
    return false;
} else {
    logStatus("TestCase", "Test Case Passed", "PASS");
    return true;
}
```

### Browser Configuration
- **Disable Automation Detection**: Avoid "Chrome is being controlled" banner
- **Disable Password Manager**: Prevent credential interference
- **Disable Info Bars**: Clean browser experience
- **Optimized Performance**: Faster test execution

## 📊 Test Data Management

### Test Credentials
```java
// Login credentials
String username = "standard_user";
String password = "secret_sauce";

// Checkout information
String firstName = "Chanchal";
String lastName = "Korsewada";
String postalCode = "492222";
```

### Product Data
```java
// Test products
String product1 = "Sauce Labs Onesie";
String product2 = "Sauce Labs Fleece Jacket";
```

## 🔄 Continuous Integration

### Maven Test Execution
```bash
# Run all tests
mvn clean test

# Run with specific profile
mvn test -Pchrome

# Run with parallel execution
mvn test -Dparallel=methods
```

### Test Reports
- **Console Output**: Real-time test execution logs
- **Maven Reports**: Test execution summaries
- **Screenshots**: Failure capture (if implemented)

## 🚀 Performance Optimization

### Browser Optimization
- **Headless Mode**: Faster execution (optional)
- **Disable Images**: Reduce load time
- **Disable JavaScript**: Faster page loads (if applicable)
- **Memory Management**: Proper driver cleanup

### Test Execution
- **Parallel Execution**: Multiple test cases simultaneously
- **Data-Driven Testing**: Parameterized test execution
- **Retry Logic**: Automatic retry on failures

## 📈 Future Enhancements

- [ ] **API Testing**: Backend service validation
- [ ] **Database Testing**: Data integrity verification
- [ ] **Performance Testing**: Load time validation
- [ ] **Cross-browser Testing**: Multi-browser support
- [ ] **Mobile Testing**: Responsive design validation
- [ ] **Visual Regression**: UI comparison testing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your test cases
4. Submit a pull request

## 📄 License

This project is for educational purposes and demonstrates comprehensive e-commerce testing automation.

## 👨‍💻 Author

**Bhargav Reddy** - Test Automation Engineer & Project Creator
- Comprehensive e-commerce testing framework
- End-to-end user journey validation
- Modern Java and Selenium implementation
- Created and developed this complete e-commerce testing solution

---

*This framework provides a complete solution for e-commerce testing, covering all critical user journeys from login to checkout completion.*
