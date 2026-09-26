# Ping0 Route Helper for Shadowrocket

This lightweight module routes Ping0 requests through the proxy policy selected in Shadowrocket. It is an independent module alongside the TikTok privacy module.

## Safari one-tap install

Open this page in Safari on an iPhone or iPad with Shadowrocket installed, then tap the link. Shadowrocket will ask you to confirm importing the module.

[🚀 Safari 一键跳转 Shadowrocket 并安装 Ping0 模块](https://lowertop.github.io/Shadowrocket-First/redirect.html?url=shadowrocket%3A%2F%2Finstall%3Fmodule%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2Fplao94619-hash%2FRepository-name-VideoToolBox%2Fmain%2Fextras%2Fshadowrocket%2Fping0%2FPing0.module)

If Safari does not switch automatically, open the raw module in Shadowrocket's module importer:

`https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/ping0/Ping0.module`

## What it does

The module adds exactly one rule:

```ini
DOMAIN-SUFFIX,ping0.cc,PROXY
```

This sends `ping0.cc` and its subdomains, including `ip.ping0.cc`, through the `PROXY` policy. If your Shadowrocket configuration uses a different policy name, edit the rule to match it.

It does not inspect or modify HTTPS traffic, enable MITM, install certificates, change other domains, or collect data. Ping0's IP-risk database, distributed probes, and browser tests remain services provided by [ping0.cc](https://ping0.cc/); this module only controls routing.

## Manual installation

1. Copy the raw module URL above.
2. In Shadowrocket, open **配置 → 模块** and tap **+**.
3. Paste the URL, import the module, and enable it.

The one-tap link uses the existing Shadowrocket URL-scheme redirect documented by the repository's current install guide. iOS still requires you to confirm the import in Shadowrocket.

## Troubleshooting

- If Shadowrocket reports 404, first open the raw module URL in Safari and confirm the file loads. This path is in the existing public repository.
- If Ping0 still sees your direct IP, confirm the module is enabled, the active configuration uses the `PROXY` policy, and Shadowrocket is connected.
- If your policy group has another name, change `PROXY` in the module rule to that exact name.

