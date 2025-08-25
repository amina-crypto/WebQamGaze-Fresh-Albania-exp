import json, re, unicodedata, math
from pathlib import Path
from typing import Optional
from transformers import MarianMTModel, MarianTokenizer

SRC = Path("datasets/xquad-master/xquad.en.json")
DST = Path("datasets/xquad-master/xquad.al.json")

model_name = "Helsinki-NLP/opus-mt-en-al"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

# ---------- helpers ----------
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def translate_text(text: str) -> str:
    if not text.strip():
        return text
    # split big paragraphs into smaller chunks (Marian has a token limit)
    parts = split_for_translation(text)
    out = []
    for p in parts:
        enc = tokenizer(p, return_tensors="pt", truncation=True)
        gen = model.generate(**enc, max_new_tokens=512)
        out.append(tokenizer.decode(gen[0], skip_special_tokens=True))
    return "".join(out)

def split_for_translation(text: str, max_len: int = 800) -> list[str]:
    # Split by sentence-ish boundaries but keep delimiters
    sentences = re.split(r"(?<=[\.\!\?])(\s+)", text)
    chunks, cur, cur_len = [], [], 0
    for seg in sentences:
        if cur_len + len(seg) > max_len and cur:
            chunks.append("".join(cur))
            cur, cur_len = [seg], len(seg)
        else:
            cur.append(seg); cur_len += len(seg)
    if cur: chunks.append("".join(cur))
    return chunks

EN_NUM = {
    "zero":"0","one":"1","two":"2","three":"3","four":"4","five":"5","six":"6","seven":"7","eight":"8","nine":"9",
    "ten":"10","eleven":"11","twelve":"12","thirteen":"13","fourteen":"14","fifteen":"15","sixteen":"16",
    "seventeen":"17","eighteen":"18","nineteen":"19","twenty":"20"
}

def candidates_for_answer(ans_al: str) -> list[str]:
    cands = [ans_al]
    digits = re.sub(r"[^\d]", "", ans_al)
    if digits:
        cands.append(digits)
    return list(dict.fromkeys(cands))  # unique, keep order

def find_with_strategies(context_al: str, ans_al: str) -> Optional[int]:
    idx = context_al.find(ans_al)
    if idx != -1: return idx

    for cand in candidates_for_answer(ans_al):
        idx = context_al.find(cand)
        if idx != -1: return idx

    ctx_norm = strip_accents(context_al).lower()
    ans_norm = strip_accents(ans_al).lower()
    idx = ctx_norm.find(ans_norm)
    if idx != -1:
        window = max(0, idx - 5)
        raw_idx = context_al.lower().find(ans_al.lower(), window)
        return raw_idx if raw_idx != -1 else idx

    if re.search(r"\d", ans_al):
        m = re.search(re.escape(re.sub(r"[^\d]", "", ans_al)), re.sub(r"[^\d]", "", context_al))
        if m:
            digits = re.sub(r"[^\d]", "", ans_al)
            return context_al.find(digits)

    return None

# ---------- main ----------
def main(src: Path = SRC, dst: Path = DST):
    data = json.loads(src.read_text(encoding="utf-8"))

    for article in data["data"]:
        for para in article["paragraphs"]:
            ctx_en = para["context"]
            ctx_al = translate_text(ctx_en)
            para["context"] = ctx_al

            for qa in para["qas"]:
                qa["question"] = translate_text(qa["question"])

                new_answers = []
                for ans in qa.get("answers", []):
                    txt_en = ans.get("text", "")
                    txt_al = translate_text(txt_en)

                    start = find_with_strategies(ctx_al, txt_al)
                    if start is None:
                        print(f"WARNING: could not align answer '{txt_al[:30]}...' in a paragraph.")
                        new_answers.append({"text": txt_al, "answer_start": -1})
                    else:
                        new_answers.append({"text": txt_al, "answer_start": start})
                qa["answers"] = new_answers
        # ...existing code...

    dst.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {dst}")

if __name__ == "__main__":
    main()
  