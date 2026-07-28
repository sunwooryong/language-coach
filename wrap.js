// 원본 앱(lesson.html; Artifact용 본문)을 GitHub Pages용 완전한 HTML 문서로 감싼다.
// 핵심: 모바일 최적화를 위한 viewport 메타(+ safe-area viewport-fit=cover)를 주입.
// 사용: node wrap.js <원본경로> <출력경로> <라이트배경색> <다크배경색>
const fs = require("fs");
const [, , src, out, light, dark] = process.argv;
if (!src || !out) { console.error("usage: node wrap.js <src> <out> <lightColor> <darkColor>"); process.exit(1); }
const raw = fs.readFileSync(src, "utf8");
const tm = raw.match(/<title>[\s\S]*?<\/title>/i);
const title = tm ? tm[0] : "<title>Language Coach</title>";
const bodyContent = tm ? raw.replace(tm[0], "") : raw;
const L = light || "#F6F1E7", D = dark || "#191510";
const doc =
"<!doctype html>\n<html lang=\"ko\">\n<head>\n" +
"<meta charset=\"utf-8\">\n" +
"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n" +
"<meta name=\"theme-color\" content=\"" + L + "\" media=\"(prefers-color-scheme: light)\">\n" +
"<meta name=\"theme-color\" content=\"" + D + "\" media=\"(prefers-color-scheme: dark)\">\n" +
"<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">\n" +
"<meta name=\"mobile-web-app-capable\" content=\"yes\">\n" +
"<meta name=\"apple-mobile-web-app-status-bar-style\" content=\"default\">\n" +
"<meta name=\"format-detection\" content=\"telephone=no\">\n" +
title + "\n</head>\n<body>\n" +
bodyContent +
"\n</body>\n</html>\n";
fs.writeFileSync(out, doc);
console.log("wrapped -> " + out + " (" + doc.length + " bytes)");
