#!/usr/bin/env python3
"""
to_lines_cell.py

Takes a Python source file (default: attack.py) and converts it into the
`lines = [...]` notebook-cell format (one repr'd string per source line,
joined with "\n", written out, then syntax-checked) — same shape as the
lines_cell.py you already have. Output is written to output.pt so you can
copy-paste it straight into a notebook cell.

Usage:
    python to_lines_cell.py [input_file]

    input_file -> path to the .py file to convert (default: attack.py)

Output:
    output.pt containing:
        lines = [
            'line 1',
            'line 2',
            ...
        ]

        ATTACK_CODE = "\n".join(lines)

        with open("attack.py", "w", encoding="utf-8") as f:
            f.write(ATTACK_CODE)
        print("attack.py written")

        import py_compile
        try:
            py_compile.compile("attack.py", doraise=True)
            print("Syntax OK")
        except py_compile.PyCompileError as e:
            print("SYNTAX ERROR: " + str(e))
"""

import sys
from pathlib import Path


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("attack.py")

    if not input_path.exists():
        print(f"ERROR: {input_path} not found")
        sys.exit(1)

    code = input_path.read_text(encoding="utf-8")
    # normalize line endings so the generated lines list is CRLF/LF-safe
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    lines = code.split("\n")

    out_path = Path("output.py")
    with out_path.open("w", encoding="utf-8") as out:
        out.write("lines = [\n")
        for ln in lines:
            out.write("    " + repr(ln) + ",\n")
        out.write("]\n\n")
        out.write('ATTACK_CODE = "\\n".join(lines)\n\n')
        out.write('with open("/kaggle/working/attack.py", "w", encoding="utf-8") as f:\n')
        out.write("    f.write(ATTACK_CODE)\n")
        out.write('print("/kaggle/working/attack.py written")\n\n')
        out.write("import py_compile\n")
        out.write("try:\n")
        out.write('    py_compile.compile("/kaggle/working/attack.py", doraise=True)\n')
        out.write('    print("Syntax OK")\n')
        out.write("except py_compile.PyCompileError as e:\n")
        out.write('    print("SYNTAX ERROR: " + str(e))\n')

    print(f"Wrote {out_path} ({len(lines)} lines from {input_path})")


if __name__ == "__main__":
    main()