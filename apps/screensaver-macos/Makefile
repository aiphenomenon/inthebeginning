# Makefile
# InTheBeginning – macOS Screensaver
#
# Builds the .saver bundle using swiftc directly (no Xcode project required).
# Requires macOS with Xcode Command Line Tools installed.
#
# Usage:
#   make          – build the screensaver bundle
#   make install  – install to ~/Library/Screen Savers/
#   make clean    – remove build artifacts
#   make test     – quick syntax check (compile only, no link)

BUNDLE_NAME     = InTheBeginning
SAVER_BUNDLE    = $(BUNDLE_NAME).saver
MODULE_NAME     = InTheBeginning
INSTALL_DIR     = $(HOME)/Library/Screen Savers

SDKROOT        := $(shell xcrun --show-sdk-path 2>/dev/null || echo /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk)
SWIFT          := swiftc
SWIFT_FLAGS     = -sdk $(SDKROOT) \
                  -target x86_64-apple-macos12.0 \
                  -module-name $(MODULE_NAME) \
                  -framework ScreenSaver \
                  -framework AppKit

SOURCES         = InTheBeginning/Simulator/Constants.swift \
                  InTheBeginning/Simulator/QuantumField.swift \
                  InTheBeginning/Simulator/AtomicSystem.swift \
                  InTheBeginning/Simulator/ChemicalSystem.swift \
                  InTheBeginning/Simulator/Environment.swift \
                  InTheBeginning/Simulator/Biosphere.swift \
                  InTheBeginning/Simulator/Universe.swift \
                  InTheBeginning/InTheBeginningView.swift

BUNDLE_CONTENTS = $(SAVER_BUNDLE)/Contents
BUNDLE_MACOS    = $(BUNDLE_CONTENTS)/MacOS
BUNDLE_PLIST    = InTheBeginning/Info.plist

.PHONY: all build install clean test

all: build

build: $(SAVER_BUNDLE)

$(SAVER_BUNDLE): $(SOURCES) $(BUNDLE_PLIST)
	@echo "==> Building $(SAVER_BUNDLE)..."
	@mkdir -p "$(BUNDLE_MACOS)"
	$(SWIFT) $(SWIFT_FLAGS) \
		-emit-library \
		-o "$(BUNDLE_MACOS)/$(BUNDLE_NAME)" \
		$(SOURCES)
	@cp "$(BUNDLE_PLIST)" "$(BUNDLE_CONTENTS)/Info.plist"
	@echo "==> Built $(SAVER_BUNDLE) successfully."

install: build
	@echo "==> Installing to $(INSTALL_DIR)..."
	@mkdir -p "$(INSTALL_DIR)"
	@rm -rf "$(INSTALL_DIR)/$(SAVER_BUNDLE)"
	@cp -R "$(SAVER_BUNDLE)" "$(INSTALL_DIR)/$(SAVER_BUNDLE)"
	@echo "==> Installed. Select '$(BUNDLE_NAME)' in System Preferences > Screen Saver."

clean:
	@echo "==> Cleaning..."
	@rm -rf "$(SAVER_BUNDLE)"
	@echo "==> Clean."

test:
	@echo "==> Syntax check (compile only)..."
	$(SWIFT) $(SWIFT_FLAGS) \
		-typecheck \
		$(SOURCES)
	@echo "==> All files passed syntax check."
