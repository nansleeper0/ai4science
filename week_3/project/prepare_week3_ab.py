"""Подготовить две копии проекта, отличающиеся одной инструкцией."""

from pathlib import Path
from hashlib import sha256
import json
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
record = ROOT / "results/week3_ab_paths.json"
if record.exists():
    raise FileExistsError("Сравнение уже подготовлено: прочитайте results/week3_ab_paths.json")

tracked = ["AGENTS.md", "INDEX.md", "STATUS.md", "src/build_pv.py", "results/week3_ab_METHOD.md", "prepare_week3_ab.py"]
for relative in tracked:
    subprocess.run(["git", "ls-files", "--error-unmatch", relative], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
dirty = subprocess.check_output(["git", "status", "--porcelain", "--", *tracked], cwd=ROOT, text=True)
if dirty.strip():
    raise RuntimeError("До сравнения закоммитьте AGENTS, INDEX, STATUS, код с пометками, методику и подготовку")

contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
lines = contract.splitlines(keepends=True)
removed = [line for line in lines if "[W3-ROUND]" in line]
if len(removed) != 1 or "двух знаков" not in removed[0]:
    raise ValueError("Нужна одна строка AGENTS с [W3-ROUND] и правилом двух знаков")

base = Path(tempfile.mkdtemp(prefix="ai4science_week3_ab_"))
ignore = shutil.ignore_patterns(".git", ".ipynb_checkpoints", "__pycache__", ".venv", ".env", ".env.*")
with_dir, without_dir = base / "with", base / "without"
shutil.copytree(ROOT, with_dir, ignore=ignore)
shutil.copytree(ROOT, without_dir, ignore=ignore)
without_contract = "".join(line for line in lines if "[W3-ROUND]" not in line)
(without_dir / "AGENTS.md").write_text(without_contract, encoding="utf-8")

def manifest(directory):
    return {str(p.relative_to(directory)): sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob("*")) if p.is_file() and not p.is_symlink()}

with_hashes, without_hashes = manifest(with_dir), manifest(without_dir)
differences = sorted(k for k in set(with_hashes) | set(without_hashes)
                     if with_hashes.get(k) != without_hashes.get(k))
if differences != ["AGENTS.md"]:
    raise RuntimeError(f"Копии отличаются не только AGENTS.md: {differences}")

data = {
    "with": str(with_dir), "without": str(without_dir),
    "precommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "removed_line": removed[0].rstrip("\n"),
    "with_contract": contract, "without_contract": without_contract,
    "with_hashes": with_hashes, "without_hashes": without_hashes,
}
record.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("С правилом:", with_dir)
print("Без правила:", without_dir)
print("Проверено: копии различаются только одной строкой AGENTS.md.")
print("Подготовка сохранена:", record)
