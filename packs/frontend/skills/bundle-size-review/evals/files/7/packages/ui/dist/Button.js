"use strict";
var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0) t[p] = s[p];
    return t;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Button = Button;
const jsx_runtime_1 = require("react/jsx-runtime");
require("./Button.css");
function Button(_a) {
    var { variant = 'primary', className = '' } = _a, rest = __rest(_a, ["variant", "className"]);
    return (0, jsx_runtime_1.jsx)("button", Object.assign({ className: `qm-btn qm-btn--${variant} ${className}` }, rest));
}
