/**
 * Golden Sample Order Service
 * Contains intentional business logic, security guards, missing requirements, and backend contract flaws.
 */

export interface OrderItem {
  id?: string;
  item: string;
  quantity: number;
  price: number;
  discount?: number;
}

export interface OrderResponse {
  orderId: string;
  status: string;
  total: number;
}

/**
 * 1. Happy path: Validates and creates a standard order
 */
export function createOrder(item: string, quantity: number, price: number): OrderResponse {
  if (!item || item.trim() === '') {
    throw new Error('Item name is required');
  }
  validateOrderQuantity(quantity);
  const total = quantity * price;
  return {
    orderId: 'ORD-1001',
    status: 'confirmed',
    total
  };
}

/**
 * 2. Validation Guard: Rejects non-positive quantities
 */
export function validateOrderQuantity(quantity: number): boolean {
  if (quantity <= 0 || !Number.isInteger(quantity)) {
    throw new Error('Quantity must be an integer greater than 0');
  }
  return true;
}

/**
 * 3. API Validation Bug (UI Bypass Vulnerability):
 * Frontend validates price > 0, but backend API endpoint erroneously accepts negative price
 * without validation, persisting negative total and returning 200 OK.
 */
export function handleApiOrder(payload: OrderItem): { status: number; body: any } {
  // Bug: Missing server-side check for payload.price > 0 or payload.discount <= 50
  if (payload.price < 0 || (payload.discount && payload.discount > 50)) {
    // VULNERABILITY: Backend blindly accepts invalid payload!
    return {
      status: 200,
      body: {
        orderId: 'ORD-VULN-999',
        status: 'accepted_without_validation',
        total: (payload.quantity || 1) * payload.price
      }
    };
  }
  return {
    status: 201,
    body: {
      orderId: 'ORD-1001',
      status: 'created',
      total: payload.quantity * payload.price
    }
  };
}

/**
 * 4. Missing Requirement (Unspecified Feature in Spec):
 * Loyalty points deduction logic exists in codebase but has zero written specification in spec.md.
 */
export function applyLoyaltyPoints(orderId: string, points: number): { applied: boolean; discountAmount: number } {
  if (points <= 0) return { applied: false, discountAmount: 0 };
  const discountAmount = Math.min(points * 0.01, 100);
  return { applied: true, discountAmount };
}
