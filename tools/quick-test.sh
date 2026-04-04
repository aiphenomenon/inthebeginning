#!/usr/bin/env bash
# tools/quick-test.sh — Targeted test execution based on git diff blast radius.
#
# Analyzes changed files and runs only the tests affected by those changes.
# Three tiers:
#   Tier 1 (always, <5s): Core validation tests
#   Tier 2 (on change, ~30s): Integration tests for affected areas
#   Tier 3 (game code or cut, ~2-5min): Browser E2E tests
#
# Usage:
#   bash tools/quick-test.sh              # Auto-detect from git diff HEAD
#   bash tools/quick-test.sh --all        # Run all tiers
#   bash tools/quick-test.sh --tier1      # Only fast tests
#   bash tools/quick-test.sh --tier2      # Tier 1 + integration
#   bash tools/quick-test.sh --cut        # Full suite for version cut

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[quick-test]${NC} $*"; }
warn() { echo -e "${YELLOW}[quick-test]${NC} $*"; }
fail() { echo -e "${RED}[quick-test]${NC} $*"; }

# ──── Blast Radius Analysis ────

analyze_changes() {
    local changed_files
    changed_files=$(git diff --name-only HEAD 2>/dev/null || echo "")
    if [ -z "$changed_files" ]; then
        changed_files=$(git diff --name-only HEAD~1 2>/dev/null || echo "")
    fi

    CHANGED_SIMULATOR=false
    CHANGED_GAME_JS=false
    CHANGED_DEPLOY=false
    CHANGED_AUDIO=false
    CHANGED_WASM=false
    CHANGED_TESTS=false
    CHANGED_GO=false
    CHANGED_RUST=false
    CHANGED_C=false
    CHANGED_CPP=false
    CHANGED_JAVA=false
    CHANGED_NODEJS=false
    CHANGED_PERL=false
    CHANGED_PHP=false
    CHANGED_TYPESCRIPT=false
    CHANGED_DOCS_ONLY=true

    while IFS= read -r file; do
        [ -z "$file" ] && continue

        case "$file" in
            simulator/*) CHANGED_SIMULATOR=true; CHANGED_DOCS_ONLY=false ;;
            apps/cosmic-runner-v5/js/*|apps/inthebeginning-bounce/js/*|deploy/v*/inthebeginning-bounce/js/*)
                CHANGED_GAME_JS=true; CHANGED_DOCS_ONLY=false ;;
            deploy/shared/audio/*) CHANGED_AUDIO=true; CHANGED_DOCS_ONLY=false ;;
            deploy/*) CHANGED_DEPLOY=true; CHANGED_DOCS_ONLY=false ;;
            apps/wasm-synth/*|apps/wasm/*) CHANGED_WASM=true; CHANGED_DOCS_ONLY=false ;;
            apps/audio/*) CHANGED_AUDIO=true; CHANGED_DOCS_ONLY=false ;;
            apps/go/*) CHANGED_GO=true; CHANGED_DOCS_ONLY=false ;;
            apps/rust/*) CHANGED_RUST=true; CHANGED_DOCS_ONLY=false ;;
            apps/c/*) CHANGED_C=true; CHANGED_DOCS_ONLY=false ;;
            apps/cpp/*) CHANGED_CPP=true; CHANGED_DOCS_ONLY=false ;;
            apps/java/*) CHANGED_JAVA=true; CHANGED_DOCS_ONLY=false ;;
            apps/nodejs/*) CHANGED_NODEJS=true; CHANGED_DOCS_ONLY=false ;;
            apps/perl/*) CHANGED_PERL=true; CHANGED_DOCS_ONLY=false ;;
            apps/php/*) CHANGED_PHP=true; CHANGED_DOCS_ONLY=false ;;
            apps/typescript/*) CHANGED_TYPESCRIPT=true; CHANGED_DOCS_ONLY=false ;;
            tests/*) CHANGED_TESTS=true; CHANGED_DOCS_ONLY=false ;;
            *.md|*.json|session_logs/*|future_memories/*) ;; # docs only
            *) CHANGED_DOCS_ONLY=false ;;
        esac
    done <<< "$changed_files"
}

# ──── Test Runners ────

run_tier1() {
    log "=== Tier 1: Core validation (<5s) ==="
    python3 -m pytest tests/test_note_data_completeness.py tests/test_deploy_assets.py -v --tb=short 2>&1
}

run_tier2() {
    log "=== Tier 2: Integration tests ==="
    local test_files="tests/test_deploy_app_flows.py"

    if $CHANGED_SIMULATOR; then
        test_files="$test_files tests/test_universe.py tests/test_quantum.py tests/test_atomic.py"
        test_files="$test_files tests/test_chemistry.py tests/test_biology.py tests/test_environment.py"
    fi
    if $CHANGED_AUDIO; then
        test_files="$test_files tests/test_audio_golden.py"
    fi

    python3 -m pytest $test_files -v --tb=short 2>&1
}

run_language_tests() {
    log "=== Language-specific tests ==="
    if $CHANGED_GO; then
        log "Running Go tests..."
        (cd apps/go && go test ./... -v) 2>&1
    fi
    if $CHANGED_RUST; then
        log "Running Rust tests..."
        (cd apps/rust && cargo test) 2>&1
    fi
    if $CHANGED_C; then
        log "Running C tests..."
        (cd apps/c && make test) 2>&1
    fi
    if $CHANGED_CPP; then
        log "Running C++ tests..."
        (cd apps/cpp && mkdir -p build && cd build && cmake .. && make && ctest --output-on-failure) 2>&1
    fi
    if $CHANGED_NODEJS; then
        log "Running Node.js tests..."
        node --test apps/nodejs/test/test_simulator.js 2>&1
    fi
    if $CHANGED_PERL; then
        log "Running Perl tests..."
        prove -v apps/perl/t/ 2>&1
    fi
    if $CHANGED_PHP; then
        log "Running PHP tests..."
        (cd apps/php && php tests/run_tests.php) 2>&1
    fi
    if $CHANGED_TYPESCRIPT; then
        log "Running TypeScript tests..."
        (cd apps/typescript && npm test) 2>&1
    fi
}

run_tier3() {
    log "=== Tier 3: Browser E2E tests ==="
    # Check if server is running
    if ! curl -s -o /dev/null http://localhost:8080/v11/inthebeginning-bounce/index.html 2>/dev/null; then
        warn "Starting static file server..."
        python3 -m http.server 8080 --directory deploy --bind 127.0.0.1 &
        sleep 1
    fi
    npx playwright test tests/e2e/game.spec.mjs --config=tests/e2e/playwright.config.mjs --reporter=list 2>&1
}

run_audio_tests() {
    log "=== Audio verification tests ==="
    bash tools/audio-sink.sh --start 2>&1
    xvfb-run -a -s "-screen 0 1280x720x24" bash -c \
        'E2E_AUDIO=1 npx playwright test tests/e2e/audio.spec.mjs tests/e2e/wasm.spec.mjs --config=tests/e2e/playwright.config.mjs --reporter=list 2>&1' \
        | grep -vE "keysym|xkbcomp|libEGL|_XSERV|Warning|Errors from"
}

# ──── Main ────

case "${1:-}" in
    --all|--cut)
        log "Running FULL test suite (version cut)"
        analyze_changes
        run_tier1
        run_tier2
        run_language_tests
        run_tier3
        run_audio_tests
        log "All tests complete."
        ;;
    --tier1)
        analyze_changes
        run_tier1
        ;;
    --tier2)
        analyze_changes
        run_tier1
        run_tier2
        ;;
    *)
        analyze_changes

        if $CHANGED_DOCS_ONLY; then
            log "Only documentation changes detected — skipping tests."
            exit 0
        fi

        # Always run Tier 1
        run_tier1

        # Tier 2 if any code changed
        run_tier2

        # Language-specific tests for changed languages
        run_language_tests

        # Tier 3 if game code changed
        if $CHANGED_GAME_JS || $CHANGED_DEPLOY || $CHANGED_WASM; then
            run_tier3
        else
            log "Game code unchanged — skipping browser E2E tests."
        fi

        log "Targeted tests complete."
        ;;
esac
