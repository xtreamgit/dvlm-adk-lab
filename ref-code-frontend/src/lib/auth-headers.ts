/**
 * Shared auth headers utility for admin pages and direct fetch calls.
 * Authentication is handled by Google IAP — the load balancer injects
 * X-Goog-IAP-JWT-Assertion automatically. No Bearer token needed.
 * 
 * All fetch calls should use credentials: 'include' to send IAP cookies.
 */

/**
 * Get headers for API requests.
 * IAP authentication is handled by the load balancer automatically.
 */
export function getAuthHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
  };
}

/**
 * Get headers without Content-Type (for non-JSON requests).
 */
export function getAuthHeadersOnly(): Record<string, string> {
  return {};
}
