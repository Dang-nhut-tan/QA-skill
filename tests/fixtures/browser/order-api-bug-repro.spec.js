import { test, expect } from '@playwright/test';
import { handleApiOrder } from '../golden-sample-project/src/order.ts';

/**
 * Bug Reproduction Spec: GAP-API-002
 * Reproduces real API vulnerability: Backend accepts negative price payload without server-side validation.
 */
test('GAP-API-002: reproduces backend accepting negative price without validation', async () => {
  // 1. Prepare invalid payload (price < 0) that frontend validation would normally block
  const payload = {
    item: 'Malicious Item',
    quantity: 1,
    price: -500,
  };

  // 2. Dispatch to backend order handler (bypassing UI)
  const response = handleApiOrder(payload);

  // 3. Assert Bug is Confirmed:
  // A secure backend must return 400 Bad Request.
  // Vulnerable backend incorrectly returns 200 OK.
  expect(response.status, 'GAP Confirmed: Backend accepted negative price payload!').toBe(200);
  expect(response.body.status).toBe('accepted_without_validation');
  expect(response.body.total).toBe(-500);
});
