# System Requirements Specification: Golden Order Management

## SPEC-AUTH-001: Authentication
Given an active user with valid credentials, when submitted, the system authenticates the user and displays the dashboard.

## SPEC-ORDER-001: Order Creation (Happy Path)
Given an active user, when valid order details (item name, quantity >= 1, unit price > 0) are submitted, the system creates the order and returns HTTP 201 with an order confirmation ID.

## SPEC-ORDER-GUARD: Validation Constraint (Security Guard)
The system must reject any order submission containing quantity <= 0 or missing item details. The user interface must display an inline validation warning and disable the submit button. The backend API must return HTTP 400 Bad Request.

## SPEC-ORDER-002: Discount Limit Enforcement
The maximum allowable promo discount on any order is 50%. Any order claiming a higher discount percentage or negative net total must be strictly rejected by both UI and backend API.
