

## Supplier | About Us | Video | Company/Shop Profile | Customer Review of Supplier: 

- Read the codebase in detail and list down all the file and Function for Supplier | About Us | Video | Company/Shop Profile | Customer Review of Supplier | and its related code. and Supplier Panel also.
- http://localhost:3000/supplier=dream-mart
- UI and UX is too basic of the page and functions are not working properly.
- Please make it more attractive and user friendly and also make sure all the functions are working properly.
- Please also add the video section on the supplier profile page and also add the customer review section on the supplier profile page.
- there should be badge sytem for the suppliers based on their performance and customer reviews and the badge must be visible on the supplier profile page and also on the search result page when customer search for supplier which is too basic right now.


-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------


## Logistic Panel | Profile Page | Cities - Countries and Charges Management which will be reflect to customer order and cart system:

- Read the codebase in detail and list down all the file and Function for Logistic Panel.

- Read the Supplier Panel Profile Page code for your reference and make the Logistic Panel Profile Page in detail with all the necessary functions and UI/UX and test it properly backend and frontend both.

- Logistic Panel should have the option to manage cities, countries and charges which will be reflect to customer order and cart system and that will be reflect into all the order management system. implement it and test it properly backend and frontend both.

- Admin Panel will have for approval to accept the Logistic Partner Charges and Cities and Countries management and also for the approval of Logistic Partner Profile. 

- http://localhost:3000/logistics-partner/ 

- this is very tricky and important part of the system so please make sure to implement it properly and test it properly backend and frontend both and verifiy Order and Cart System reflection becasue it is linked with the `location` and `GPS system` becasue it is wokring cities and countries. Admin must to accept the charges which is giving by the logistic partner then it should be complete the process and reflect to the order and cart system. if admin reject the charges then it should not be reflect to the order and cart system. and also logistic partner profile must be approved by admin then only it should be visible to the customers and also in the search result when customer search for logistic partner.

- according to `ORDER_MANAGEMENT.md` system when the Supplier will complete preperation of the order means point number 3 and 4. if the Admin reject the logistic partner changes then it should not be flash the order in the partner shipment page `http://localhost:3000/logistics-partner/shipments`.

- make a complete plan, checkpoint, test before implementation and after implementation and start to work on it.


-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------


## Payment Management System | Cash on Delivery | Pay by Card | Payout System of Supplier and Logistic Partner:

let's get back to cash management system of the ZOZI website.
There is 2 ways to payment "Cash on Delivery" and "Pay by Card"

- "Cash On Delivery" will receive by the Logistic Partner which is last end.
- "Pay by Card" will receive by the Zozi Management.

Now the point is how we will manage efficiently and track cash appropriately ?

Every Order have 4 components:
    1. Product Price.
    2. Delivery Charges. - which have 2 changes Pick-Up Charges and Drop-Off Charges. 
    3. VAT - 5% of the Product Price and Delivery Charges.
    4. ZOZI Service Charges - 10% to 20% of the Product Price.


## Problem 1: 
    When Logistic Partner receive cash on delivery from the customer then how Zozi Management will ask the Delivery Charges from the Logistic Partner and Logistic Partner never pay it back to the Zozi Management becasue it is their charges to keep with them.

## Problem 2: 
    How can we reconcile Management automatically and Payout System will work automatically for the Supplier and Logistic Partner based on the order completion and delivery.

## Problem 3:
    If the customer will order for Product A, B and C from Supplier A, B, and C.
    - `Supplier A` is located `City 1` and `Logistic Partner 1` will pick up the order from `City 1`.
    - `Supplier B` is located `City 2` and `Logistic Partner 2` will pick up the order from `City 2`.
    - `Supplier C` is located `City 3` and `Logistic Partner 3` will pick up the order from `City 3`.
    - Pick-up Charges of `City 1`, `City 2` and `City 3` 
    - Drop-off Charges of `City 4` which is customer location.
    - How it will be manage full process and how we will manage the reconciliation and payout system for the Supplier and Logistic Partner based on the order completion and delivery ?

## Problem 4:
    How we will manage the refund process for the customer and how it will be reflect to the Supplier and Logistic Partner based on the order cancellation and refund process ?

## Problem 5:
    How to reconcile with Bank System -> Supplier Payout -> Logistic Partner Payout -> Cash on Delivery Reconciliation -> Pay by Card Reconciliation -> Refund Reconciliation -> Payout Reconciliation -> etc.

## Problem 6:
    Product Wise, Category Wise, Weight Wise, Distance Wise.
    How we will manage the charges and payment management system for the different product, category, weight and distance ?

What will be complete ecosystem of the payment management system for the ZOZI website and how it will be manage and track efficiently and automatically with the help of technology and how we will manage the reconciliation process for the Zozi Management, Supplier and Logistic Partner.

## Some suggestions for the payment management system:
    1. Suggestion of Hybrid Model: `flat fees for in‑city, distance + weight for inter‑city.` is nice
    2. `Allow product/category overrides for bulky or fragile items` this suggestion also nice.
    3. Ensure logistics partner revenue is tied to actual effort (weight + distance), making it profitable and sustainable.





--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------

## UI and UX of the web_app:

1. Read the codebase in detail and list down all the file and Function for UI and UX of the web_app.
2. UI and UX of the web_app is mis-match accross all the pages, button, widgets, font, theme, color, panel, glossy look accross all the pages. 
3. Panel Pages, Login/Signup Page of `Admin`, `Supplier` and `Logistic Partner` needs to be attention to be similar.
4. Light theme need attention to be look glossy and attractive and better look.
5. Dark theme as well for similar accross to all the pages and panels.
6. Need complete audit and review of the UI and UX of all the pages and panels and make it more attractive, user friendly and glossy look and similar accross to all the pages and panels and also make sure all the functions are working properly.
7. All three panels `Admin`, `Supplier` and `Logistic Partner` will be handle 1000s of queries and request at a time so according to that you can use below intelligently: 
    -  alert and notification system.
    -  tabs and filters system, search and sorting system. 
    -  color coding system for the status and priority and etc but under the theme, not extra colors.
    -  complete integrated dashborad system for the panels to manage and track all the queries and request efficiently and effectively.
    - and make changes of improvement what you feel better to have in the Ui and UX to manage and track 1000s of queries and request at a time. 
8. You don't need to make big changes.
9. Make a complete plan, checkpoint, test before implementation and after implementation and start to work on it.
10. You have to be careful while working on the UI and UX our website is already 80% complete already.


--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------

## Audit of UI and UX of the web_app:

### Phase 1: Analysis
1. Audit all pages in `frontend/web_app` and document current UI/UX inconsistencies
2. Identify mismatches across: buttons, widgets, fonts, themes, colors, spacing, and visual effects
3. Compare Login/Signup and Panel designs for `Admin`, `Supplier`, and `Logistic Partner` - highlight alignment gaps

### Phase 2: Design System Definition
4. Create a unified design system with consistent theme variables (light and dark modes)
5. Define standardized components: buttons, cards, inputs, modals, notifications, and panels
6. Establish typography, spacing, color palette, and glossy visual effects guidelines

### Phase 3: Implementation Strategy
7. For high-volume query/request management across all panels, implement:
    - Smart alert and notification system with priority levels
    - Advanced filters, search, and sorting functionality
    - Color-coded status indicators (using theme-aware palette, no extra colors)
    - Integrated dashboard with real-time analytics and query tracking
    - Responsive layout optimizations for handling concurrent operations
8. Minimize disruption: target incremental refinements, not full redesigns
9. Create migration checkpoints to prevent breaking existing functionality

### Phase 4: Execution & Validation
10. Establish QA checkpoints (pre-implementation, mid-sprint, post-implementation)
11. Test all functionality across light/dark themes on each updated page
12. Verify performance under load and ensure consistency across all three panels
13. Proceed carefully—preserve the 80% completion; focus on polish and consistency



--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------

## Update of Banner Management System:

--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------


## Mobile App Audit, Alignment & Enhancement

### Phase 1: Codebase Analysis
1. List all files, folder structure, pages, components, and functions in `frontend/mobile_app` and `frontend/shared`
2. Document UI/UX framework, state management, authentication, API integration, and navigation
3. Audit all existing functionality: features, bugs, performance issues, and incomplete implementations
4. Update `CODEBASE_STATUS_MATRIX_DETAILED.md` with mobile app current status

### Phase 2: Web-to-Mobile Feature Mapping
5. Create comprehensive inventory of all `frontend/web_app` pages, components, functions, and features
6. Map each web_app feature to corresponding mobile_app implementation status (Complete/Partial/Missing/Broken)
7. Identify gaps: missing pages, missing functions, incomplete features, and non-working functions
8. Document UI/UX differences and usability issues specific to mobile

### Phase 3: Bug Fixing & Core Stabilization
9. Reproduce, document, and fix all identified bugs and issues in mobile_app
10. Test core functionality: authentication, API calls, state persistence, offline handling, navigation flow
11. Verify error handling, validation, and user feedback across all screens
12. Test on multiple device sizes (phone, tablet), orientations, and OS versions

### Phase 4: Feature Implementation & Alignment
13. Implement all missing pages and features from web_app (prioritize by business criticality)
14. Ensure functional parity: test each implemented feature against web_app equivalent
15. Implement missing API integrations and backend connections
16. Verify all components integrate properly with `frontend/shared` components

### Phase 5: UI/UX Enhancement & Consistency
17. Audit UI consistency: typography, spacing, colors, button styles, icons, and theme application
18. Redesign basic/outdated UI elements to match modern mobile standards
19. Implement responsive design patterns for varied screen sizes
20. Apply unified design system across light/dark themes for mobile platform
21. Enhance navigation patterns, gestures, loading states, and error screens

### Phase 6: Performance & Reliability Testing
22. Profile app performance: startup time, memory usage, navigation speed, API response time
23. Optimize: lazy loading, image optimization, state management, network requests
24. Test offline functionality, network reconnection handling, and data sync
25. Conduct load testing and stress testing on critical features

### Phase 7: End-to-End Testing
26. Create comprehensive test matrix covering all pages, functions, and user flows
27. Test on real devices (not just emulators): iOS and Android, various OS versions
28. Perform UAT (User Acceptance Testing) across all three user types: Customer, Supplier, Logistic Partner
29. Test payment flows, order management, notifications, and authentication workflows
30. Verify all backend API calls work correctly and handle errors gracefully

### Phase 8: Security & Data Validation
31. Audit security: credentials storage, API authentication, data encryption, sensitive data handling
32. Validate input handling on all forms and user inputs
33. Test permission requests (camera, location, notifications, storage)
34. Verify secure session management and logout functionality

### Phase 9: Documentation & Readiness
35. Document all implemented features, known limitations, and known issues
36. Create user guides for mobile app functionality
37. Update developer documentation with mobile-specific implementation details
38. Prepare release notes and deployment checklist

### Testing Checkpoints:
- **Pre-Implementation**: Document current issues, create test cases database
- **Mid-Implementation**: Test features as implemented, verify API integration
- **Post-Implementation**: Full regression testing, device compatibility testing, performance validation
- **Final Release**: UAT sign-off, production readiness check, backup and rollback plan

### Success Criteria:
- All web_app features functional in mobile_app (or documented as intentional omissions)
- No critical bugs; all P0 and P1 issues resolved
- Performance metrics met (startup < 3s, navigation < 500ms, API calls < 2s)
- UI/UX consistent across all screens and themes
- All three user roles (Customer, Supplier, Logistic Partner) fully functional with complete workflows
- Test coverage > 80% on critical user flows


--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------

## Audit Cash Management and Payment Management Cycle

- List down all the File and Function of `frontend/web_app`, `frontend/mobile_app`, `backend`, `backend API`, `Database setup` for `Cash and Payment Management Cycle` in detail and test all the files and update the `CODEBASE_STATUS_MATRIX_DETAILED.md` because this the document from which we are following for completing the project.

- Investigate and Audit in detial and Review each and every element of the `Cash and Payment Management Cycle` and findout what are actually the problems and issues in the `Cash and Payment Management Cycle` and list down all the problems and issues in detail and start to work on it one by one and make sure all the functions are working properly in the `Cash and Payment Management Cycle` and also make sure it is efficient, secure, scalable, reliable, maintainable and well documented as well.

- The Target ressult `Cash and Payment Management Cycle` should be:
    - Admin Panel : Admin will put the Bank Account details and updated Bank Statement. 
        - it will automatically start the `payout system` and also for the `reconciliation process` and also for the refund process and etc.
        - Logistic Partner will receive the cash on delivery from the customer and then it will automatically start the `reconciliation process` for the cash on delivery and also for the payout system for the logistic partner and also for the refund process and etc.
        - Supplier will receive the payment from the Zozi Management for the order completion and delivery and then it will automatically start the `reconciliation process` for the payment and also for the payout system for the supplier and also for the refund process and etc.
    - Customer Panel : Customer will make the payment by card and then it will automatically start the `reconciliation process` for the pay by card and also for the refund process and etc.
    - Reconciliation Process : it will automatically reconcile with the Bank System -> Supplier Payout -> Logistic Partner Payout -> Cash on Delivery Reconciliation -> Pay by Card Reconciliation -> Refund Reconciliation -> Payout Reconciliation -> etc.
    - Payout System : it will automatically payout to the Supplier and Logistic Partner based on the order completion and delivery and also based on the cash on delivery and pay by card and also based on the refund process and etc.
    - Refund Process : it will automatically manage the refund process for the customer and also for the Supplier and Logistic Partner based on the order cancellation and refund process and also based on the cash on delivery and pay by card and also based on the reconciliation process and etc.

- Test everything for the `Cash and Payment Management Cycle` and make sure all the functions are working properly in the `Cash and Payment Management Cycle` and also make sure it is efficient, secure, scalable, reliable, maintainable and well documented as well.

- Potential Problem: 
    - How it will connect with real bank account even if I give you real bank account details ?

--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------


## Audit and Implementation of Email System:

### Email System Optimization | Email System Security | Email System Performance | Email System Scalability | Email System Reliability | Email System Maintainability | Email System Backup and Recovery | Email System Checking and Auditing | Email System Documentation:

- List down all the File and Function of `frontend/web_app`, `frontend/mobile_app`, `backend`, `backend API`, `Database setup` for `Email System` in detail and test all the files and fix the error and bugs. 
- update the `CODEBASE_STATUS_MATRIX_DETAILED.md` because this the document from which we are following for completing the project and also for the future reference.

- Target Result to achieve for the `Email System` should be:

    - Admin Panel : 
 
        - Admin will manage the `email templates` and `email content` and also manage the email system and also manage the email service provider and also manage the email related functions and features in the admin panel.
 
        - Admin will put the email address, for example:
            - for promotional email         ->  donotreply@zozi.com 
            - for transactional email       ->  donotreply@zozi.com
            - for notification email        ->  donotreply@zozi.com
            - for alert email               ->  alert@zozi.com
            - for verification email        ->  alert@zozi.com
            - for login verification email  ->  alert@zozi.com
            - for password reset email      ->  alert@zozi.com
 
            - For testing purpose you can use my personal email address which is 
            Email: `arshad.khan198345@gmail.com` 
            Password `BlackBird@WhiteTree5`
            zozi smpt
            Password: vazf bkxk uclg xicl

        - promotion, notification, alert email will circulate to all the customer list and also to the supplier and logistic partner list for the promotion and marketing purpose.
            - for that admin need coplete email bank for management of the email system and also for the email related functions and features in the admin panel.

        - `Customer`,  `Logistic Partner` and `Supplier` will receive the email for the order status, order update, order cancellation, order refund, order delivery and etc. and also for the payment status, payment update, payment refund and etc. and also for the account related functions and features like login verification, password reset and etc.

        - Later on Admin will change the email when we will get domain and hosting for the website and also for the email service provider from the Admin Panel. So make sure Admin Panel will have the option to change the email configuration setting feature and page. 

- Promotional Email, Transactional Email, Notification Email, Alert Email, Verification Email, Login verification Email, Password Reset Email and etc should be working properly and efficiently for all the email related functions and features in the `frontend/web_app`, `frontend/mobile_app`, `backend`, `backend API`, `Database setup` for `Email System`.

- Email System should be working properly and efficiently for all the email related functions and features in the `frontend/web_app`, `frontend/mobile_app`, `backend`, `backend API`, `Database setup` for `Email System`.

- Email System should be secure, scalable, reliable, maintainable and well documented as well.

- Email System should be integrated with the real email service provider and should be able to send and receive emails properly.

- You are end to end manager of to integration of Email System, you have complete authority to fix, revise and improve to manage and control the Email System to complete. Make a complete plan, checkpoint, test before implementation and after implementation and start to work on to finish the Email System and also make sure all the functions are working properly in the `Email System`.



--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------


## Audit | Review | Testing | Cleaning | Debugging | Optimization | Security | Performance | Scalability | Reliability | Maintainability | Documentation 

- Read, Test, Audit and Investigate complete `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup` in detail and update the #file:CODEBASE_STATUS_MATRIX_DETAILED.md because this the document from which we are following for completing the project. 

- `backend`, `backend API`, `Database setup` -> shift all the test files into one folder - update one by one all the test file and test all the features and files of the backend.
- `frontend/web_app`, -> shift all the test files into one folder - update one by one all the test file and test all the features and files of the `web_app`.
- `frontend/mobile_app`, `frontend/shared` -> shift all the test files into one folder - update one by one all the test file and test all the features and files of the `mobile_app`.


## Files Management | Folder Management | Function Management | Variable Management | Code Structure Management | Code Style Management | Code Consistency Management | Code Readability Management | Code Documentation Management:

- Read, Review, Test, Audit and Investigate complete `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup` in detail for the Files Management, Folder Management, Function Management, Variable Management, Code Structure Management, Code Style Management, Code Consistency Management, Code Readability Management and Code Documentation Management and update the #file:CODEBASE_STATUS_MATRIX_DETAILED.md because this the document from which we are following for completing the project.

- Make a list of majors and minors changes for the Files Management, Folder Management, Function Management, Variable Management, Code Structure Management, Code Style Management, Code Consistency Management, Code Readability Management and Code Documentation Management for the `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup` and then start making changes one by one and make sure all the functions are working properly in the `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup` and also make sure it is efficient, secure, scalable, reliable, maintainable and well documented as well.

- You are end to end manager for Review of Codebase, you have complete authority to fix, revise and improve to manage and control the entire process to complete. 
- Make a complete plan, checkpoint, test before implementation and after implementation and start to work on to finish and also make sure all the functions are working properly in the `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup`.

## Code Quality | Code Refactoring | Code Review | Code Optimization | Code Debugging | Code Testing | Code Cleaning | Code Security | Code Performance | Code Scalability | Code Reliability | Code Maintainability | Code Documentation:

- Read, Review, Test, Audit and Investigate complete `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup` in detail for the Code Quality, Code Refactoring, Code Review, Code Optimization, Code Debugging, Code Testing, Code Cleaning, Code Security, Code Performance, Code Scalability, Code Reliability, Code Maintainability and Code Documentation and update the #file:CODEBASE_STATUS_MATRIX_DETAILED.md because this the document from which we are following for completing the project.

- Make a list of majors and minors changes for the Code Quality, Code Refactoring, Code Review, Code Optimization, Code Debugging, Code Testing, Code Cleaning, Code Security, Code Performance, Code Scalability, Code Reliability, Code Maintainability and Code Documentation for the `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup` and then start making changes one by one and make sure all the functions are working properly in the `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup` and also make sure it is efficient, secure, scalable, reliable, maintainable and well documented as well.

- You are end to end manager for Review of Codebase, you have complete authority to fix, revise and improve to manage and control the entire process to complete. 

- You have to be carefully clean also files which are not in use except documents and test files.
    - Remove unnecessary files and when reviewing the code if you find any better way to changes the code for improvement then you can do it but make sure about the `functionality` are working properly in the `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup` and also make sure it is efficient, secure, scalable, reliable, maintainable and well documented as well.

    - Remove unncessary file if there is doubled files.

    - test files should be in one folder for each `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared` and also for the `backend API` and `Database setup` and also make sure all the test files are working properly and updated and all the tests are passing successfully.

- Make a complete plan, checkpoint, test before implementation and after implementation and start to work on to finish the Code Quality, Code Refactoring, Code Review, Code Optimization, Code Debugging, Code Testing, Code Cleaning, Code Security, Code Performance, Code Scalability, Code Reliability, Code Maintainability and Code Documentation and also make sure all the functions are working properly in the `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup`.

-----------------------------------------------------------------------------------
-----------------------------------------------------------------------------------

## Database Optimization | Database Security | Database Performance | Database Scalability | Database Reliability | Database Maintainability | Database Backup and Recovery | database Checking and Auditing | Database Documentation:

## Server Optimization | Server Security | Server Performance | Server Scalability | Server Reliability | Server Maintainability | Server Backup and Recovery | Server Checking and Auditing | Server Documentation:

## API Optimization | API Security | API Performance | API Scalability | API Reliability | API Maintainability | API Documentation:

## Error Handling Optimization | Error Handling Security | Error Handling Performance | Error Handling Scalability | Error Handling Reliability | Error Handling Maintainability | Error Handling Documentation:

## Logging Optimization | Logging Security | Logging Performance | Logging Scalability | Logging Reliability | Logging Maintainability | Logging Documentation:

## Health Check Optimization | Health Check Security | Health Check Performance | Health Check Scalability | Health Check Reliability | Health Check Maintainability | Health Check Documentation:

--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------


Cash and Payment and Payout Management System: 

Admin Panel 
    - Audit all `Admin Panel` pages, settings, and functionalities in detail.
    - Identify duplicate or similar functionalities across pages that can be consolidated.
    - Refactor widgets to reduce complexity and improve maintainability and performance.
    - Create a comprehensive inventory of all Admin Panel pages and functions with their dependencies and use cases.
    - Implement optimizations to reduce the number of pages and widgets while ensuring all necessary functionalities are retained and easily accessible.
    - Implement a more intuitive navigation structure to improve Admin experience and efficiency.
    - Document recommended optimizations for better management, scalability, and user control.
    - 


Read carefully `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup` and list down all the Files and Functions related to the below points and start improvement in detail and make sure all the functions are working properly and also make sure it is efficient, secure, scalable, reliable, maintainable and well documented as well.

## Admin Panel UI reorganize and re-arrange elements and functions for better management, scalability and user control:
- Hierarchy of the Admin Panel pages is harded code to be controlable by Admin and it should be efficient and scalable because which will allow to add new staff and Hierarchy and roles.

- `Product Page` interface and functions also need attention to be more efficient and scalable because it is the most important part of the system and also it is linked with the `inventory management system` and also with the `order management system` and some Admin Roles CRUDS and Bluk operations also needed, so make sure to review it in detail and make it more efficient, secure, scalable, reliable, maintainable and test after making changes.

- `Order Page` interface and functions also need attention to be more efficient and scalable because it is the most important part of the system and also it is linked with the `inventory management system` and also with the `product management system` and some Admin Roles CRUDS and Bluk operations also needed, so make sure to review it in detail and make it more efficient, secure, scalable, reliable, maintainable and test after making changes.

- Barcode and QR Code Page in Admin Panel - is irrelevant because that Function for the Order Page and Product Page - so shift or remove it.

- Return Page in Admin Panel - is part of Order Page - so shift it.

- `Users Page` needs proper Bulk CRUD Operations and also need to be more efficient and scalable.

- Supplier Page in Admin Panel needs proper Bulk CRUD Operations and also need to be more efficient and scalable and this page is too messy having large size of widgets which is creating problem for the preformance and handling of the page and so make sure to review it in detail and make it more efficient, secure, scalable, reliable, maintainable and test after making changes.

- Logistic Page in Admin Panel needs proper Bulk CRUD Operations and also need to be more efficient and scalable and this page is too messy having large size of widgets which is creating problem for the preformance and handling of the page and so make sure to review it in detail and make it more efficient, secure, scalable, reliable, maintainable and test after making changes.

- Dashboard Page and Analytics Page in Admin Panel widgets are very large and not reflecting proper information regarding system and preformance and also need to be more efficient and scalable. It should to show every single detail regarding system and keep updating in real time.

- Ticket Page in Admin Panel - I don't understand what is the purpose of this page and why we created - find out the purpose and if you didn't get any valid reason for that remove it.

- Export Page in Admin Panel - should to shift that into Dashborad Page with some filters and options to export the data in different formats and also need to be more efficient and scalable. 

- Verifications Page in Admin Panel - is irrelevant because that Function for Product Page and Supplier Page - so shift or remove it.


### Admin Panel / Staff Management Page:

**Staff Addition & Configuration:**
- Require complete staff details during creation: full name, email, contact, hire date, area of operation
- Assign roles and permissions at creation time
- Auto-sync role changes to staff panel for access control

**Staff Management Table:**
- Display staff listing with: Name, Email, Role, Area, Status, Actions
- Include inline edit, view, deactivate, and delete actions
- Support multi-select for bulk operations (role updates, area assignments, status changes)

**Role & Permission System:**
- Replace hierarchy-based access with flexible role assignment
- Allow admin to override roles based on performance and experience
- Maintain granular permissions list (view, create, edit, delete, export, etc.)
- Enable area-specific access (regions, warehouses, departments)
- Create custom roles with specific task/project assignments

**UI/UX Standards:**
- Professional enterprise-grade interface matching admin panel design
- Pagination with sorting/filtering capabilities
- Search functionality across name, email, role
- Responsive design for desktop/tablet
- Clear visual feedback for status changes and permissions
- Comprehensive documentation for role assignment best practices

--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------


### UI/UX Optimization - Admin, Supplier & Logistics Partner Panels

Review and refactor the following directories to support enterprise-scale operations (1000+ users/inquiries):
- `frontend\web_app\src\app\admin\`
- `frontend\web_app\src\app\supplier\`
- `frontend\web_app\src\app\logistics-partner\`

**Required Changes:**

1. **Component Optimization:**
   - Remove unnecessary/unused items from all pages
   - Reduce widget sizes to improve page performance and rendering
   - Reduce button sizes for better space utilization
   - Expand main content area to display more data efficiently

2. **UI/UX Improvements:**
   - Redesign panels to handle high-volume operations (1000s of customers/inquiries)
   - Implement compact, scalable layouts with improved data density
   - Replace basic designs with professional, enterprise-grade interfaces
   - Optimize for performance, responsiveness, and usability at scale

3. **Admin Panel Focus:**
   - Prioritize admin pages as they manage highest volume of inquiries
   - Add batch operation capabilities and bulk actions
   - Implement efficient filtering, sorting, and search mechanisms
   - Ensure pages can handle 1000+ concurrent data records

--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------


## Audit and Review of Admin, Supplier & Logistics Partner Panel UI and UX to handle 1000s of queries and request at a time:

## ✅ STRUCTURED DEVELOPMENT PROMPT: UI/UX MODERNIZATION & TESTING

**Status:** ACTIONABLE & TESTABLE | **Priority:** P1 | **Timeline:** Phase-based

---

### **PHASE 1: PLAN & CHECKPOINT (Before Implementation)**

#### **1.1 Code Audit Checklist**
**Objective:** Map the entire codebase before making changes.

**Files to Document:**
```
✓ List all component files in: frontend/web_app/src/app/admin/
✓ List all component files in: frontend/web_app/src/app/supplier/
✓ List all component files in: frontend/web_app/src/app/logistics-partner/
✓ Identify shared UI components in: frontend/shared/
✓ Document all CSS/styling frameworks (Tailwind, Ant Design, etc.)
✓ Extract all reusable hooks and utilities
```

**Output:** `CODEBASE_AUDIT.md` file containing:
- Component hierarchy tree
- Current styling inconsistencies
- Performance bottlenecks
- Missing test coverage

---

#### **1.2 Design System Definition**
**Objective:** Establish consistent UI standards across all panels.

**Create:** `DESIGN_SYSTEM.md` with:
- **Typography:** Font sizes (xs, sm, base, lg, xl), font weights, line heights
- **Spacing:** Global spacing scale (px-1 to px-8)
- **Colors:** Light & Dark theme palettes with semantic naming
- **Components:** Button sizes (xs, sm, md, lg), badge styles, card designs
- **Data Density Modes:**
  - **Compact:** text-xs, py-1, max rows per page: 50
  - **Normal:** text-sm, py-2, max rows per page: 25 (default)
  - **Expanded:** text-base, py-4, max rows per page: 10

---

### **PHASE 2: IMPLEMENTATION (By Component Type)**

#### **2.1 Priority Implementation Order**
1. **Admin Dashboard** (handles highest volume)
2. **Admin Tables/Data Grids** (1000+ records display)
3. **Admin Forms & Modals**
4. **Supplier Dashboard** (medium priority)
5. **Logistics Partner Dashboard** (medium priority)
6. **Mobile Responsive Views**

---

#### **2.2 ADMIN DASHBOARD - Detailed Specification**

**File Path:** `frontend/web_app/src/app/admin/dashboard/page.tsx`

**Requirements:**
```markdown
1. Main Layout
   - Collapsible sidebar (4rem collapsed, 16rem expanded)
   - Full-width main content grid
   - Data density toggle (top-right corner)
   - Theme switcher (light/dark)

2. Dashboard Cards (Resize-enabled)
   - Total Orders, Revenue, Pending Tickets, Active Users
   - Each card: min-w-64 px, responsive grid
   - Config saved to localStorage: `dashboard_layout_${userId}`

3. Chart Section
   - Sales trend (last 30 days) - compact in compact mode
   - Collapsible legend to save space
   - Responsive height based on density mode

4. Quick Action Buttons
   - Reduced size in compact mode: px-3 py-1
   - Consolidated into dropdown in mobile view
   - Accessible via keyboard shortcuts
```

**Testing Checklist:**
- [ ] Sidebar collapse/expand works smoothly
- [ ] Data density toggle applies to all sections
- [ ] Charts render correctly in all density modes
- [ ] Layout responsive on mobile (<768px)
- [ ] LocalStorage persists user preferences
- [ ] No console errors or warnings

---

#### **2.3 DATA TABLES - Enterprise Grid Component**

**File Path:** `frontend/shared/components/EnterpriseDataTable.tsx`

**Specification:**
```typescript
// Core Features
- Supports 1000+ rows with virtual scrolling
- Configurable columns (show/hide, reorder, resize)
- Built-in filtering (multi-column, type-aware)
- Sorting (single/multi-column)
- Search bar integrated (global + column-specific)
- Pagination: 10, 25, 50, 100 rows per page (adaptive)
- Bulk actions (select all, select page, select filtered)
- Row actions menu (edit, delete, view details)
- Inline cell editing (optional, per column)
- Column freeze support (first N columns)
- Data export: CSV, PDF (filtered/sorted data)
- Responsive: Collapse to cards on mobile

// Density Modes
COMPACT:   font-xs, py-1, min header height 36px
NORMAL:    font-sm, py-2, min header height 44px
EXPANDED:  font-base, py-4, min header height 56px

// Configuration Example
{
  columns: [
    { key: 'id', label: 'ID', width: '80px', sortable: true, searchable: true },
    { key: 'status', label: 'Status', width: '100px', filterable: true, renderer: StatusBadge },
    { key: 'amount', label: 'Amount', width: '120px', sortable: true, format: 'currency' }
  ],
  rowsPerPage: 25,
  densityMode: 'normal',
  enableBulkActions: true,
  enableExport: true,
  onRowClick: handleRowClick
}
```

**Testing Checklist:**
- [ ] Render 1000+ rows without lag (virtual scrolling)
- [ ] Filter works across all columns
- [ ] Sort maintains data integrity
- [ ] Bulk select: all, page, filtered rows
- [ ] CSV export includes visible columns only
- [ ] Column resize persists to localStorage
- [ ] Mobile view collapses to card layout
- [ ] Keyboard navigation functional (Tab, Arrow keys)
- [ ] Accessibility: ARIA labels, screen reader compatible

---

#### **2.4 FORMS & MODALS - Consistency Update**

**Files to Update:**
- `frontend/web_app/src/app/admin/forms/*`
- `frontend/web_app/src/app/supplier/forms/*`
- `frontend/web_app/src/app/logistics-partner/forms/*`

**Specification:**
```
1. Form Layout
   - Max width: 600px (desktop), 100% (mobile)
   - Field size consistency: all use same input height (40px default, 32px compact)
   - Label styling: bold, 12px, semantic color

2. Button Groups
   - Primary button: always on right
   - Secondary, Cancel buttons: left-aligned
   - Mobile: stack vertically, full width

3. Validation Feedback
   - Real-time validation (debounced 300ms)
   - Error messages below field with error icon
   - Success toast notifications (top-right, auto-dismiss 3s)

4. Modal Styling
   - Consistent backdrop blur, shadow
   - Header: title + close button (top-right)
   - Fixed footer with action buttons
   - Responsive: max-h-90vh, overflow-y-auto
```

**Testing Checklist:**
- [ ] All forms follow same structure
- [ ] Validation messages clear and actionable
- [ ] Mobile forms stack properly
- [ ] Toast notifications appear and dismiss correctly
- [ ] Modal closes on ESC key
- [ ] No unsaved form data loss warning working

---

### **PHASE 3: PERFORMANCE TESTING**

#### **3.1 Lighthouse Audit**
**Each Page Must Achieve:**
- Performance: ≥85
- Accessibility: ≥95
- Best Practices: ≥90
- SEO: ≥90

**Run Command:**
```bash
npm run build
npx lighthouse http://localhost:3000/admin/dashboard --view
```

#### **3.2 Load Testing**
**Test Scenario: 1000+ records display**
```bash
# Simulate data load in browser console
npx artillery run load-test.yml --target http://localhost:3000
```

**Expected Results:**
- Table render time: <2s
- Pagination response: <500ms
- Filter response: <800ms
- Bulk action execution: <1s

---

#### **3.3 Responsive Testing**
**Device Breakpoints to Test:**
- Mobile: 375px (iPhone SE), 414px (iPhone 12)
- Tablet: 768px (iPad), 1024px (iPad Pro)
- Desktop: 1440px, 1920px
- Ultrawide: 2560px

**Test Tools:**
```bash
npm run start
# Open DevTools → Device Toggle → Test each breakpoint
```

---

### **PHASE 4: END-TO-END TESTING**

#### **4.1 Smoke Test Checklist**

**Admin Panel - `/admin`**
- [ ] Dashboard loads with all cards visible
- [ ] Sidebar collapse/expand works
- [ ] Data density toggle applies correctly
- [ ] All dashboard charts render
- [ ] Navigation to sub-pages works

**Admin Tables - `/admin/orders`, `/admin/users`, `/admin/tickets`**
- [ ] Tables load with 25 rows (configurable)
- [ ] Pagination: First, Last, Next, Previous work
- [ ] Search finds matching records
- [ ] Filter by status/category works
- [ ] Sort (ascending/descending) maintains data
- [ ] Bulk select all/page/filtered works
- [ ] Export to CSV generates correct file
- [ ] Row actions (view/edit/delete) trigger modals

**Supplier Panel - `/supplier`**
- [ ] Dashboard loads
- [ ] Products list displays
- [ ] Product add/edit form works
- [ ] Orders tab shows related orders
- [ ] Analytics displays metrics

**Logistics Partner - `/logistics-partner`**
- [ ] Dashboard loads
- [ ] Shipments list displays
- [ ] Status filter works
- [ ] Location map (if applicable) renders
- [ ] Status update modal works

**Mobile Responsive**
- [ ] All panels accessible on mobile
- [ ] Tables collapse to card layout
- [ ] Forms stack properly
- [ ] Buttons easily tappable (≥44px height)
- [ ] No horizontal scroll (except tables)

---

#### **4.2 Visual Regression Testing**
**Baseline Screenshots (run once):**
```bash
npm run test:visual -- --update-snapshots
```

**Ongoing Testing:**
```bash
npm run test:visual
```

**Files to Create:**
- `__tests__/visual/admin-dashboard.test.ts`
- `__tests__/visual/admin-tables.test.ts`
- `__tests__/visual/supplier-dashboard.test.ts`
- `__tests__/visual/logistics-dashboard.test.ts`

---

### **PHASE 5: DOCUMENTATION & DELIVERY**

#### **5.1 Update Master Status File**
**File:** `CODEBASE_STATUS_MATRIX_DETAILED.md`

**Add Rows:**
```markdown
| UI/UX - Admin Dashboard | COMPLETE | V1.0 | Dashboard with density modes | Q4 2024 |
| UI/UX - Data Tables | COMPLETE | V1.0 | Enterprise grid with 1000+ rows | Q4 2024 |
| UI/UX - Forms & Modals | COMPLETE | V1.0 | Consistent styling across panels | Q4 2024 |
| UI/UX - Mobile Responsive | COMPLETE | V1.0 | Tested on breakpoints | Q4 2024 |
| Performance - Lighthouse | VERIFIED | V1.0 | 85+ Performance score | Q4 2024 |
| Testing - E2E Smoke | PASSED | V1.0 | All workflows tested | Q4 2024 |
```

---

#### **5.2 Component Library Documentation**
**Create:** `COMPONENT_LIBRARY.md`

```markdown
## Reusable Components

### DataTable
- **Path:** `frontend/shared/components/EnterpriseDataTable.tsx`
- **Usage:**...
- **Props:** columns, data, densityMode, etc.

### FormField
- **Path:** `frontend/shared/components/FormField.tsx`
- **Variants:** text, select, checkbox, radio

### StatusBadge
- **Path:** `frontend/shared/components/StatusBadge.tsx`
- **Variants:** success, pending, error, info
```

---

### **FINAL CHECKLIST - BEFORE FINAL DEPLOYMENT**

- [ ] All code committed to `main` branch
- [ ] No console errors or warnings in any panel
- [ ] Lighthouse scores ≥85 on all pages
- [ ] E2E smoke tests pass 100%
- [ ] `CODEBASE_STATUS_MATRIX_DETAILED.md` updated
- [ ] New components documented in `COMPONENT_LIBRARY.md`
- [ ] Dark & Light theme fully tested
- [ ] Mobile responsive verified on 4+ device sizes
- [ ] Accessibility audit passed (WAVE, axe DevTools)
- [ ] Code review approved by team lead
- [ ] Deployed and verified on staging environment

---


--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------

## **CRITICAL REQUIREMENTS: Admin, Supplier & Logistics Partner Panels**

**Scope:** Review and implement across `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, and `Database setup`.

---

### **1. Integrated Communication System**
- **Requirement:** Build a unified messaging/ticketing system for Supplier and Logistics Partner communication with Admin
- **Features Required:**
  - Real-time notifications (WebSocket)
  - Message threads and conversation history
  - Priority/urgency levels for inquiries
  - File/document attachment support
- **Quality Standards:** Efficient, secure, scalable, reliable, maintainable, fully documented

### **2. Product Deletion & Cascade Management**
- **Requirement:** Admin deletion of products must remove from entire system
- **Cascade Rules:**
  - Remove from inventory, orders, carts, wishlists
  - Update order statuses if product was pending
  - Archive associated reviews/ratings
  - Notify affected users of unavailable products
- **Audit Trail:** Log all deletion actions with timestamps and admin user ID

### **3. Commission Agreement System**
- **Requirement:** Flexible commission % structure (not fixed, varies by agreement)
- **Two Commission Models:**
  - **Supplier-Based:** Fixed % for all products from a supplier
  - **Product-Based:** Custom % per product within supplier's catalog
- **Optional Enhancement:** Location-wise commission adjustments (needs stakeholder approval)
- **Implementation:** Store in separate agreement table with version history

### **4. Return Policy Management**
- **Requirement:** Product-specific return policies set by suppliers during upload
- **Constraints:**
  - Minimum: 10 days return window
  - Supplier-configurable: Up to maximum allowed days
  - Link to payout timeline based on return window
- **Default:** 10-day return policy if not specified

### **5. Comprehensive Reporting System**
- **Requirement:** Analytics dashboard for Admin, Supplier, and Logistics Partner roles
- **Metrics Required:**
  - Performance KPIs (sales, revenue, conversion rates)
  - Operational metrics (order fulfillment, delivery times)
  - User behavior analytics
  - Commission tracking and payouts
- **Export Capabilities:** PDF, CSV, scheduled reports

---

### **TESTING & DOCUMENTATION**
- **Functional Testing:** Thoroughly test all backend and frontend features post-implementation
- **Documentation Update:** Sync all changes to `CODEBASE_STATUS_MATRIX_DETAILED.md` for project tracking and future reference
- **Code Review:** Ensure maintainability and adherence to project standards 


--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------

1. Supplier Panel :
    - Discount Allowed by the Supplier on the Product to Product and it should be on supplier/product/.
    - Supplier Bank Account Details should be entered in the supplier/profile Page and it should be reflect to the payment management system and also for the payout system of the supplier.
    - Supplier should be able to see the payment status and Payout status in the Supplier panel Payout page and Order page also to verify which order is paid and which order is not paid and also for the payout status to verify which payout is completed and which payout is pending and etc.


- Admin and Supplier Panel:
    - Admin going to charge the commission from the supplier and it is still not yet configure properly.
    - When supplier will send the application to the zozi and there is 2 option for the commission setup.
        1. Supplier Based Commission - in this case the supplier will pay the fixed commission for all the products which is going to be sold from that supplier.
        2. Product Based Commission - in this case the supplier will pay the different commission for different products which is going to be sold from that supplier.
    
- Admin Panel -> Payments gateways - have redesign with removing all unnecessary items and easy to integration for Admin to add new payment gateway and also make it more efficient and scalable.

- Admin Panel -> Finance Page: 
    - Redesign the finance page [remove all the unnecessary widget and reduce the clutter] 
    - Shift the Zozi bank account into [Bank Account Page] and also test and ensure connection of bank is working.
    - I can't understand what is happening in the Finance Page and how ? review properly because it is not undertandable the cycle. 
    - it should be connected with the order place 
        - `Pay by Card` - Order Delivered to Customer -> Collection Received from Customer -> Share of Zozi Admin keep -> Check Payment to Supplier Period -> Payout Sent to Supplier and Logistic Partner Delivery Settlement and Payout Sent to Logistic Partner. Right now nothing is cleared. 
        - `Cash on Delivery` - Order Delivered to Customer -> Collection Received by Logistic Partner {share of VAT + ADMIN Commission + Supplier Share} -> Received to Zozi Keep -> Check Payment to Supplier Period -> Payout Sent to Supplier. Right now nothing is cleared.
        - So make sure to review the complete cycle of the collection and payout system.
        - Bank Verification of Supplier and Logistic Partner is not correctly presented.
    
- Supplier Panel -> Profile Page: will have page to enter the bank account details which will be reflected to the payment management system and also for the payout system of the supplier.

- Logistic Partner Panel -> Profile Page: will have page to enter the bank account details which will be reflected to the payment management system and also for the payout system of the Logistic Partner.

- Right now the Commission Comprehensive system is also in the available which will help to wire with the finance and payout system.

- test complete cycle of the collection and payout system for both `Pay by Card` and `Cash on Delivery` and make sure it is working properly and also make sure it is efficient, secure, scalable, reliable, maintainable and well documented as well.

--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------





Read carefully `backend`, `frontend/web_app`, `frontend/mobile_app`, `frontend/shared`, `backend API`, `Database setup` and list down all the Files and Functions related to the below points and start improvement in detail and make sure all the functions are working properly and also make sure it is efficient, secure, scalable, reliable, maintainable and well documented as well.

## Supplier Panel :

- Discount Allowed by the Supplier on the Product to Product and it should be on supplier/product/.
- Supplier `Bank Account Details` should be entered in the supplier/profile Page and it should be reflect to the payment management system and also for the payout system of the supplier.
- Supplier should be able to see the payment status and Payout status in the Supplier panel Payout page and Order page also to verify which order is paid and which order is not paid and also for the payout status to verify which payout is completed and which payout is pending and etc.

## Logistic Partner Panel :

- Read the supplier/profile Page and tabs of the supplier/profile tab and Implement into Logistic_Partner Panel and profile page properly. 

---

### 🏗️ Functional Flow
1. **Logistic Partner Profile Page** → Add a new tab called **“Delivery Settings.”**  
2. Inside the tab, logistics partners can manage:
- **Country** (where they operate)  
- **Pickup City** + **Pickup Charges**  
- **Delivery City** + **Delivery Charges**  
- **Approval Status** (admin must approve before charges go live)  
- **Action** (edit/delete/update)  

3. When a customer places an order:
- The system checks the supplier’s city and customer’s city.  
- It pulls the **pickup + delivery charges** from the logistics partner’s table.  
- These charges are added to the cart and reflected in the order summary.  

4. In **Order Management System**:
- Each order shows the logistics partner assigned, pickup/delivery charges, and approval status.  
- These values flow into the **payout calculation** for the logistics partner.

---

### 💵 Payout System Integration
- **Data Source:** The charges table you design.  
- **Calculation:**  
- For each completed order → `Pickup Charges + Delivery Charges`.  
- Weekly/Monthly → Sum all completed orders for that partner.  
- **Settlement:** Generate payout statement → push to finance → transfer to partner’s bank.  

---

### 📊 Suggested Table Schema
| Country | Pickup City | Pickup Charges (OMR) | Delivery City | Delivery Charges (OMR) | Action | Approval Status |
|---------|-------------|-----------------------|---------------|-------------------------|--------|-----------------|
| Oman    | Muscat      | 1.500                 | Sohar         | 2.000                   | Edit   | Approved        |
| Oman    | Muscat      | 1.000                 | Nizwa         | 2.500                   | Edit   | Pending         |

---

### ⚙️ Design Notes
- **Approval Workflow:** Admin must approve new charges before they affect customer carts.  
- **Audit Trail:** Log who updated charges and when.  
- **Flexibility:** Allow partners to set multiple city pairs (Muscat → Sohar, Muscat → Nizwa, etc.).  
- **API Hook:** Cart system queries this table in real time to calculate delivery fees.  

---
---


- Logistic Partner Bank Account Details should be entered in the Logistic Partner Panel at Profile Page and it should be reflect to the payment management system and also for the payout system of the Logistic Partner.

- Logistic Partner should be able to see the payment status and Payout status in the Logistic Partner panel Payout page and Order page also to verify which order is paid and which order is not paid and also for the payout status to verify which payout is completed and which payout is pending and etc.


Cash on Delivery System : 
    Customer         -> Logistic Partner 
    Logistic Partner -> Admin Management
    Admin Management -> Supplier

Pay by Card System : 
    Customer         -> Admin Management
    Admin Management -> Supplier
    Admin Management -> Logistic Partner

    Parties         |  Particular                 | Product/Services    | VAT (5%)    | Payment Gateway (2.5%) | Total Charges
    Supplier        | (Product cost)              | OMR 3.000           | OMR 0.1500  | OMR 0.0787             | OMR 3.2250
    Logistic Partner| (Pickup + Delivery Charges) | OMR 1.750           | OMR 0.0875  | OMR 0.0438             | OMR 1.8813
    Admin Management| (Zozi Service Charges 15%)  | OMR 0.450           | OMR 0.0225  | OMR 0.0113             | OMR 0.4840
    Total           |                             | OMR 5.200           | OMR 0.2600  | OMR 0.1301             | OMR 5.5901

    Customer will pay total OMR 5.5901



# Supplier Payout System:
    - when the order is delivered and completed - after 10 days of the order completion the payment will be automatically transfer to the supplier bank account and also reflect in the supplier panel payout page and order page for the payment status and payout status. in both cases of `Cash on Delivery` and `Pay by Card` - Admin have to give to 

    - 


--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------


---

## 📝 Prompt for AI Development

**Objective:**  
Upgrade the Admin Panel with a **Payment Gateway Management Page** that is gateway‑agnostic, allowing connection to multiple providers (Stripe, Tap, PayTabs, HyperPay, OmanNet, PayPal, etc.), sandbox testing, and automatic reflection of charges in the frontend cart, order management, and payout system.

---

### 🔑 Functional Requirements
1. **Gateway Configuration Tab**
   - Dropdown: Select Gateway Provider (Stripe, Tap, PayTabs, HyperPay, OmanNet, PayPal, Custom).  
   - Fields: API Key, Secret Key, Merchant ID, Endpoint URL, Currency, Mode (Sandbox/Live).  
   - Save credentials securely (encrypted storage).  
   - Test Connection button → sends a dummy request to gateway sandbox and logs response.

2. **Charges & Fees**
   - Admin can define transaction fee % and/or flat fee per gateway.  
   - These fees are automatically added to customer checkout totals.  
   - Formula:  
     \[
     \text{Total Payable} = \text{Order Value} + \text{Delivery Charges} + \text{Gateway Fee}
     \]

3. **Frontend Checkout Integration**
   - When customer places an order, system queries active gateway settings.  
   - Displays final payable amount including delivery + gateway fee.  
   - Processes payment via selected gateway adapter.  
   - Returns transaction status (Success/Failure/Pending).

4. **Order Management System**
   - Logs gateway used, transaction ID, fees applied, and net revenue.  
   - Links charges to supplier and logistics partner payout records.

5. **Payout System**
   - Supplier payout = Order Value – Commission – Gateway Fee.  
   - Logistics partner payout = Pickup + Delivery Charges.  
   - Gateway fee deducted automatically.  
   - ZoZi retains commission margin.  
   - Settlement cycle configurable (daily/weekly/monthly).

---

### ⚙️ Technical Design
- **Generic Adapter Interface (`PaymentAdapter`)**  
  - Methods: `authorizePayment()`, `capturePayment()`, `refundPayment()`, `testConnection()`.  
  - Each gateway implements this interface with its own API logic.  
- **Database Schema**  
  - `Gateways`: provider, credentials, fees, mode.  
  - `Orders`: order_id, gateway_id, transaction_id, total, fees.  
  - `Payouts`: supplier_id, logistics_id, net_amount, settlement_status.  
- **Logs & Monitoring**  
  - Store test results, transaction errors, and settlement reports.  
  - Admin can view history of gateway connections and payouts.

---

### 🚀 Deliverables
- Admin Panel Payment Page with gateway‑agnostic configuration.  
- Sandbox testing capability for any gateway.  
- Automatic fee reflection in frontend checkout.  
- Integrated payout system for suppliers and logistics partners.  
- Secure credential storage and audit logs.

---

👉 a **clear blueprint**: build a modular Payment Page that supports *any* gateway, not just Stripe or Tap, and ties charges seamlessly into the cart, order, and payout flows.

---



--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------

- read the `frontend/shared` in detail and shift all the files and codes into properly `frontend/web_app` and `frontend/mobile_app` becasue keep shared folder is looking like use 

- do one final full-stack smoke run through Docker Compose or the Windows launchers to confirm the whole repo starts cleanly end to end.

Maintainability