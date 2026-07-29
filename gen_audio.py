# 핸즈프리 "오디오 모드"용 단어별 연속 MP3 생성기 (매끄러운 고품질 방식).
# 각 클립을 PCM으로 디코드→하나로 이어붙임(경계 잡음 없음)→128kbps로 한 번만 인코딩.
# 대상언어 voice: edge 음성명(vi-VN-HoaiMyNeural 등) 또는 "google"(gTTS, 폰 음성과 유사).
# 사용: python gen_audio.py <lesson.html> <출력폴더> <대상언어voice> <한국어voice>
import sys, os, json, subprocess, hashlib, asyncio
import edge_tts, miniaudio, lameenc
try: from gtts import gTTS
except Exception: gTTS = None
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

SR = 24000
CACHE_DIR = r"C:\Users\sunwo\.claude\audio-cache"

def synth_path(text, voice):
    text = (text or "").strip()
    if not text:
        return None
    key = hashlib.md5((voice + "|" + text).encode("utf-8")).hexdigest()
    path = os.path.join(CACHE_DIR, key + ".mp3")
    if not os.path.exists(path) or os.path.getsize(path) < 200:
        if voice == "google":
            gTTS(text, lang="vi").save(path)
        elif voice == "google-ko":
            gTTS(text, lang="ko").save(path)
        else:
            asyncio.run(edge_tts.Communicate(text, voice).save(path))
    return path

def pcm(text, voice):
    p = synth_path(text, voice)
    if not p:
        return b""
    d = miniaudio.decode_file(p, output_format=miniaudio.SampleFormat.SIGNED16,
                              nchannels=1, sample_rate=SR)
    return bytes(d.samples)

def sil(sec):
    return b"\x00\x00" * int(SR * sec)

def build_pcm(w, tv, kv):
    target, ko, exs = w[1], w[2], w[4]
    segs = [pcm(ko, kv), sil(1.8)]
    v = pcm(target, tv)
    segs += [v, sil(1.5), v, sil(1.2)]
    for e in exs:
        segs += [pcm(e[2], kv), sil(1.5), pcm(e[1], tv), sil(1.4)]
    segs += [sil(0.7)]
    return b"".join(segs)

def write_word(w, tv, kv, outp):
    data = build_pcm(w, tv, kv)
    enc = lameenc.Encoder()
    enc.set_bit_rate(128); enc.set_in_sample_rate(SR); enc.set_channels(1); enc.set_quality(0)
    with open(outp, "wb") as f:
        f.write(enc.encode(data) + enc.flush())

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
