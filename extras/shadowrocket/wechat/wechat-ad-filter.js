/*
 * WeChat AdBlock response filter, version 1.0.0 (2026-10-02).
 * Original implementation, licensed under the repository's MIT license.
 * Supports only the exact HTTPS/HTTP interfaces listed in SOURCES.md.
 * No network calls, credentials, request modifications or MMTLS handling.
 * Unknown response formats are returned unchanged through $done({}).
 */
(function () {
  "use strict";

  var MAX_BODY_LENGTH = 1048576;
  var own = Object.prototype.hasOwnProperty;

  function isObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function routeFor(url) {
    if (typeof url !== "string") return "";
    if (/^https?:\/\/mp\.weixin\.qq\.com\/mp\/getappmsgad(?:\?|$)/.test(url)) {
      return "article";
    }
    if (/^https?:\/\/(?:webapi|miniapp)\.qmai\.cn\/web\/catering(?:[0-9]-apiserver)?\/advertising\/ad\/advertiseInfo(?:\?|$)/.test(url)) {
      return "qmai";
    }
    if (/^https?:\/\/rms\.meituan\.com\/api\/v\d+\/rmsmina\/c\/queryPortalInfo(?:\?|$)/.test(url)) {
      return "meituan";
    }
    return "";
  }

  function headerValue(headers, name) {
    if (!isObject(headers)) return "";
    var keys = Object.keys(headers);
    for (var i = 0; i < keys.length; i++) {
      if (keys[i].toLowerCase() === name) return String(headers[keys[i]]);
    }
    return "";
  }

  function hasError(payload) {
    var containers = [payload, payload.base_resp];
    for (var i = 0; i < containers.length; i++) {
      if (!isObject(containers[i])) continue;
      if (own.call(containers[i], "ret") && String(containers[i].ret) !== "0") {
        return true;
      }
    }
    return false;
  }

  function clearArticleAds(payload) {
    // Do not invent a new schema if the known array is absent or has changed type.
    if (!own.call(payload, "advertisement_info") || !Array.isArray(payload.advertisement_info)) {
      return false;
    }
    if (payload.advertisement_info.length === 0 && payload.advertisement_num === 0) {
      return false;
    }
    payload.advertisement_info = [];
    payload.advertisement_num = 0;
    // appid, base_resp, reading counts, comments and every other field are kept.
    return true;
  }

  function clearQmaiAds(payload) {
    // This is a dedicated advertising endpoint, not an ordering/homepage endpoint.
    if (!Array.isArray(payload.data) || payload.data.length === 0) return false;
    // Keep unknown elements; recognize the advertising schema by detailInfo.
    var remaining = payload.data.filter(function (item) {
      return !isObject(item) || !isObject(item.detailInfo);
    });
    if (remaining.length === payload.data.length) return false;
    payload.data = remaining;
    return true;
  }

  function clearMeituanAds(payload) {
    // Preserve navigation, products, order controls and unknown module shapes.
    if (!isObject(payload.data) || !Array.isArray(payload.data.modules)) return false;
    var modules = payload.data.modules;
    var remaining = modules.filter(function (item) {
      if (!isObject(item)) return true;
      return item.name !== "float-window" && !(isObject(item.data) && item.data.advType === true);
    });
    if (remaining.length === modules.length) return false;
    payload.data.modules = remaining;
    return true;
  }

  function rewriteResponseHeaders(headers) {
    if (!isObject(headers)) return null;
    var output = {};
    Object.keys(headers).forEach(function (key) {
      // The new body is plain text; old size/compression/hash metadata is stale.
      var name = key.toLowerCase();
      if (name !== "content-length" && name !== "content-encoding" &&
          name !== "content-md5" && name !== "etag" && name !== "digest") {
        Object.defineProperty(output, key, {
          value: headers[key], enumerable: true, writable: true, configurable: true
        });
      }
    });
    return output;
  }

  function filterResponse(request, response) {
    try {
      if (!isObject(request) || !isObject(response)) return {};
      if (request.method && !/^(GET|POST)$/i.test(request.method)) return {};
      var route = routeFor(request.url);
      if (!route || typeof response.body !== "string" || !response.body ||
          response.body.length > MAX_BODY_LENGTH) return {};

      var status = response.statusCode || response.status;
      if (typeof status === "string") {
        var match = status.match(/(?:^|\s)(\d{3})(?:\s|$)/);
        status = match ? Number(match[1]) : 0;
      }
      if (typeof status === "number" && status >= 400) return {};
      var contentType = headerValue(response.headers, "content-type");
      if (/^(?:image\/|audio\/|video\/|multipart\/|application\/(?:octet-stream|(?:x-)?protobuf))/i.test(contentType)) {
        return {};
      }

      var body = response.body.replace(/^\uFEFF/, "");
      if (!/^\s*\{/.test(body)) return {};
      var payload = JSON.parse(body);
      if (!isObject(payload) || hasError(payload)) return {};

      var changed = false;
      if (route === "article") changed = clearArticleAds(payload);
      else if (route === "qmai") changed = clearQmaiAds(payload);
      else if (route === "meituan") changed = clearMeituanAds(payload);
      if (!changed) return {};

      var result = { body: JSON.stringify(payload) };
      var headers = rewriteResponseHeaders(response.headers);
      if (headers) result.headers = headers;
      return result;
    } catch (_) {
      // Missing, malformed, encrypted, compressed or changed schemas fail open.
      return {};
    }
  }

  if (typeof $done === "function") {
    var result = {};
    try {
      result = filterResponse(
        typeof $request !== "undefined" ? $request : null,
        typeof $response !== "undefined" ? $response : null
      );
    } catch (_) { result = {}; }
    $done(result);
  } else if (typeof module !== "undefined" && module.exports) {
    module.exports = { filterResponse: filterResponse, routeFor: routeFor };
  }
})();
