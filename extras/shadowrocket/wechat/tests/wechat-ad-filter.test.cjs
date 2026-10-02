"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { filterResponse, routeFor } = require("../wechat-ad-filter.js");
const article = "https://mp.weixin.qq.com/mp/getappmsgad?__biz=example";
const qmai = "https://webapi.qmai.cn/web/catering/advertising/ad/advertiseInfo";
const meituan = "https://rms.meituan.com/api/v1/rmsmina/c/queryPortalInfo";
const source = fs.readFileSync(path.join(__dirname, "../wechat-ad-filter.js"), "utf8");
const moduleText = fs.readFileSync(path.join(__dirname, "../WeChat-AdBlock-2026.module"), "utf8");
const adBody = { base_resp: { ret: 0 }, advertisement_num: 2, advertisement_info: [{ ad: 1 }, { ad: 2 }] };

function run(url, payload, extra = {}) {
  return filterResponse({ url, method: "GET" }, { body: JSON.stringify(payload), ...extra });
}

test("article ad removal preserves appid, comments, reading counts and other fields", () => {
  const payload = { ...adBody, appid: "wx-example", appmsgstat: { read_num: 321, like_num: 12 },
    comment_list: [{ content: "这是正常评论" }], next_url: "https://mp.weixin.qq.com/s/normal" };
  const before = JSON.stringify(payload);
  const result = JSON.parse(run(article, payload).body);
  assert.deepEqual(result, { ...payload, advertisement_num: 0, advertisement_info: [] });
  assert.equal(JSON.stringify(payload), before);
});

test("already clean responses stay byte-for-byte untouched", () => {
  const body = '{ "advertisement_info" : [], "advertisement_num" : 0, "appid": "keep" }';
  assert.deepEqual(filterResponse({ url: article }, { body }), {});
});

for (const payload of [{}, { advertisement_num: 5 }, { advertisement_info: {} },
  { advertisement_info: null }, { data: { advertisement_info: [{ ad: 1 }] } }]) {
  test("unknown article schema passes through: " + JSON.stringify(payload), () => {
    assert.deepEqual(run(article, payload), {});
  });
}

for (const [name, body] of [
  ["HTML", "<html><body>article</body></html>"],
  ["JSONP", "callback({\"advertisement_info\":[{}]})"],
  ["malformed JSON", '{"advertisement_info":'],
  ["JSON array", "[]"], ["empty body", ""], ["compressed/binary bytes", "\x1f\x8b\x00\x00"]
]) {
  test(name + " passes through without throwing", () => {
    assert.deepEqual(filterResponse({ url: article }, { body }), {});
  });
}

test("BOM and whitespace are accepted for otherwise valid JSON", () => {
  const result = filterResponse({ url: article }, { body: "\uFEFF  " + JSON.stringify(adBody) });
  assert.equal(JSON.parse(result.body).advertisement_num, 0);
});

for (const extra of [{ status: 500 }, { statusCode: 403 }, { status: "HTTP/1.1 401 Unauthorized" },
  { headers: { "Content-Type": "application/octet-stream" } },
  { headers: { "content-type": "application/x-protobuf" } },
  { headers: { "Content-Type": "video/mp4" } }]) {
  test("HTTP error or binary MIME is untouched: " + JSON.stringify(extra), () => {
    assert.deepEqual(run(article, adBody, extra), {});
  });
}

test("API error responses are preserved", () => {
  assert.deepEqual(run(article, { ...adBody, base_resp: { ret: -3, err_msg: "expired" } }), {});
  assert.deepEqual(run(article, { ...adBody, ret: "-1" }), {});
});

test("new body has no stale size/encoding/hash but preserves cookies and unrelated headers", () => {
  const headers = { "Content-Length": "500", "content-encoding": "gzip", ETag: "old-hash",
    "Content-MD5": "old", Digest: "old", "Content-Type": "application/json",
    "Set-Cookie": "session=fixture", "X-Custom": "keep" };
  const result = run(article, adBody, { headers });
  assert.deepEqual(result.headers, { "Content-Type": "application/json",
    "Set-Cookie": "session=fixture", "X-Custom": "keep" });
  assert.equal(headers.ETag, "old-hash");
});

test("article requests are never rewritten", () => {
  const request = { url: article, method: "POST", headers: { Cookie: "keep", Authorization: "keep" },
    body: "important=formdata" };
  const before = structuredClone(request);
  filterResponse(request, { body: JSON.stringify(adBody) });
  assert.deepEqual(request, before);
});

test("oversized responses pass through", () => {
  const payload = { ...adBody, padding: "a".repeat(1048577) };
  assert.deepEqual(run(article, payload), {});
});

test("missing objects and HEAD responses pass through", () => {
  assert.deepEqual(filterResponse(null, null), {});
  assert.deepEqual(filterResponse({ url: article, method: "HEAD" }, { body: JSON.stringify(adBody) }), {});
  assert.deepEqual(filterResponse({ url: article }, { body: new Uint8Array([1, 2]) }), {});
});

test("Qmai filters recognized ads while preserving unknown data and success envelope", () => {
  const payload = { code: 0, message: "success", requestId: "keep", data: [
    { id: 1, detailInfo: { adType: 4, popDayLimit: 3 } },
    { unknownFutureSchema: true }, null,
    { id: 2, detailInfo: { adLandingInfoList: [] } } ] };
  assert.deepEqual(JSON.parse(run(qmai, payload).body), { ...payload, data: [{ unknownFutureSchema: true }, null] });
});

test("Qmai object, clean array and unknown array schemas pass through", () => {
  for (const data of [{ token: "keep" }, [], [{ id: "unknown" }]]) {
    assert.deepEqual(run(qmai, { data }), {});
  }
});

test("Meituan removes ads and float window while keeping navigation, products and malformed entries", () => {
  const keep = [{ name: "menu", data: { advType: false, products: [1, 2] } },
    { name: "navigation" }, { name: "future", data: { advType: "true" } }, null];
  const payload = { code: 0, token: "keep", data: { shopId: 123, modules: [
    ...keep, { name: "banner", data: { advType: true } }, { name: "float-window", data: {} }
  ] } };
  const result = JSON.parse(run(meituan, payload).body);
  assert.deepEqual(result, { ...payload, data: { shopId: 123, modules: keep } });
});

test("Meituan normal responses are not reserialized", () => {
  for (const payload of [{ data: { modules: [{ name: "menu" }] } }, { data: null }, { data: { modules: {} } }]) {
    assert.deepEqual(run(meituan, payload), {});
  }
});

for (const url of [
  "https://mp.weixin.qq.com/mp/getappmsgext?normal=1",
  "https://mp.weixin.qq.com/s?__biz=article",
  "https://mp.weixin.qq.com/mp/getappmsgadExtra",
  "https://mp.weixin.qq.com.evil.example/mp/getappmsgad",
  "https://mp.weixin.qq.com@evil.example/mp/getappmsgad",
  "https://pay.weixin.qq.com/mp/getappmsgad",
  "https://webapi.qmai.cn/web/catering/order/create",
  "https://webapi.qmai.cn/web/catering/advertising/ad/advertiseInfoExtra",
  "https://rms.meituan.com/api/v1/rmsmina/c/queryPortalInfoExtra",
  "https://short.weixin.qq.com/mmtls/00000001",
  "https://wxa.wxs.qq.com/wxaapi/business"
]) {
  test("normal/lookalike/MMTLS interface is outside script scope: " + url, () => {
    assert.equal(routeFor(url), "");
    assert.deepEqual(run(url, adBody), {});
  });
}

test("Qmai aliases/versioned paths and Meituan multi-digit versions are covered", () => {
  assert.equal(routeFor("https://miniapp.qmai.cn/web/catering3-apiserver/advertising/ad/advertiseInfo?a=1"), "qmai");
  assert.equal(routeFor("https://rms.meituan.com/api/v12/rmsmina/c/queryPortalInfo?shop=1"), "meituan");
});

test("JSC-style runtime completes once with no external APIs or Node globals", () => {
  const results = [];
  vm.runInNewContext(source, {
    $request: { url: article }, $response: { body: JSON.stringify(adBody) },
    $done: result => results.push(JSON.parse(JSON.stringify(result)))
  }, { timeout: 1000 });
  assert.equal(results.length, 1);
  assert.equal(JSON.parse(results[0].body).advertisement_num, 0);
});

test("JSC-style runtime completes once for malformed and missing responses", () => {
  for (const context of [{ $request: { url: article }, $response: { body: "bad JSON" } }, {}]) {
    const results = [];
    vm.runInNewContext(source, { ...context, $done: result => results.push(JSON.parse(JSON.stringify(result))) }, { timeout: 1000 });
    assert.deepEqual(results, [{}]);
  }
});

const rewrites = moduleText.split("\n").filter(line => line.startsWith("^"))
  .map(line => new RegExp(line.split(" - ")[0]));
const scriptPatterns = moduleText.split("\n").filter(line => line.includes(" = type=http-response,"))
  .map(line => new RegExp(line.match(/pattern=([^,]+),/)[1]));
const intercepted = url => [...rewrites, ...scriptPatterns].some(rule => rule.test(url));

test("module blocks ad fetch/exposure with reordered query parameters", () => {
  for (const url of [
    "https://mp.weixin.qq.com/wapad/getaddata?action=getad&foo=1",
    "https://mp.weixin.qq.com/wapad/getaddata?foo=1&action=getad&bar=2",
    "https://mp.weixin.qq.com/wapad/reportaddata?a=1&action=exposure_report",
    "https://mp.weixin.qq.com/mp/advertisement?x=1",
    "https://mp.weixin.qq.com/mp/ad_video?x=1",
    "https://miniapp.qmai.cn/web/cmk-center/marketing/canvas/advert?shop=1"
  ]) assert.equal(intercepted(url), true, url);
});

test("module leaves unrelated article/mini-program/payment operations untouched", () => {
  for (const url of [
    "https://mp.weixin.qq.com/wapad/getaddata?action=getad_other",
    "https://mp.weixin.qq.com/wapad/getaddata?notaction=getad",
    "https://mp.weixin.qq.com/wapad/getaddata?next=action=getad",
    "https://mp.weixin.qq.com/mp/advertisementExtra",
    "https://miniapp.qmai.cn/web/cmk-center/marketing/canvas/advertExtra",
    "https://mp.weixin.qq.com/s?__biz=article",
    "https://mp.weixin.qq.com/mp/getappmsgext",
    "https://payapp.weixin.qq.com/mchopenapp/goldplan/pay",
    "https://wxa.wxs.qq.com/wxaapi/business",
    "https://rms.meituan.com/api/v1/rmsmina/c/createOrder",
    "https://mp.weixin.qq.com.evil.example/mp/advertisement"
  ]) assert.equal(intercepted(url), false, url);
});

test("module uses supported narrow sections, bounded scripts and append-only MITM", () => {
  const sections = moduleText.match(/^\[[^\]]+\]$/gm);
  assert.deepEqual(sections, ["[Rule]", "[URL Rewrite]", "[Script]", "[MITM]"]);
  assert.match(moduleText, /^hostname = %APPEND% mp\.weixin\.qq\.com, webapi\.qmai\.cn, miniapp\.qmai\.cn, rms\.meituan\.com$/m);
  assert.equal(scriptPatterns.length, 3);
  assert.equal(rewrites.length, 5);
  for (const line of moduleText.split("\n").filter(line => line.includes(" = type=http-response,"))) {
    assert.match(line, /requires-body=1,max-size=1048576/);
    assert.match(line, /engine=jsc$/);
  }
  assert.doesNotMatch(moduleText, /^DOMAIN-SUFFIX,(?:wxs\.qq\.com|weixin\.qq\.com|qq\.com),/m);
  assert.doesNotMatch(source, /\$(?:httpClient|task|persistentStore|prefs|notification)\b|fetch\(/);
});
