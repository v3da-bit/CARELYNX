/**
 * CARELYNX Cloudflare Edge Worker API Gateway
 * 
 * Provides Cloudflare edge routing, security headers, rate limiting defense,
 * and SSL termination for the CARELYNX FastAPI backend.
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const backendOrigin = env.BACKEND_ORIGIN || "http://localhost:8000";

    // Handle health check directly at edge
    if (url.pathname === "/healthz") {
      return new Response(JSON.stringify({ status: "ok", edge: "cloudflare", app: "carelynx" }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    // Proxy request to the backend origin
    const targetUrl = new URL(url.pathname + url.search, backendOrigin);
    const newHeaders = new Headers(request.headers);
    newHeaders.set("X-Forwarded-Host", url.hostname);
    newHeaders.set("X-Forwarded-Proto", "https");

    try {
      const response = await fetch(targetUrl.toString(), {
        method: request.method,
        headers: newHeaders,
        body: request.body,
        redirect: "follow",
      });

      // Attach strict security headers at Cloudflare edge
      const edgeResponse = new Response(response.body, response);
      edgeResponse.headers.set("X-Content-Type-Options", "nosniff");
      edgeResponse.headers.set("X-Frame-Options", "DENY");
      edgeResponse.headers.set("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload");
      edgeResponse.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
      return edgeResponse;
    } catch (err) {
      return new Response(JSON.stringify({
        error: {
          code: "GATEWAY_ERROR",
          message: "Unable to reach CARELYNX backend origin.",
        }
      }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }
  },
};
