/*
 * TikTok Network Privacy Guard for Shadowrocket
 *
 * Removes explicit SIM, carrier, advertising-ID, and precise-location fields
 * from unsigned text requests. Requests carrying known TikTok signature headers
 * are left untouched to avoid invalidating authentication and request integrity.
 * Binary, multipart, and compressed bodies are not modified.
 */

(function () {
  "use strict";

  var request = typeof $request === "object" && $request ? $request : {};
  var originalUrl = typeof request.url === "string" ? request.url : "";
  var originalHeaders = request.headers && typeof request.headers === "object"
    ? request.headers
    : {};
  var originalBody = typeof request.body === "string" ? request.body : null;

  var sensitiveKeys = {
    carrier: true,
    carrier_code: true,
    carrier_country: true,
    carrier_id: true,
    carrier_name: true,
    carrier_region: true,
    carrier_region_v2: true,
    cellular_country_code: true,
    cellular_network_code: true,
    iccid: true,
    imsi: true,
    mcc: true,
    mcc_mnc: true,
    mnc: true,
    mobile_country_code: true,
    mobile_network_code: true,
    network_operator: true,
    network_operator_name: true,
    op_region: true,
    operator_name: true,
    operator_region: true,
    radio_access_technology: true,
    sim_country: true,
    sim_country_iso: true,
    sim_operator: true,
    sim_operator_name: true,
    sim_region: true,
    sim_serial_number: true,
    sim_state: true,
    telephony_carrier: true,

    advertising_id: true,
    gps_adid: true,
    idfa: true,
    limit_ad_tracking: true,

    gps_latitude: true,
    gps_longitude: true,
    latitude: true,
    location_latitude: true,
    location_longitude: true,
    longitude: true,
    precise_location: true
  };

  var signatureHeaders = {
    "x-argus": true,
    "x-gorgon": true,
    "x-helios": true,
    "x-khronos": true,
    "x-ladon": true,
    "x-medusa": true,
    "x-ss-stub": true
  };

  function safeDecode(value) {
    try {
      return decodeURIComponent(String(value).replace(/\+/g, " "));
    } catch (_) {
      return String(value);
    }
  }

  function canonicalKey(value) {
    return safeDecode(value)
      .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
      .replace(/[^A-Za-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .toLowerCase();
  }

  function isSensitiveKey(value) {
    var key = canonicalKey(value);

    if (sensitiveKeys[key]) {
      return true;
    }

    if (/^(?:sim|carrier|telephony|cellular)_(?:info|data|details|metadata)$/.test(key)) {
      return true;
    }

    return /^(?:sim|carrier|telephony|cellular)_(?:country|region|operator|network|identifier|id|code|name)(?:_|$)/.test(key);
  }

  function hasSignature(headers) {
    var names = Object.keys(headers);
    for (var index = 0; index < names.length; index += 1) {
      if (signatureHeaders[String(names[index]).toLowerCase()]) {
        return true;
      }
    }
    return false;
  }

  function getHeader(headers, expectedName) {
    var target = expectedName.toLowerCase();
    var names = Object.keys(headers);

    for (var index = 0; index < names.length; index += 1) {
      if (String(names[index]).toLowerCase() === target) {
        return String(headers[names[index]] || "");
      }
    }

    return "";
  }

  function deleteHeader(headers, expectedName) {
    var target = expectedName.toLowerCase();
    var names = Object.keys(headers);
    var changed = false;

    for (var index = 0; index < names.length; index += 1) {
      if (String(names[index]).toLowerCase() === target) {
        delete headers[names[index]];
        changed = true;
      }
    }

    return changed;
  }

  function isSensitiveHeader(name) {
    var normalized = String(name).toLowerCase();

    if (
      normalized === "client-ip" ||
      normalized === "forwarded" ||
      normalized === "true-client-ip" ||
      normalized === "x-forwarded-for" ||
      normalized === "x-real-ip"
    ) {
      return true;
    }

    return /^(?:x-)?(?:sim|carrier|mcc|mnc|telephony|cellular)(?:-|_)/.test(normalized) ||
      /^x-[a-z0-9]+-(?:sim|carrier|mcc|mnc|telephony|cellular)(?:-|_)/.test(normalized);
  }

  function scrubHeaders(source) {
    var headers = {};
    var changed = false;

    Object.keys(source).forEach(function (name) {
      if (isSensitiveHeader(name)) {
        changed = true;
        return;
      }
      headers[name] = source[name];
    });

    return { value: headers, changed: changed };
  }

  function scrubObject(value, depth, state) {
    if (!value || depth > 12) {
      return;
    }

    if (Array.isArray(value)) {
      value.forEach(function (item) {
        scrubObject(item, depth + 1, state);
      });
      return;
    }

    if (typeof value !== "object") {
      return;
    }

    Object.keys(value).forEach(function (key) {
      if (isSensitiveKey(key)) {
        delete value[key];
        state.changed = true;
        return;
      }
      scrubObject(value[key], depth + 1, state);
    });
  }

  function scrubJsonText(text) {
    try {
      var parsed = JSON.parse(text);
      var state = { changed: false };
      scrubObject(parsed, 0, state);
      return state.changed
        ? { value: JSON.stringify(parsed), changed: true }
        : { value: text, changed: false };
    } catch (_) {
      return { value: text, changed: false };
    }
  }

  function scrubEncodedPairs(text) {
    if (!text) {
      return { value: text, changed: false };
    }

    var changed = false;
    var kept = [];

    text.split("&").forEach(function (pair) {
      var separator = pair.indexOf("=");
      var rawKey = separator >= 0 ? pair.slice(0, separator) : pair;
      var rawValue = separator >= 0 ? pair.slice(separator + 1) : "";

      if (isSensitiveKey(rawKey)) {
        changed = true;
        return;
      }

      var decodedValue = safeDecode(rawValue).trim();
      if (decodedValue.charAt(0) === "{" || decodedValue.charAt(0) === "[") {
        var nested = scrubJsonText(decodedValue);
        if (nested.changed) {
          kept.push(rawKey + "=" + encodeURIComponent(nested.value));
          changed = true;
          return;
        }
      }

      kept.push(pair);
    });

    return { value: kept.join("&"), changed: changed };
  }

  function scrubUrl(url) {
    var hashIndex = url.indexOf("#");
    var hash = hashIndex >= 0 ? url.slice(hashIndex) : "";
    var withoutHash = hashIndex >= 0 ? url.slice(0, hashIndex) : url;
    var queryIndex = withoutHash.indexOf("?");

    if (queryIndex < 0) {
      return { value: url, changed: false };
    }

    var base = withoutHash.slice(0, queryIndex);
    var query = withoutHash.slice(queryIndex + 1);
    var scrubbed = scrubEncodedPairs(query);

    if (!scrubbed.changed) {
      return { value: url, changed: false };
    }

    return {
      value: base + (scrubbed.value ? "?" + scrubbed.value : "") + hash,
      changed: true
    };
  }

  if (hasSignature(originalHeaders)) {
    $done({});
    return;
  }

  var output = {};
  var urlResult = scrubUrl(originalUrl);
  var headerResult = scrubHeaders(originalHeaders);
  var headers = headerResult.value;
  var bodyResult = { value: originalBody, changed: false };

  if (originalBody !== null) {
    var contentEncoding = getHeader(headers, "content-encoding").toLowerCase();
    var contentType = getHeader(headers, "content-type").toLowerCase();
    var bodyLooksJson = /^[\s\r\n]*[\[{]/.test(originalBody);
    var bodyIsCompressed = contentEncoding && contentEncoding !== "identity";

    if (!bodyIsCompressed && (contentType.indexOf("application/json") >= 0 || bodyLooksJson)) {
      bodyResult = scrubJsonText(originalBody);
    } else if (!bodyIsCompressed && contentType.indexOf("application/x-www-form-urlencoded") >= 0) {
      bodyResult = scrubEncodedPairs(originalBody);
    }
  }

  if (bodyResult.changed) {
    headerResult.changed = deleteHeader(headers, "content-length") || headerResult.changed;
    headerResult.changed = deleteHeader(headers, "content-md5") || headerResult.changed;
    output.body = bodyResult.value;
  }

  if (urlResult.changed) {
    output.url = urlResult.value;
  }

  if (headerResult.changed) {
    output.headers = headers;
  }

  $done(output);
})();
