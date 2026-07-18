



# Prompt - DISCOUNT SYSTEM | PROMOTIONS | FLASH SALES | SUPPLIER DISCOUNTS:

Read the below carefully and start implementation and test and run to ensure everything is integrated properly and running smoothly and also ensure that there should not be any hardcoded fallback which will block the actual functionality. 

After implementation update regarding implementation, integration and test into 
documents\CODEBASE_STATUS_MATRIX_DETAILED.md - `🎯 Component/Feature Status Matrix`

---

## Flash-Sales | Supplier Discounts | Promotions :-

There is 3 kind i told you 
1. Discounts which allowed by the Supplier on Product to Product which badge shoud be `Lime Green` 
2. Flash Sales which allowed by the Zozi Admin which is same Discounts thing but from Zozi on Product to Product which badge shoud be `Yellow`
3. Promotion/Deals which allowed by the Zozi Admin or Supplier both which is like buy `one get one free` or `bundle offer` which badge shoud be `Red`

and right now I can't see any badge even flash-sales is runing from all product by Zozi Admin 


- Flash Sales badge is not coming on the product and calculation of prices is also not reflecting with stricker on original price and showing new price. check the pasted image.
- All product-card should be reflect the discounted price and badge also of Flash-Sales like as I given you example Pasted Image.
- Admin just open the Flash Deal but it is not impacted on web_app and mobile_app.
- Check all the `web_app`, `backend`, `mobile_app` and fix it. 
- I marked in the Image pasted.
- `Flash Sales`, `Promotional Offers` should be announce by the admin and it should to show duration also.
- `Supplier Discounts` can be offer by the individual Supplier also and it should to show duration also.
- Please check all the code properly and connect backend to frontend and remove all the hardcode.



- Flash Sales badge is not coming on the product and calculation of prices is also not reflecting with stricker on original price and showing new price. check the pasted image.


- Admin just open the Flash Deal but it is not impacted on web_app and mobile_app.
- Check all the `web_app`, `backend`, `mobile_app` and fix it. 
- I marked in the Image pasted.
- `Flash Sales`, `Promotional Offers` should be announce by the admin and it should to show duration also.
- `Supplier Discounts` can be offer by the individual Supplier also and it should to show duration also.
- Please check all the code properly and connect backend to frontend and remove all the hardcode.

---

- Banner will also have 3 Slots for | Discounts | Flash-Sales | Promotion | as i marked into Banner into pasted image which should be flash if Admin alowed banner to run,

---

- Implement into both mobile_app and web_app properly and check also.
- After finishing implementation, test everything in detail to conclude it is done.

---




-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------





# Prompt - ORDER TRACKER | ORDER MANAGEMENT:

Read the below carefully and start implementation and test and run to ensure everything is integrated properly and running smoothly and also ensure that there should not be any hardcoded fallback which will block the actual functionality. 

---

## `Oder Tracker` | `Order Management` required in Customer, Admin, Supplier, Logistic Partner | Panels 

- Order Tracker is one of the most tricky and important part of this project.
- Customer Place Order.
- it will imtimate to Supplier and Supplier arrange and make ready. 
- Logistic Partner will take the order from supplier. 
- Logistic Partner will deliver to same customer.
- Customer will receive same order.

-- in this complete process there is 2 major problem will arise [1. Who will handle the Packaging and How ?] [2. How the exact same Order is passing the hands ? ]
- this order tracking can be handle by 2 ways [First is QR Code] but the QR Code can be handle Package Manager.

- if there is status of order placed by Supplier and Logistic party wrong then Admin should to modify that.
- if customer placed wrong order and want want to cancel the order then ofcouse admin can cancel the order also.

1. When supplier will proceesing the packaging, supplier need `print of paper` and that should be show into `supplier oder page` with order details

2. When supplier will complete processing part supplier uploads the photo for packed parcel for confirmation to `ship` and the status of the order should be change with `prepared` and that should to show into logistic partner pages for `pick-up`.

3. When the Supplier-Order status become `prepared`, it should to show in the logistic partner shipment area shows that for `pick-up`. 

4. if anyone logistic partner will confirm that he is picking up then it should to show `picking-up' in the Supplier-Order page, Customer-My Orders page, Admin-Order Page and when the status of Order become `Picking-Up` then it should to remove from all Logistic Partner Pages other then the logistic partner who confirm for picking up.

5. Logistic Partner can cancel also the `Picking-Up` for any reason but before `shipped` status of the `Order`

6. Logistic Partner can will scan the QR code of the order by app when he will be receiving the parcel from supplier and that time status of the Order become `Picked From Supplier` and that should to show in the Supplier-Order page, Customer-My Orders page, Admin-Order Page and when the status of Order become `Picked From Supplier`. 

7. After that Logistic Partner will deliver to customer and take the e-signature from the customer on the app page for verification that parcel is delivered to customer and the order status become `Delivered` and that should to show in the Supplier-Order page, Customer-My Orders page, Admin-Order Page and when the status of Order become `Delivered`.

8. Logistic Partner can change the following status of order only after status `Picked From Supplier` and before status `Delivered`: 
      - `Logistic Received` when Logistic Partner from rider.
      - `Distritution Checkpoint` when Logistic Partner reach to distribution center.
      - `Out for Delivery` when Logistic Partner out for delivery to customer.
      - `Shipment Delayed` when Logistic Partner face any problem in delivery.
      - `Shipment Failed` when Logistic Partner face any problem in delivery and he want to cancel the order.
      - `Shipment Rescheduled` when Logistic Partner want to reschedule the delivery of order.
      - `Shipment Cancelled` when Logistic Partner want to cancel the order - but for that he have to retrun to supplier and then cancel the order that is also a process which should to show in the Supplier-Order page, Customer-My Orders page, Admin-Order Page and when the status of Order become `Shipment Cancelled` then it should to show in the Supplier-Order page, Customer-My Orders page, Admin-Order Page.
      - `Shipment Returned` when Customer reject the order and want to return the order to supplier and then cancel the order that is also a process which should to show in the Supplier-Order page, Customer-My Orders page, Admin-Order Page and when the status of Order become `Shipment Returned` then it should to show in the Supplier-Order page, Customer-My Orders page, Admin-Order Page.
      
9. in middle of the process if there is any problem with the order then customer can cancel the order and that should to show in the Supplier-Order page, Customer-My Orders page, Admin-Order Page and when the status of Order become `Cancelled` and that should to show in the Supplier-Order page, Customer-My Orders page, Admin-Order Page.


one more point customer orders must be visible to Supplier | Logistic | Admin | and ofcouse Customer also.

---

## 🧩 Core Challenges
1. **Packaging Responsibility**
   - Who prepares the package? Supplier or a centralized packaging hub?
   - Packaging must be standardized (tamper‑proof, labeled, QR‑coded).

2. **Order Identity Across Hands**
   - The same order must be traceable as it moves from Supplier → Logistic Partner → Customer.
   - Prevent mix‑ups, fraud, or “lost in transit” excuses.

---

## 📦 Solution Design

### 1. **Unified Order ID + QR Code**
- Every order gets a **unique Order ID** + **QR code** generated at placement.
- QR code is printed/attached to the package.
- Scanning the QR at each handover updates the **Order Tracker timeline**.

### 2. **Packaging Flow**
- **Supplier handles packaging** (default, fastest).
- Packaging rules enforced:
  - Tamper‑proof seal
  - QR code label
  - Optional: weight + dimensions logged
- If you want more control later → introduce **Packaging Manager role** (centralized hub).

### 3. **Tracking Timeline**
Each stage is logged in the database:
- **Customer Panel**: “Order Placed → Supplier Preparing → Logistic Picked Up → Out for Delivery → Delivered”
- **Supplier Panel**: “Order Received → Packaged → Handed to Logistic”
- **Logistic Panel**: “Picked Up → In Transit → Delivered”
- **Admin Panel**: Full visibility across all orders.

### 4. **Database Schema Additions**
- `OrderStatus` table or enum:
  - `PLACED`, `PACKAGED`, `PICKED_UP`, `IN_TRANSIT`, `DELIVERED`
- `OrderTrackingEvent` table:
  - `id`, `order_id`, `actor_role` (supplier/logistic/admin), `timestamp`, `status`, `location`, `notes`
- `Package` table (optional):
  - `order_id`, `qr_code`, `weight`, `dimensions`, `packaged_by`

### 5. **Panel Integration**
- **Customer**: Timeline view + live status.
- **Supplier**: Orders awaiting packaging, QR generation, handover logs.
- **Logistic Partner**: Scan QR → update status → GPS tracking.
- **Admin**: Dashboard with filters (pending, delayed, delivered).

---

## ⚡ Workflow Example
1. Customer places order → `OrderStatus = PLACED`.
2. Supplier packages → QR code generated → `OrderStatus = PACKAGED`.
3. Logistic scans QR at pickup → `OrderStatus = PICKED_UP`.
4. Logistic updates transit → `OrderStatus = IN_TRANSIT`.
5. Customer receives package → QR scanned → `OrderStatus = DELIVERED`.

---

## ✅ Benefits
- **Transparency**: All parties see the same timeline.
- **Accountability**: Every handover is logged with QR scan.
- **Scalability**: Works for single supplier or multi‑supplier marketplace.
- **Dispute Resolution**: Admin can trace exactly where delays or issues occurred.

---

## Printing Material:
There must be a printing Flow for Supplier for Order-Details. Supplier will print a paper from system to attach with the parcel simple which will reduce the time. It will have 
        Customer Name: 
        Customer Contact Number:
        Customer Location and Location Longitude and Latitude:
        Customer Order Items List:
        Customer Invoice:
        Customer Order Number:
        Customer QR code:
        and some more important information

---

- continue directly with the next backend slice: package metadata persistence plus a first-class label payload endpoint. Completed the current implementation slice: shipment-reconciled order tracking is live across backend, customer web/mobile, and shared admin/supplier/logistics web panels; supplier parcel-sheet printing with real QR generation was added; targeted tests, lint, and diagnostics passed, and the status matrix was updated with the verified implementation and validation notes.

- Check the Admin Panel, Supplier Panel, Logistic Panel, I didn't see any changes which is showing as above discussed regarding order tracking.

- Please test each and everything from end to end becasue this is most important part of this application, all the business model will stand on this. and all the revenue will come from this.

- next thing is that you have consider the returns and replacement system also as you know it is part of orders and order tracking.

---

- Implement into both mobile_app and web_app properly and check also.
- After finishing implementation, `test` everything in detail to conclude it is done.
- After implementation update regarding implementation, integration and test into 
documents\CODEBASE_STATUS_MATRIX_DETAILED.md according to the status matrix format section to section but after finishing the implementation and testing of whole order tracking system.

---


-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------


---

# Prompt - Supplier About | Supplier Product.

## Implementation - Supplier About | Supplier Product.

Read the below carefully and start implementation and test and run to ensure everything is integrated properly and running smoothly and also ensure that there should not be any hardcoded fallback which will block the actual functionality. 

---

 - Implementation of Supplier About | Supplier Product

- Have to make customer friendly supplier about and supplier product description which will be visible to customer on product details page and also on supplier details page, it will be like a supplier website but in our system and it will be visible to customer, it will have all the details regarding supplier and also about the product which supplier is selling. 
- this way customer can know about the supplier and also about the product which supplier is selling and it will increase the trust of customer on supplier and also on our system.
	- Supplier About Us, 
	- Supplier Product Card of Individual Supplier 
	- Supplier Video, Supplier 
	- Contact Details, 
	- Supplier Certifications, 
	- Chat with the Supplier + Customer but without sharing any personal information.
	- Supplier Ratings and Reviews, 
	- some more important information which will be visible to customer on supplier details page. 

---
- Implement into both mobile_app and web_app properly and check also.
- After finishing implementation, `test` everything in detail to conclude it is done.
- After implementation update regarding implementation, integration and test into 
documents\CODEBASE_STATUS_MATRIX_DETAILED.md according to the status matrix format section to section but after finishing the implementation and testing of whole order tracking system.

---


-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------


---

# Prompt - Supplier About | Supplier Product.

Read the below carefully and start implementation and test and run to ensure everything is integrated properly and running smoothly and also ensure that there should not be any hardcoded fallback which will block the actual functionality. 

---

## Implementation of Supplier `Payment System` | `Term of Payout` | `Verification System` | `Terms and Condition` | `sharing the %` | `Time for payout` and etc.


- Every Supplier Have different product and every product have different profit margin, some supplier will work with Zozi in `Profit Margin % Sharing`, `Selling Price + Zozi Commission %`.
- Additional we have to think about Logistic Matter so, how it will be work ?, what will be the business model ?
- What is your suggestion for this ? Should we keep system flexible or Hard rule ? or what ?

---


-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------

# Implementation & Correction - Database Optimization | Caching | Performance Improvement

1. there is 3 database setup which is `SQLite`, `PostgreSQL`, `Redis` and we are using all three database in our system but we have to optimize the database queries and also we have to implement caching system to improve the performance of our system.
2. We have to optimize the database queries and also we have to implement caching system to improve the performance of our system and caching.
3. Database backup and recovery system also we have to implement to ensure the data safety and security, which we have some code and files in the directory which should be download data for backup and recovery system management by the Admin Panel by clicking buttons.
4. right now, we are having problem for login/registration system and product details and pictures are also not coming properly, so clear all the data and optimize the database and give Admin Panel Login for arranging things.
5. You must have to read all the database setup and tables and each and every system which is connected to database and optimize the database queries.
6. Make a Complete and Proper list of Todos before taking any action and then start implementation and after finishing implementation, test everything in detail to conclude it is done.





-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------


# Supplier - Product Management Page

1. Upload of Photos and Videos is not allowed for more then one profuct at a time.
2. When AI runs it should to check the color of product also and fill the `Color` field in product and it should to check all the uploaded photos and videos and fill the `Color` field in product details page and also it should to check the category of product and fill the `Category` field in product details page.
3. When Supplier upload the product then it should to show the product details page with all the details and also it should to show the product in the product listing page and also in the supplier details page.
4. When Supplier upload the product then it should to show the product details page with all the details and also it should to show the product in the product listing page and also in the supplier details page and also it should to show the product in the customer details page and also it should to show the product in the home page and also it should to show the product in the search results page.
5. Selection of size is also not working properly. 
6. Price is come in both $ (AED) and this not correct becasue Supplier is based in OMAN, and it should be show in (OMR).






-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------

## Implementation of Logistic Partner System | Profile Page | aera to aera delivery charges Mapping | Logistic Partner Registration.

Read the below carefully and start implementation and test and run to ensure everything is integrated properly and running smoothly and also ensure that there should not be any hardcoded fallback which will block the actual functionality. 

1. Right Now, 





