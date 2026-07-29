// lesson.html에서 VOCAB 배열을 추출해 JSON으로 출력 (gen_audio.py가 사용)
const fs=require("fs"), vm=require("vm");
const html=fs.readFileSync(process.argv[2],"utf8");
const m=html.match(/var VOCAB\s*=\s*\[([\s\S]*?)\];/);
if(!m){ process.stderr.write("VOCAB not found\n"); process.exit(1); }
const ctx={}; vm.createContext(ctx); vm.runInContext(m[0]+";this.V=VOCAB;",ctx);
process.stdout.write(JSON.stringify(ctx.V));
