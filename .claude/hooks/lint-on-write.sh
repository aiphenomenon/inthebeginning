#!/usr/bin/env bash
# ============================================================================
# PostToolUse hook: Lint/validate files after Edit or Write
# ============================================================================
# Runs syntax checks on written files. Non-blocking (exit 0 always) but
# outputs errors that Claude will see and should fix.
# ============================================================================

set -uo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Edit tool uses 'file_path', Write tool uses 'file_path'
ti = data.get('tool_input', {})
print(ti.get('file_path', ''))
" 2>/dev/null)

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

EXTENSION="${FILE_PATH##*.}"
ERRORS=""

case "$EXTENSION" in
    py)
        # Python syntax check via py_compile
        RESULT=$(python3 -m py_compile "$FILE_PATH" 2>&1)
        if [ $? -ne 0 ]; then
            ERRORS="[LINT] Python syntax error in $FILE_PATH:\n$RESULT"
        fi
        ;;
    json)
        # JSON validation
        RESULT=$(python3 -m json.tool "$FILE_PATH" > /dev/null 2>&1)
        if [ $? -ne 0 ]; then
            ERRORS="[LINT] Invalid JSON in $FILE_PATH"
        fi
        ;;
    js)
        # Basic JS syntax check via Node if available
        if command -v node &> /dev/null; then
            RESULT=$(node --check "$FILE_PATH" 2>&1)
            if [ $? -ne 0 ]; then
                ERRORS="[LINT] JavaScript syntax error in $FILE_PATH:\n$RESULT"
            fi
        fi
        ;;
    rs)
        # For Rust, just check if the file parses (only if in a cargo project)
        if [ -f "$(dirname "$FILE_PATH")/Cargo.toml" ] || [ -f "$(dirname "$(dirname "$FILE_PATH")")/Cargo.toml" ]; then
            echo "[LINT] Rust file modified: $FILE_PATH — run 'cargo check' when ready"
        fi
        ;;
    go)
        # Go: vet the file's package if go is available
        if command -v go &> /dev/null; then
            GO_DIR=$(dirname "$FILE_PATH")
            RESULT=$(cd "$GO_DIR" && go vet ./... 2>&1)
            if [ $? -ne 0 ]; then
                ERRORS="[LINT] Go vet error in $FILE_PATH:\n$RESULT"
            fi
        fi
        ;;
    swift)
        # Swift: syntax check if swiftc is available
        if command -v swiftc &> /dev/null; then
            RESULT=$(swiftc -parse "$FILE_PATH" 2>&1)
            if [ $? -ne 0 ]; then
                ERRORS="[LINT] Swift parse error in $FILE_PATH:\n$RESULT"
            fi
        fi
        ;;
    html)
        # HTML: basic well-formedness check via Python
        RESULT=$(python3 -c "
from html.parser import HTMLParser
import sys
class P(HTMLParser):
    def __init__(self): super().__init__(); self.errors = []
    def handle_starttag(self, tag, attrs): pass
p = P()
try: p.feed(open('$FILE_PATH').read())
except Exception as e: print(str(e)); sys.exit(1)
" 2>&1)
        if [ $? -ne 0 ]; then
            ERRORS="[LINT] HTML error in $FILE_PATH:\n$RESULT"
        fi
        ;;
    css)
        # CSS: basic brace matching
        OPEN=$(grep -o '{' "$FILE_PATH" | wc -l)
        CLOSE=$(grep -o '}' "$FILE_PATH" | wc -l)
        if [ "$OPEN" -ne "$CLOSE" ]; then
            ERRORS="[LINT] CSS brace mismatch in $FILE_PATH: $OPEN open, $CLOSE close"
        fi
        ;;
esac

if [ -n "$ERRORS" ]; then
    echo -e "$ERRORS"
    # Non-blocking: exit 0 so work continues, but Claude sees the error output
    exit 0
fi

exit 0
