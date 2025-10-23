# 🛍️ Shops2-Website - Modern E-commerce Landing Page with Selenium Testing

## 📋 Project Overview

Shops2-Website is a modern, responsive e-commerce landing page built with HTML5, CSS3, and JavaScript, featuring a sleek design with animated elements and comprehensive Selenium WebDriver test automation. The project demonstrates both frontend development skills and test automation expertise.

## 🎯 Key Features

### 🌐 Frontend Features
- **Responsive Design**: Mobile-first approach with CSS Grid and Flexbox
- **Modern UI/UX**: Clean, professional design with smooth animations
- **Interactive Elements**: Dynamic navigation, pricing filters, and hover effects
- **Asset Management**: Optimized images, SVGs, and icons
- **Cross-browser Compatibility**: Works on all modern browsers

### 🧪 Testing Features
- **Comprehensive Test Suite**: Automated testing with Selenium WebDriver
- **Page Object Model**: Maintainable test structure
- **TestNG Integration**: Advanced test framework features
- **Cross-browser Testing**: Chrome WebDriver support
- **Screenshot Capabilities**: Visual regression testing

## 🏗️ Project Structure

```
shops2-website/
├── assets/                    # Static assets
│   ├── *.png                  # Product images
│   ├── *.svg                  # Icons and logos
│   └── *.jpg                  # Background images
├── src/test/java/            # Test automation
│   └── HomePageTests.java     # Main test class
├── index.html                 # Main HTML page
├── style.css                 # CSS styles
├── pom.xml                   # Maven configuration
└── README.md                 # Project documentation
```

## 🛠️ Technologies Used

### Frontend
- **HTML5**: Semantic markup and modern features
- **CSS3**: Advanced styling with animations and transitions
- **JavaScript**: Interactive functionality and DOM manipulation
- **AOS (Animate On Scroll)**: Scroll-triggered animations
- **jQuery**: DOM manipulation and event handling
- **Boxicons**: Icon library for UI elements

### Testing
- **Selenium WebDriver**: Web automation framework
- **TestNG**: Testing framework with reporting
- **Maven**: Build automation and dependency management
- **WebDriverManager**: Automatic driver management

## 🎨 Design Features

### 🎯 Landing Page Sections
1. **Hero Section**: Eye-catching header with call-to-action
2. **About Section**: Company information and branding
3. **Features Section**: Key product features with icons
4. **Pricing Section**: Dynamic pricing with filter functionality
5. **Footer**: Contact information and links

### 🎨 Visual Elements
- **Gradient Backgrounds**: Modern gradient color schemes
- **Smooth Animations**: CSS transitions and AOS animations
- **Responsive Grid**: CSS Grid and Flexbox layouts
- **Interactive Buttons**: Hover effects and state changes
- **Professional Typography**: Clean, readable fonts

## 🧪 Test Automation

### Test Coverage
```java
@Test(priority = 1)
public void testNavigateToAboutSection() {
    // Navigate to About section and verify header
}

@Test(priority = 2)
public void testDiscordButtonOpensCorrectUrl() {
    // Verify Discord button opens correct external link
}

@Test(priority = 3)
public void testPricingFilterGroup1ShowsCorrect() {
    // Test pricing filter functionality
}
```

### Test Scenarios
1. **Navigation Testing**: Verify all navigation links work correctly
2. **External Link Testing**: Ensure Discord button opens correct URL
3. **Filter Functionality**: Test pricing filter interactions
4. **Responsive Testing**: Verify mobile and desktop layouts
5. **Cross-browser Testing**: Ensure compatibility across browsers

## 🚀 Getting Started

### Prerequisites
- Java 17 or higher
- Maven 3.6+
- Chrome browser
- Node.js (for development server)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd shops2-website
   ```

2. **Install dependencies**
   ```bash
   mvn clean install
   ```

3. **Run the website locally**
   ```bash
   # Using Python (if available)
   python -m http.server 8000
   
   # Using Node.js
   npx serve .
   ```

4. **Run tests**
   ```bash
   mvn test
   ```

## 🎯 Key Components

### HTML Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sowwyz</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <!-- Navigation menu -->
        </nav>
    </header>
    
    <section class="home" id="home">
        <!-- Hero section -->
    </section>
    
    <section class="about" id="about">
        <!-- About section -->
    </section>
    
    <section class="features" id="features">
        <!-- Features section -->
    </section>
    
    <section class="pricing" id="pricing">
        <!-- Pricing section -->
    </section>
</body>
</html>
```

### CSS Features
```css
/* Responsive design */
@media (max-width: 768px) {
    .navbar {
        flex-direction: column;
    }
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* Grid layouts */
.features-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}
```

### JavaScript Functionality
```javascript
// Mobile menu toggle
const burger = document.getElementById('burger');
const links = document.getElementById('links');

burger.addEventListener('click', () => {
    links.classList.toggle('active');
});

// Scroll effects
$(window).scroll(function () {
    if ($(window).scrollTop()) {
        $("header").addClass("black");
    } else {
        $("header").removeClass("black");
    }
});
```

## 🧪 Test Implementation

### Page Object Model
```java
public class HomePage {
    private WebDriver driver;
    
    public HomePage(WebDriver driver) {
        this.driver = driver;
    }
    
    public void clickAboutNavLink() {
        driver.findElement(By.linkText("About")).click();
    }
    
    public String getAboutHeaderText() {
        return driver.findElement(By.tagName("h1")).getText();
    }
}
```

### Test Configuration
```java
@BeforeMethod
public void setupTest() {
    driver = new ChromeDriver();
    driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
    driver.manage().window().maximize();
    driver.get("/index.html");
    homePage = new HomePage(driver);
}
```

## 📊 Performance Features

### 🚀 Optimization
- **Minified Assets**: Compressed CSS and JavaScript
- **Image Optimization**: WebP format support
- **Lazy Loading**: Images load as needed
- **CDN Integration**: External library loading

### 📱 Responsive Design
- **Mobile-first**: Optimized for mobile devices
- **Breakpoints**: Tablet and desktop layouts
- **Touch-friendly**: Mobile navigation and interactions
- **Cross-device**: Consistent experience across devices

## 🎨 Design System

### Colors
- **Primary**: Modern gradient schemes
- **Secondary**: Complementary colors
- **Accent**: Highlight colors for CTAs
- **Neutral**: Text and background colors

### Typography
- **Headings**: Bold, impactful fonts
- **Body**: Readable, clean fonts
- **Links**: Interactive, hover states
- **Buttons**: Clear, actionable text

## 🚀 Deployment

### Static Hosting
```bash
# Build for production
npm run build

# Deploy to GitHub Pages
git push origin gh-pages

# Deploy to Netlify
netlify deploy --prod
```

### Testing in CI/CD
```yaml
# GitHub Actions example
- name: Run Selenium Tests
  run: mvn test
```

## 🔧 Configuration

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

## 📈 Future Enhancements

- [ ] **E2E Testing**: Complete user journey testing
- [ ] **Performance Testing**: Load time optimization
- [ ] **Accessibility Testing**: WCAG compliance
- [ ] **Visual Regression**: Screenshot comparison
- [ ] **API Testing**: Backend integration testing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Submit a pull request

## 📄 License

This project is for educational purposes and demonstrates modern web development and test automation practices.

## 👨‍💻 Author

**Bhargav Reddy** - Full Stack Developer & Test Automation Engineer
- Modern web development with HTML5, CSS3, JavaScript
- Comprehensive Selenium WebDriver testing
- Responsive design and user experience
- Created and developed this complete web application and testing framework

---

*This project showcases both frontend development skills and test automation expertise, providing a complete solution for modern web applications.*