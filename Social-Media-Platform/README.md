# Social-Media-Platform — Full REST API Testing Suite

## End-to-End Explanation
The project exercises REST endpoints for a social network using Node.js, Chai, and Mocha. The tests (located in `test/task.js`) log in (`/api/authenticate/login`), manage users including follow/unfollow, exercise post CRUD operations, and validate social engagement endpoints (`like`, `comment`). A JWT token is stored per run and attached to subsequent requests, ensuring the entire flow (authentication → user/action → post engagement) mirrors a real social media session.

## Key Components & Coverage
- **`test/task.js`**: primary test suite covering authentication, follow flows, post creation/deletion, and engagement.
- **`package.json`**: lists dependencies (`chai`, `chai-http`, `mocha`, `chai-sorted`) and scripts for running tests and coverage.
- **`test/`**: organizes API tests, includes request setup and helper functions.
- **Environment Variables** (`API_BASE_URL`, `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`): keep endpoints and credentials configurable.
- **`README.md`**: this document, now describing theory/interview focus.

## Setup & Execution
1. Install **Node.js 14+** and **npm/yarn**.
2. Clone the repo and install dependencies via `npm install` or `yarn install`.
3. Configure environment variables:  
   - `API_BASE_URL=http://localhost:3000`  
   - `TEST_USER_EMAIL=test@example.com`  
   - `TEST_USER_PASSWORD=testpassword`
4. Run the suite with `npm test` or `yarn test`.
5. Optionally run coverage: `npm run test:coverage`.

## Reporting & Observability
- Chai assertions provide expressive failure messages (status, body structure).
- The suite prints request details to the console for each endpoint tested.
- Use `npm test -- --reporter spec` for verbose output when debugging complex flows.

## Important Interview Questions & Answers
1. **Q:** How do you test authenticated REST APIs reliably?  
   **A:** Hit `/api/authenticate/login` once per suite, store the returned JWT, and attach it to every subsequent request as shown in `test/task.js`.
2. **Q:** How do you validate social interactions like follow/unfollow and likes?  
   **A:** After authentication, call `/api/follow/:id`, `/api/unfollow/:id`, `/api/like/:id`, and verify the responses with HTTP 200 statuses plus expected JSON shapes.
3. **Q:** What is the role of negative tests here?  
   **A:** Tests such as missing required fields or wrong tokens ensure the API returns the correct HTTP status codes (`400`, `401`, `404`, `500`), guarding against regressions.

## Theory Knowledge for Interviews
- **RESTful Principles:** Understand HTTP verbs (GET/POST/PUT/DELETE), status codes, and idempotency so you can explain why each endpoint uses the appropriate verb.
- **JWT Authentication:** Know how tokens are issued (`/authenticate/login`), stored, and sent in headers for protected routes (the project uses `authtoken` header injection).
- **API Test Design:** Combine happy-path coverage (post creation, follows) with negative/error scenarios (missing title, unauthorized access) to validate both functionality and resilience.

## Troubleshooting & Tips
- Ensure the API server is running before executing tests; otherwise, you’ll see connection refused errors.
- Use the `--grep` flag (`npm test -- --grep "Authentication"`) to isolate specific scenarios while debugging.
- Keep dummy data (like `userId`, `postId`) up to date if the backend clears seeded data regularly.

## Next Steps
- Add schema validation (e.g., Joi or ajv) to ensure the APIs return the expected payload structure.
- Integrate `supertest` or `chakram` for richer HTTP testing or use Postman/Newman collections for exploratory checks.
