const assert = require("node:assert");
const check = require("./index.js");

assert.strictEqual(check("42"), true);
assert.strictEqual(check("forty-two"), false);
console.log("npm fixture: tests passed");
