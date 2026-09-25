from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/build.gradle"
s=p.read_text(encoding="utf-8")
s=s.replace("versionCode 4","versionCode 5")
s=s.replace("versionName '1.3'","versionName '1.4'")
p.write_text(s,encoding="utf-8")
print("Jarvis Casa v1.4 version")

import runpy
runpy.run_path("jarvis-build/fix_v14g.py", run_name="__main__")
