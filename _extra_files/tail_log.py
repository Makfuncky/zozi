import io
p = r"C:\Users\user\.local\share\kilo\tool-output\tool_fd87bc24000170M0P9nRCPjzAJ"
lines = io.open(p, encoding="utf-8", errors="replace").read().split("\n")
print("TOTAL LINES:", len(lines))
for ln in lines[-50:]:
    print(ln)
