// lesson.html에서 VOCAB + THEMES 를 추출해 JSON으로 출력 (gen_audio.py가 사용)
const fs=require("fs"), vm=require("vm");
const html=fs.readFileSync(process.argv[2],"utf8");
const m=html.match(/var VOCAB\s*=\s*\[([\s\S]*?)\];/);
if(!m){ process.stderr.write("VOCAB not found\n"); process.exit(1); }
const tm=html.match(/var THEMES\s*=\s*\[([\s\S]*?)\];\s*\nfunction themeById/);
const ctx={}; vm.createContext(ctx);
vm.runInContext(m[0]+";this.V=VOCAB;",ctx);
let themes=[];
if(tm){ try{ vm.runInContext(tm[0].replace(/\s*function themeById[\s\S]*$/,"")+";this.T=THEMES;",ctx); themes=ctx.T||[]; }catch(e){ process.stderr.write("THEMES parse warn: "+e.message+"\n"); } }
process.stdout.write(JSON.stringify({vocab:ctx.V, themes:themes}));
