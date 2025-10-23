# 🌐 Social-Media-Platform - REST API Testing Suite

## 📋 Project Overview

Social-Media-Platform is a comprehensive REST API testing framework built with Node.js, Chai, and Mocha. This project demonstrates advanced API testing techniques including authentication, CRUD operations, user interactions, and social media features like following, liking, and commenting.

## 🎯 Key Features

- **REST API Testing**: Comprehensive API endpoint validation
- **Authentication Testing**: JWT token-based authentication
- **Social Media Features**: Follow, unfollow, like, unlike, comment functionality
- **User Management**: Profile operations and user interactions
- **Post Management**: Create, read, update, delete posts
- **Advanced Testing**: Chai assertions with HTTP testing
- **Data Validation**: Request/response validation and error handling

## 🏗️ Project Structure

```
Social-Media-Platform/
├── test/
│   └── task.js                 # Main test suite
├── package.json               # Node.js dependencies
└── README.md                  # Project documentation
```

## 🛠️ Technologies Used

- **Node.js**: JavaScript runtime environment
- **Chai**: Assertion library for testing
- **Chai-HTTP**: HTTP testing plugin for Chai
- **Chai-Sorted**: Array sorting validation
- **Mocha**: Test framework (implied)
- **REST API**: HTTP-based API testing

## 🧪 Test Scenarios

### 1. **Authentication Testing**
```javascript
beforeEach("User Authenticated", done => {
    chai.request(server)
    .post("/api/authenticate/login")
    .send(defaultUser)
    .end((err, res) => {
        token = res.body.token;
        res.should.have.status(200);
        done();
    });
});
```

**Features Tested:**
- User login authentication
- JWT token generation
- Session management
- Credential validation

### 2. **User Interaction Testing**
```javascript
describe('POST /api/follow/:id', ()=>{
    it("testing whether a user can follow another user", (done)=>{
        chai.request(server)
        .post(`/api/follow/${userId}`)
        .set({ authtoken : `${token}` })
        .end((err,res)=>{
            res.should.have.status(200);
            done();
        })
    })
})
```

**Features Tested:**
- User following functionality
- User unfollowing functionality
- Profile access validation
- User relationship management

### 3. **Post Management Testing**
```javascript
describe('POST /api/posts', ()=>{
    it("Post successful creation check", (done)=>{
        chai.request(server)
        .post('/api/posts')
        .set({ authtoken : `${token}` })
        .send(dummyPost)
        .end((err,res)=>{
            res.should.have.status(200);
            done();
        })
    })
})
```

**Features Tested:**
- Post creation with validation
- Post deletion functionality
- Post retrieval and filtering
- Content validation

### 4. **Social Engagement Testing**
```javascript
describe('POST /api/like/:id', ()=>{
    it("Able to Like a Post", (done)=>{
        chai.request(server)
        .post(`/api/like/${postId}`)
        .set({ authtoken : `${token}` })
        .end((err,res)=>{
            res.should.have.status(200);
            done();
        })
    })
})
```

**Features Tested:**
- Post liking functionality
- Post unliking functionality
- Comment system
- Engagement metrics

## 🚀 Getting Started

### Prerequisites
- Node.js 14+ or higher
- npm or yarn package manager
- REST API server running
- MongoDB or database connection

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Social-Media-Platform
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Configure test environment**
   ```bash
   # Set environment variables
   export API_BASE_URL=http://localhost:3000
   export TEST_USER_EMAIL=test@example.com
   export TEST_USER_PASSWORD=testpassword
   ```

4. **Run tests**
   ```bash
   npm test
   # or
   yarn test
   ```

## 🔧 Configuration

### Test Data Setup
```javascript
let defaultUser = {
    email: "pratap123@email.com",
    password: "pratap"
};

const dummyPost = {
    title: "CSE",
    description: "CSE is the trending degree nowdays"
};

const userId = "63aab02b121a380036383e8e";
const postId = "63ac732f377ccda1fc090d3b";
```

### Chai Configuration
```javascript
const server = require('../index');
let chai = require('chai');
let chaihttp = require('chai-http');

chai.should();
chai.use(chaihttp);
chai.use(require("chai-sorted"));
```

## 📊 API Endpoints Tested

### Authentication Endpoints
- `POST /api/authenticate/login` - User login
- `POST /api/authenticate/register` - User registration
- `POST /api/authenticate/logout` - User logout

### User Management
- `GET /api/user` - Get user profile
- `PUT /api/user` - Update user profile
- `DELETE /api/user` - Delete user account

### Social Features
- `POST /api/follow/:id` - Follow user
- `POST /api/unfollow/:id` - Unfollow user
- `GET /api/followers` - Get followers list
- `GET /api/following` - Get following list

### Post Management
- `POST /api/posts` - Create new post
- `GET /api/posts/:id` - Get specific post
- `GET /api/all_posts` - Get all posts
- `PUT /api/posts/:id` - Update post
- `DELETE /api/posts/:id` - Delete post

### Engagement Features
- `POST /api/like/:id` - Like post
- `POST /api/unlike/:id` - Unlike post
- `POST /api/comment/:id` - Comment on post
- `GET /api/comments/:id` - Get post comments

## 🧪 Test Implementation

### HTTP Request Testing
```javascript
chai.request(server)
    .post('/api/endpoint')
    .set({ authtoken: token })
    .send(requestData)
    .end((err, res) => {
        res.should.have.status(200);
        res.body.should.be.a('object');
        done();
    });
```

### Authentication Flow
```javascript
beforeEach("User Authenticated", done => {
    chai.request(server)
    .post("/api/authenticate/login")
    .send(defaultUser)
    .end((err, res) => {
        token = res.body.token;
        res.should.have.status(200);
        done();
    });
});
```

### Error Handling Testing
```javascript
it("Post creation with Title field missing", (done)=>{
    chai.request(server)
    .post('/api/posts')
    .set({ authtoken : `${token}` })
    .send({ description: "Missing title" })
    .end((err,res)=>{
        res.should.have.status(500);
        done();
    })
})
```

## 📈 Test Categories

### 🔐 Authentication Tests
- **Login Validation**: Credential verification
- **Token Management**: JWT token handling
- **Session Security**: Authentication state
- **Error Handling**: Invalid credentials

### 👥 User Management Tests
- **Profile Operations**: CRUD operations
- **User Relationships**: Follow/unfollow
- **Data Validation**: Input validation
- **Privacy Controls**: Access restrictions

### 📝 Content Management Tests
- **Post Creation**: Content publishing
- **Post Retrieval**: Content access
- **Post Modification**: Content updates
- **Post Deletion**: Content removal

### 💬 Social Features Tests
- **Engagement**: Like, comment, share
- **Interactions**: User-to-user actions
- **Notifications**: Activity updates
- **Feed Management**: Content aggregation

## 🚨 Error Handling

### HTTP Status Codes
```javascript
// Success responses
res.should.have.status(200);  // OK
res.should.have.status(201); // Created

// Error responses
res.should.have.status(400); // Bad Request
res.should.have.status(401); // Unauthorized
res.should.have.status(404); // Not Found
res.should.have.status(500); // Internal Server Error
```

### Validation Testing
```javascript
// Test missing required fields
it("Post creation with Title field missing", (done)=>{
    chai.request(server)
    .post('/api/posts')
    .set({ authtoken : `${token}` })
    .send({ description: "Missing title" })
    .end((err,res)=>{
        res.should.have.status(500);
        done();
    })
})
```

## 📊 Data Validation

### Request Validation
```javascript
const dummyPost = {
    title: "CSE",
    description: "CSE is the trending degree nowdays"
};

// Test valid data
chai.request(server)
.post('/api/posts')
.set({ authtoken: token })
.send(dummyPost)
.end((err, res) => {
    res.should.have.status(200);
    res.body.should.have.property('title');
    res.body.should.have.property('description');
});
```

### Response Validation
```javascript
// Validate response structure
res.body.should.be.a('object');
res.body.should.have.property('success');
res.body.should.have.property('data');
res.body.data.should.be.a('array');
```

## 🔄 Continuous Integration

### Test Execution
```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- --grep "Authentication"

# Run with verbose output
npm test -- --reporter spec
```

### Environment Configuration
```bash
# Development
NODE_ENV=development
API_BASE_URL=http://localhost:3000

# Testing
NODE_ENV=test
API_BASE_URL=http://localhost:3001

# Production
NODE_ENV=production
API_BASE_URL=https://api.example.com
```

## 📈 Performance Testing

### Load Testing
```javascript
// Test multiple concurrent requests
describe('Load Testing', () => {
    it('should handle multiple concurrent requests', (done) => {
        const promises = [];
        for (let i = 0; i < 10; i++) {
            promises.push(
                chai.request(server)
                .get('/api/posts')
                .set({ authtoken: token })
            );
        }
        Promise.all(promises).then(() => done());
    });
});
```

### Response Time Testing
```javascript
it('should respond within acceptable time', (done) => {
    const startTime = Date.now();
    chai.request(server)
    .get('/api/posts')
    .set({ authtoken: token })
    .end((err, res) => {
        const responseTime = Date.now() - startTime;
        responseTime.should.be.below(1000); // Less than 1 second
        done();
    });
});
```

## 🚀 Future Enhancements

- [ ] **GraphQL Testing**: GraphQL API validation
- [ ] **WebSocket Testing**: Real-time communication testing
- [ ] **Database Testing**: Data integrity validation
- [ ] **Security Testing**: Vulnerability assessment
- [ ] **Performance Testing**: Load and stress testing
- [ ] **Mobile API Testing**: Mobile-specific endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your test cases
4. Submit a pull request

## 📄 License

This project is for educational purposes and demonstrates comprehensive REST API testing techniques.

## 👨‍💻 Author

**Bhargav Reddy** - API Testing Engineer & Project Creator
- Comprehensive REST API testing framework
- Advanced Chai and HTTP testing
- Social media platform validation
- Created and developed this complete API testing solution

---

*This framework provides a complete solution for REST API testing, covering authentication, CRUD operations, and social media features with comprehensive validation.*
