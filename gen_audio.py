# 핸즈프리 "오디오 모드"용 단어별 연속 MP3 생성기 (무손실 방식).
# edge-tts(뉴럴 음성) 원본 MP3를 재인코딩 없이 그대로 이어붙인다 → 원음질 100% 보존.
# 사이 침묵은 동일 포맷(24kHz/48kbps/mono)의 무음 MP3를 삽입.
# 사용: python gen_audio.py <lesson.html> <출력폴더> <대상언어voice> <한국어voice>
import sys, os, json, subprocess, hashlib, asyncio
import edge_tts, lameenc
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

SR = 24000
CACHE_DIR = r"C:\Users\sunwo\.claude\audio-cache"  # 원본 음성 클립 캐시(저장소 밖)

def synth_path(text, voice):
    text = (text or "").strip()
    if not text:
        return None
    key = hashlib.md5((voice + "|" + text).encode("utf-8")).hexdigest()
    path = os.path.join(CACHE_DIR, key + ".mp3")
    if not os.path.exists(path) or os.path.getsize(path) < 200:
        async def go():
            await edge_tts.Communicate(text, voice).save(path)
        asyncio.run(go())
    return path

def clip(text, voice):
    p = synth_path(text, voice)
    return open(p, "rb").read() if p else b""

_SIL = {}
def sil(sec):
    k = round(sec, 2)
    if k not in _SIL:
        e = lameenc.Encoder()
        e.set_bit_rate(48); e.set_in_sample_rate(SR); e.set_channels(1); e.set_quality(2)
        _SIL[k] = e.encode(b"\x00\x00" * int(SR * sec)) + e.flush()
    return _SIL[k]

def build_word(w, tv, kv):
    # w = [cat, target, ko, say, [[t, target_ex, ko_ex, say], ...]]
    target, ko, exs = w[1], w[2], w[4]
    parts = [clip(ko, kv), sil(1.8)]
    v = clip(target, tv)
    parts += [v, sil(1.5), v, sil(1.2)]
    for e in exs:
        parts += [clip(e[2], kv), sil(1.5), clip(e[1], tv), sil(1.4)]
    parts += [sil(0.7)]
    return b"".join(parts)

def write_word(w, tv, kv, outp):
    with open(outp, "wb") as f:
        f.write(build_word(w, tv, kv))

def main():
    lesson, outdir, tv, kv = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    data = json.loads(subprocess.check_output(["node", os.path.join(here, "dump_vocab.js"), lesson]).decode("utf-8"))
    VOCAB = data.get("vocab", [])
    THEMES = data.get("themes", [])
    made = 0
    for i, w in enumerate(VOCAB):
        outp = os.path.join(outdir, "w%d.mp3" % i)
        if os.path.exists(outp) and os.path.getsize(outp) > 500:
            continue
        try:
            write_word(w, tv, kv, outp); made += 1
            print("  w%d.mp3  (%s)" % (i, w[1]), flush=True)
        except Exception as ex:
            print("  ! w%d FAILED: %s" % (i, ex), flush=True)
    tcount = {}
    for th in THEMES:
        tid = th.get("id"); words = th.get("words", [])
        tcount[tid] = len(words)
        for n, w in enumerate(words):
            outp = os.path.join(outdir, "%s_%d.mp3" % (tid, n))
            if os.path.exists(outp) and os.path.getsize(outp) > 500:
                continue
            try:
                write_word(w, tv, kv, outp); made += 1
                print("  %s_%d.mp3  (%s)" % (tid, n, w[1]), flush=True)
            except Exception as ex:
                print("  ! %s_%d FAILED: %s" % (tid, n, ex), flush=True)
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"count": len(VOCAB), "themes": tcount}, f)
    print("DONE. new=%d vocab=%d themes=%d" % (made, len(VOCAB), sum(tcount.values())), flush=True)

if __name__ == "__main__":
    main()
