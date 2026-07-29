# 핸즈프리 "오디오 모드"용 단어별 연속 MP3 생성기.
# 각 단어 → [한국어뜻] (생각) [대상언어] (따라말하기) [대상언어 반복] + 예문들 → 단일 MP3.
# edge-tts(뉴럴 음성) → miniaudio 디코드 → 무음 삽입 → lameenc 단일 MP3 재인코딩.
# 사용: python gen_audio.py <lesson.html> <출력폴더> <대상언어voice> <한국어voice>
import sys, os, json, subprocess, hashlib, asyncio
import edge_tts, miniaudio, lameenc
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

SR = 24000
CACHE_DIR = r"C:\Users\sunwo\.claude\audio-cache"  # 저장소 밖(캐시), 재사용으로 재생성 최소화

def synth(text, voice):
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

def pcm(path):
    if not path:
        return b""
    d = miniaudio.decode_file(path, output_format=miniaudio.SampleFormat.SIGNED16,
                              nchannels=1, sample_rate=SR)
    return bytes(d.samples)

def sil(sec):
    return b"\x00\x00" * int(SR * sec)

def build_word(w, tv, kv):
    # w = [cat, target, ko, say, [[t, target_ex, ko_ex, say], x3]]
    target, ko, exs = w[1], w[2], w[4]
    segs = []
    segs += [pcm(synth(ko, kv)), sil(1.8)]
    clip = pcm(synth(target, tv))
    segs += [clip, sil(1.5), clip, sil(1.2)]
    for e in exs:
        segs += [pcm(synth(e[2], kv)), sil(1.5)]
        segs += [pcm(synth(e[1], tv)), sil(1.4)]
    segs += [sil(0.7)]
    return b"".join(segs)

def encode(pcm_bytes, path):
    enc = lameenc.Encoder()
    enc.set_bit_rate(64); enc.set_in_sample_rate(SR); enc.set_channels(1); enc.set_quality(3)
    with open(path, "wb") as f:
        f.write(enc.encode(pcm_bytes) + enc.flush())

def main():
    lesson, outdir, tv, kv = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    vj = subprocess.check_output(["node", os.path.join(here, "dump_vocab.js"), lesson])
    data = json.loads(vj.decode("utf-8"))
    VOCAB = data.get("vocab", [])
    THEMES = data.get("themes", [])
    made = 0
    # 1) 메인 커리큘럼 단어
    for i, w in enumerate(VOCAB):
        outp = os.path.join(outdir, "w%d.mp3" % i)
        if os.path.exists(outp) and os.path.getsize(outp) > 500:
            continue
        try:
            encode(build_word(w, tv, kv), outp)
            made += 1
            print("  w%d.mp3  (%s)" % (i, w[1]), flush=True)
        except Exception as ex:
            print("  ! w%d FAILED: %s" % (i, ex), flush=True)
    # 2) 주제팩 단어 (aud 이름 = <themeId>_<n>)
    tcount = {}
    for th in THEMES:
        tid = th.get("id"); words = th.get("words", [])
        tcount[tid] = len(words)
        for n, w in enumerate(words):
            outp = os.path.join(outdir, "%s_%d.mp3" % (tid, n))
            if os.path.exists(outp) and os.path.getsize(outp) > 500:
                continue
            try:
                encode(build_word(w, tv, kv), outp)
                made += 1
                print("  %s_%d.mp3  (%s)" % (tid, n, w[1]), flush=True)
            except Exception as ex:
                print("  ! %s_%d FAILED: %s" % (tid, n, ex), flush=True)
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"count": len(VOCAB), "themes": tcount}, f)
    print("DONE. new=%d vocab=%d themes=%d" % (made, len(VOCAB), sum(tcount.values())), flush=True)

if __name__ == "__main__":
    main()
