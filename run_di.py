"""Run Sarvam Document Intelligence on a file. Usage: python3 run_di.py <file> <language>"""

import sys
import zipfile
from pathlib import Path

from sarvamai import SarvamAI

from config import get_api_key

path = Path(sys.argv[1])
language = sys.argv[2] if len(sys.argv) > 2 else "mr-IN"
out_dir = Path("output") / f"{path.stem}-{language}"
out_dir.mkdir(parents=True, exist_ok=True)

client = SarvamAI(api_subscription_key=get_api_key())

job = client.document_intelligence.create_job(language=language, output_format="md")
print(f"job created for {path.name} [{language}]")
job.upload_file(str(path))
job.start()
status = job.wait_until_complete()
print(f"state: {status.job_state}")

zip_path = out_dir / "output.zip"
job.download_output(str(zip_path))
with zipfile.ZipFile(zip_path) as z:
    z.extractall(out_dir)

for f in sorted(out_dir.rglob("*.md")):
    print(f"\n===== {f.name} =====")
    print(f.read_text())
