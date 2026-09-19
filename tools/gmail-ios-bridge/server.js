const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const port = Number(process.env.PORT || 3000);
const host = "0.0.0.0";
const index = fs.readFileSync(path.join(__dirname, "index.html"));

const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://localhost");
  if (url.pathname === "/health") {
    res.writeHead(200, {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store"
    });
    return res.end("ok");
  }
  if (url.pathname === "/" || url.pathname === "/index.html") {
    res.writeHead(200, {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "public, max-age=300",
      "x-content-type-options": "nosniff",
      "referrer-policy": "no-referrer",
      "content-security-policy": "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none';"
    });
    return res.end(index);
  }
  res.writeHead(404, {"content-type":"text/plain; charset=utf-8"});
  res.end("Not found");
});

server.listen(port, host, () => {
  console.log(`gmail-ios-bridge listening on ${host}:${port}`);
});
