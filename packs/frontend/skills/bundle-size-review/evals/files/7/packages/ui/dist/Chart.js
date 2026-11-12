"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Chart = exports.QmChart = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const auto_1 = __importDefault(require("chart.js/auto"));
function QmChart({ config }) {
    const canvas = (0, react_1.useRef)(null);
    (0, react_1.useEffect)(() => {
        if (!canvas.current)
            return;
        const chart = new auto_1.default(canvas.current, config);
        return () => chart.destroy();
    }, [config]);
    return (0, jsx_runtime_1.jsx)("canvas", { ref: canvas });
}
exports.QmChart = QmChart;
exports.Chart = QmChart;
