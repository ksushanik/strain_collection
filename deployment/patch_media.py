import sys
path = "/tmp/default.conf"
s = open(path, "r", encoding="utf-8", errors="ignore").read().splitlines()
out = []
in_block = False
inserted = False
for i, line in enumerate(s):
    out.append(line)
    if not in_block and line.strip().startswith("location ^~ /media/ {"):
        in_block = True
        continue
    if in_block and "proxy_pass http://backend:8000;" in line and not inserted:
        # check if Host header already present before closing brace
        j = i + 1
        present = False
        while j < len(s) and "}" not in s[j]:
            if "proxy_set_header Host" in s[j]:
                present = True
                break
            j += 1
        if not present:
            out.append("        proxy_set_header Host culturedb.elcity.ru;")
            inserted = True
        continue
    if in_block and "}" in line:
        in_block = False
        continue
open(path, "w", encoding="utf-8").write("\n".join(out))
