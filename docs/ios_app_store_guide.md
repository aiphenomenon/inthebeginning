# In The Beginning -- iOS App Store Deployment Guide

A complete, end-to-end guide for building and deploying the **In The Beginning**
cosmic evolution simulator to the Apple App Store. This guide covers every step
from setting up a fresh Mac through a public App Store release.

This guide uses **only** Xcode, the Mac App Store, and Apple's built-in tools.
No Homebrew, no CocoaPods, no third-party package managers, and no command-line
tools beyond optionally verifying the simulator library with `swift build`.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Apple Developer Program](#2-apple-developer-program)
3. [Project Setup in Xcode](#3-project-setup-in-xcode)
4. [Configuring the Project](#4-configuring-the-project)
5. [Building in Xcode](#5-building-in-xcode)
6. [Running in Simulator](#6-running-in-simulator)
7. [Running on Physical Device](#7-running-on-physical-device)
8. [App Store Connect Setup](#8-app-store-connect-setup)
9. [Archive and Upload](#9-archive-and-upload)
10. [TestFlight](#10-testflight)
11. [App Review and Release](#11-app-review-and-release)
12. [General Public Release](#12-general-public-release)

---

## 1. Prerequisites

### macOS Version

This project requires **macOS 14 (Sonoma) or later**. The `Package.swift`
declares `.macOS(.v14)` as a platform minimum, and Xcode 15+ requires Sonoma.
To verify your macOS version:

1. Click the Apple menu in the top-left corner of the screen.
2. Select **About This Mac**.
3. Confirm the version is 14.0 or later.

If you need to upgrade, open **System Settings > General > Software Update** and
install the latest macOS release.

### Hardware

- A Mac with Apple silicon (M1, M2, M3, M4, or later) is strongly recommended.
  The app uses Metal for GPU rendering, and Apple silicon Macs have the best
  Metal support and can run iOS apps natively.
- At least 16 GB of free disk space for Xcode and related tools.
- At least 8 GB of RAM (16 GB recommended for comfortable development).

### Xcode Installation

Install Xcode exclusively from the Mac App Store:

1. Open the **App Store** app on your Mac.
2. Search for **Xcode**.
3. Click **Get**, then **Install**. Xcode is free but large (approximately
   12 GB download, expanding to roughly 35 GB on disk).
4. Wait for the download and installation to complete.
5. Launch Xcode from your Applications folder or Launchpad.
6. On first launch, Xcode will prompt you to install **additional components**
   (iOS simulator runtimes, command-line tools). Click **Install** and enter
   your Mac administrator password when prompted.
7. Accept the Xcode license agreement.

Verify the installation:

1. Open Xcode.
2. Go to **Xcode > About Xcode** in the menu bar.
3. Confirm the version is **15.0 or later** (Xcode 15 ships with Swift 5.9,
   which this project requires).

### iOS Simulator Runtime

Xcode typically installs the latest iOS simulator runtime automatically. Since
this app targets iOS 17, you need at least the iOS 17 simulator:

1. Open Xcode.
2. Go to **Xcode > Settings** (or **Xcode > Preferences** on older versions).
3. Click the **Platforms** tab.
4. If iOS 17 (or later) is not listed, click the **+** button in the lower left
   and select the iOS simulator runtime to download.

### Apple ID

You need an Apple ID. If you do not have one:

1. Go to https://appleid.apple.com.
2. Click **Create Your Apple ID** and follow the steps.

---

## 2. Apple Developer Program

### Why You Need It

A free Apple ID lets you run apps on your own device and use the simulator, but
to distribute on the App Store you must enroll in the **Apple Developer
Program** ($99 USD per year).

### Enrollment Steps

1. Open Safari and navigate to https://developer.apple.com/programs/.
2. Click **Enroll**.
3. Sign in with your Apple ID.
4. If you are enrolling as an individual, select **Individual / Sole
   Proprietor**. If you are enrolling on behalf of an organization, select
   **Organization** (this requires a D-U-N-S number).
5. Fill in your legal name, address, and contact information.
6. Review and accept the Apple Developer Program License Agreement.
7. Pay the $99 USD annual fee.
8. Apple may take up to 48 hours to process your enrollment. You will receive
   an email when your account is active.

### Setting Up Certificates via Xcode (Automatic Signing)

Once enrolled, configure Xcode to manage your signing identity automatically.
There is no need to use the command line, Keychain Access, or the Apple
Developer portal manually.

1. Open Xcode.
2. Go to **Xcode > Settings > Accounts**.
3. Click the **+** button in the lower left.
4. Select **Apple ID** and sign in with the Apple ID associated with your
   Developer Program membership.
5. After signing in, your account appears in the list. Select it and click
   **Manage Certificates**.
6. If no certificates are listed, click the **+** button and select **Apple
   Development**. Xcode will automatically create a development signing
   certificate and install it in your keychain.
7. For distribution, Xcode creates the **Apple Distribution** certificate
   automatically when you first archive the app (covered in Section 9). You
   do not need to create it manually.

---

## 3. Project Setup in Xcode

The In The Beginning source code is organized as a Swift Package Manager (SPM)
project with a `Package.swift` manifest. Since the app uses Metal (which requires
Xcode for shader compilation) and platform-specific features, you need an Xcode
project or workspace.

### Option A: Create a New Xcode Project and Import Source Files (Recommended)

This approach gives you full control over all Xcode build settings.

#### Step 1: Create the Xcode Project

1. Open Xcode.
2. Select **File > New > Project** (or press Cmd+Shift+N).
3. Under the **iOS** tab at the top, select **App**.
4. Click **Next**.
5. Configure the project:
   - **Product Name**: `InTheBeginning`
   - **Team**: Select your Apple Developer team (the one you enrolled in
     Section 2). If no team appears, go to Xcode > Settings > Accounts and
     verify your Apple ID is added.
   - **Organization Identifier**: Enter a reverse-DNS identifier you own, for
     example `com.yourname` or `com.yourcompany`. This combined with the
     product name forms the **Bundle Identifier** (e.g.,
     `com.yourname.InTheBeginning`).
   - **Interface**: Select **SwiftUI**.
   - **Language**: Select **Swift**.
   - **Storage**: Select **None** (the app does not use Core Data or
     SwiftData).
   - Leave **Include Tests** unchecked (you can add tests later).
6. Click **Next**.
7. Choose a location on disk to save the project (e.g., your Desktop or a
   projects folder). Click **Create**.

#### Step 2: Remove the Template Files

Xcode creates template files (`ContentView.swift`,
`InTheBeginningApp.swift`, and `Assets.xcassets`). You will replace these:

1. In the Project Navigator (left sidebar), select the generated
   `InTheBeginningApp.swift` file.
2. Press Delete and choose **Move to Trash**.
3. Delete `ContentView.swift` the same way.
4. Keep `Assets.xcassets` -- you will use it for the app icon later.

#### Step 3: Add the Source Files

1. In Finder, navigate to the source code directory:
   ```
   apps/swift/InTheBeginning/
   ```
2. Select all the Swift files and the Renderer/Shaders.metal file:
   - `App.swift`
   - `Views/SimulationView.swift`
   - `Views/EpochTimelineView.swift`
   - `Views/SettingsView.swift`
   - `Renderer/MetalRenderer.swift`
   - `Renderer/Shaders.metal`
   - `Audio/AudioEngine.swift`
   - `Simulator/Constants.swift`
   - `Simulator/QuantumField.swift`
   - `Simulator/AtomicSystem.swift`
   - `Simulator/ChemicalSystem.swift`
   - `Simulator/Biosphere.swift`
   - `Simulator/Environment.swift`
   - `Simulator/Universe.swift`
3. Drag all selected files into the Project Navigator in Xcode, dropping them
   into the `InTheBeginning` group.
4. In the dialog that appears:
   - Check **Copy items if needed**.
   - Make sure **Create groups** is selected (not "Create folder references").
   - Ensure the **InTheBeginning** target is checked under **Add to targets**.
   - Click **Finish**.

You can optionally organize the files into groups (Simulator, Views, Renderer,
Audio) by right-clicking in the Project Navigator and selecting **New Group**,
then dragging files into the appropriate groups. This is cosmetic and does not
affect the build.

#### Step 4: Add the Info.plist

1. In Finder, locate `apps/swift/Info.plist`.
2. Drag it into the project root in the Project Navigator.
3. Check **Copy items if needed** and click **Finish**.
4. In the Project Navigator, click the top-level project node (blue icon).
5. Select the **InTheBeginning** target.
6. Go to the **Build Settings** tab.
7. Search for `Info.plist File`.
8. Set the value to `InTheBeginning/Info.plist` (or wherever the file was
   placed relative to the project root).

### Option B: Open Package.swift Directly in Xcode

For development and testing (but not for archiving/uploading to the App Store),
you can open the package directly:

1. In Finder, navigate to `apps/swift/`.
2. Double-click `Package.swift`. Xcode opens it as a Swift Package.
3. Xcode will resolve the package structure and display both targets:
   `InTheBeginningSimulator` (library) and `InTheBeginning` (executable).
4. Select the `InTheBeginning` scheme in the scheme selector.

**Important**: This approach works for building and running in the simulator,
but for App Store distribution you will need a full `.xcodeproj` or
`.xcworkspace` to configure signing, entitlements, and app metadata. Use
Option A for the final submission workflow.

### Setting the Bundle Identifier

The Bundle Identifier must be unique across the entire App Store.

1. Click the project in the Project Navigator (blue icon at the top).
2. Select the **InTheBeginning** target.
3. Go to the **General** tab.
4. Under **Identity**, set:
   - **Display Name**: `In The Beginning`
   - **Bundle Identifier**: `com.yourname.InTheBeginning` (replace `yourname`
     with your actual identifier).
   - **Version**: `1.0` (matches `CFBundleShortVersionString` in Info.plist).
   - **Build**: `1` (matches `CFBundleVersion` in Info.plist). Increment this
     for each upload to App Store Connect.

### Setting the Team and Signing

1. Still on the **General** tab under **Signing & Capabilities** (or the
   **Signing & Capabilities** tab):
   - Check **Automatically manage signing**.
   - Select your **Team** from the dropdown.
   - Xcode automatically creates a provisioning profile and resolves the
     signing identity.
2. If you see a red error about the Bundle Identifier being unavailable,
   your chosen identifier is already taken. Modify it to be unique.

---

## 4. Configuring the Project

### Deployment Target

The `Package.swift` specifies `.iOS(.v17)`. Set this in the Xcode project:

1. Click the project in the Project Navigator.
2. Select the **InTheBeginning** target.
3. Go to the **General** tab.
4. Under **Minimum Deployments**, set **iOS** to **17.0**.

This means the app will run on iPhones and iPads with iOS 17 or later.

### Device Capabilities

The Info.plist already declares `UIRequiredDeviceCapabilities` with `armv7`.
For an app that uses Metal rendering, consider updating this:

1. Select the **InTheBeginning** target.
2. Go to the **General** tab (or **Info** tab).
3. Under **Custom iOS Target Properties**, find `Required device capabilities`
   (UIRequiredDeviceCapabilities).
4. Change `armv7` to `metal` to ensure the app only installs on devices with
   Metal GPU support. Virtually all iOS devices from iPhone 5s onward support
   Metal, so this is not overly restrictive.

You can make this edit in Xcode or by editing Info.plist directly:

Replace:
```xml
<key>UIRequiredDeviceCapabilities</key>
<array>
    <string>armv7</string>
</array>
```

With:
```xml
<key>UIRequiredDeviceCapabilities</key>
<array>
    <string>metal</string>
</array>
```

### Supported Orientations

The Info.plist already configures orientations. Verify them:

- **iPhone**: Portrait, Landscape Left, Landscape Right (no upside-down).
- **iPad**: All four orientations.

This is appropriate for a simulation app where users may want to hold the
device in any orientation. No changes are needed.

### App Icons

Apple requires app icons in multiple sizes. You need a single 1024x1024 pixel
PNG image (no transparency, no rounded corners -- Apple applies the rounding
automatically).

1. Create or commission a 1024x1024 PNG icon. For In The Beginning, consider
   an image that evokes cosmic origins: a bright singularity expanding, or
   particle trails on a dark background.
2. In the Project Navigator, click **Assets.xcassets**.
3. Select **AppIcon** in the asset catalog sidebar.
4. In Xcode 15 and later with the "Single Size" icon option, drag your
   1024x1024 PNG into the **All Sizes (1024x1024)** well.
5. If your project uses the older multi-size format, drag the same 1024x1024
   image into the **App Store - iOS 1024pt** slot. Xcode will derive all
   other sizes automatically if you enable **Single Size** under the
   Attributes Inspector (right sidebar) by setting **iOS** to **Single Size**.

### Launch Screen

The Info.plist already configures a launch screen via `UILaunchScreen` with
a system background color. This creates a clean solid-color launch screen
with no storyboard file needed.

If you want a more branded launch screen:

1. Select the **InTheBeginning** target.
2. Go to the **General** tab.
3. Under **App Icons and Launch Screen**, you will see **Launch Screen**
   settings.
4. For a simple approach, keep the current Info.plist-based launch screen
   (a solid dark background matches the app's `.preferredColorScheme(.dark)`).
5. For a more custom approach:
   - Select **File > New > File**.
   - Choose **Launch Screen** (under User Interface).
   - Name it `LaunchScreen` and add it to the target.
   - Design it in Interface Builder (e.g., add a centered image or title text
     on a dark background).
   - In the target's General tab, set the **Launch Screen File** to
     `LaunchScreen`.

### Frameworks

The app uses the following Apple frameworks, all of which are included
automatically -- no linking configuration is needed:

- **SwiftUI** -- User interface (imported in App.swift, all Views).
- **Metal** and **MetalKit** -- GPU rendering (imported in MetalRenderer.swift,
  conditionally with `#if canImport(MetalKit)`).
- **AVFoundation** -- Audio synthesis (imported in AudioEngine.swift,
  conditionally with `#if canImport(AVFoundation)`).
- **Foundation** -- Standard library (imported in all Simulator files).
- **Observation** -- Observable macro (imported in Universe.swift).
- **simd** -- Vector/matrix math (used via Metal and Accelerate, implicitly
  available).

---

## 5. Building in Xcode

### Debug Build

1. In the scheme selector (top center of the Xcode toolbar), select the
   **InTheBeginning** scheme. If it does not exist, click the scheme selector,
   choose **Manage Schemes**, and click **+** to add one for the
   InTheBeginning target.
2. Select a destination device next to the scheme (e.g., **iPhone 15 Pro**
   simulator or a connected physical device).
3. Press **Cmd+B** to build, or select **Product > Build** from the menu bar.
4. The build status appears in the activity area at the top of the Xcode
   window. A "Build Succeeded" message appears when the build completes.

If errors occur:

- Check that all 14 source files are added to the target (Project Navigator >
  select each file > File Inspector > verify **Target Membership** checkbox is
  checked for InTheBeginning).
- Ensure `Shaders.metal` is listed under **Build Phases > Compile Sources**
  for the target.
- Ensure the deployment target is set to iOS 17.0 or later.

### Release Build

For testing performance with optimizations enabled:

1. Go to **Product > Scheme > Edit Scheme** (or press Cmd+Shift+<).
2. Select the **Run** action in the left sidebar.
3. Change **Build Configuration** from **Debug** to **Release**.
4. Click **Close**.
5. Press **Cmd+B** to build.

The Release build enables compiler optimizations (`-O`), strips debug symbols,
and produces faster code. Metal shaders are compiled with optimizations as well.

Switch back to Debug when you need breakpoints and debug logging.

### Key Build Settings

These settings are configured automatically by Xcode but are worth understanding:

| Setting | Value | Reason |
|---------|-------|--------|
| SWIFT_VERSION | 5.9 | Matches Package.swift swift-tools-version |
| IPHONEOS_DEPLOYMENT_TARGET | 17.0 | Minimum iOS version |
| ARCHS | arm64 | All modern iOS devices use arm64 |
| METAL_LIBRARY_OUTPUT_DIR | (auto) | Xcode compiles .metal files into default.metallib |
| ENABLE_BITCODE | NO | Bitcode is deprecated since Xcode 14 |
| SWIFT_OPTIMIZATION_LEVEL | -Onone (Debug) / -O (Release) | Performance optimization |

---

## 6. Running in Simulator

### Selecting a Simulator Device

1. In the scheme selector toolbar, click the device destination.
2. A list of available simulators appears, organized by device type.
3. **Recommended choices** for this app:
   - **iPhone 15 Pro** or **iPhone 16 Pro** -- Standard phone form factor.
   - **iPad Pro 13-inch (M4)** -- Tests iPad layout with all four orientations.
4. Click a simulator to select it.

### Running the App

1. Press **Cmd+R** or click **Product > Run**.
2. The iOS Simulator app launches automatically.
3. The In The Beginning app installs and launches in the simulator.
4. You should see:
   - A dark gradient background (Planck epoch).
   - The top bar showing "Planck" with "All forces unified, T~10^32K".
   - An epoch timeline at the bottom.
   - A control bar with play, reset, speed slider, and settings buttons.
5. Tap the **play button** to start the simulation.
6. Particles appear and the simulation advances through cosmic epochs.

### Simulator Limitations

- **Metal**: The iOS Simulator on Apple silicon Macs supports Metal rendering.
  On Intel Macs, Metal is not available in the simulator, and the Metal
  renderer will not initialize (the app falls back to the Canvas-based
  SwiftUI rendering in `SimulationView` since `MetalRenderer` is wrapped
  in `#if canImport(MetalKit)`).
- **Audio**: AVAudioEngine works in the simulator but audio quality and latency
  may differ from a real device.
- **Performance**: Simulator performance is not representative of device
  performance. Always test on a real device for performance profiling.

### Debugging with Breakpoints

1. Open a source file in the editor (e.g., `Universe.swift`).
2. Click in the gutter (the gray area to the left of the line numbers) to set
   a breakpoint. A blue arrow appears.
3. Run the app (Cmd+R). Execution pauses when the breakpoint is hit.
4. Use the Debug area at the bottom of Xcode:
   - **Variables View** (left pane): Inspect local and instance variables.
   - **Console** (right pane): Type LLDB commands like `po universe.tick` or
     `p universe.currentEpoch`.
5. Use the debugger controls:
   - **Continue** (Cmd+Ctrl+Y): Resume execution.
   - **Step Over** (F6): Execute the current line and move to the next.
   - **Step Into** (F7): Enter a function call.
   - **Step Out** (F8): Return from the current function.

### Console Output

- **View > Debug Area > Show Debug Area** (or Cmd+Shift+Y) to show the
  console.
- `print()` statements in the code appear here (e.g., the MetalRenderer logs
  "Failed to load shader library" on error).
- The simulation's event log (displayed in the UI) also tracks epoch
  transitions, nucleosynthesis events, and abiogenesis milestones.

---

## 7. Running on Physical Device

Running on a real iPhone or iPad is essential for testing Metal rendering
performance, audio fidelity, and touch interactions.

### Connecting Your Device

1. Connect your iPhone or iPad to your Mac using a USB or USB-C cable.
2. If prompted on the device, tap **Trust This Computer** and enter your
   device passcode.
3. In Xcode's device selector (the destination dropdown in the toolbar), your
   device should appear under **iOS Devices** with its name.

### First-Time Setup: Developer Mode

On iOS 16 and later, you must enable Developer Mode on the device:

1. On the iPhone/iPad, go to **Settings > Privacy & Security > Developer
   Mode**.
2. Toggle **Developer Mode** on.
3. The device will restart. After restarting, confirm when prompted.

### Trusting the Developer Certificate

The first time you run an app from Xcode on a device:

1. Build and run (Cmd+R) targeting your physical device.
2. The app installs but may not launch. You may see an "Untrusted Developer"
   alert on the device.
3. On the device, go to **Settings > General > VPN & Device Management**
   (or **Profiles & Device Management** on older iOS versions).
4. Under **Developer App**, tap your Apple ID / team name.
5. Tap **Trust "[Your Name]"** and confirm.
6. Return to the home screen and launch the app, or run again from Xcode.

### Running and Testing on Device

1. Select your physical device in the destination selector.
2. Press **Cmd+R**.
3. The app installs on the device and launches.
4. Test the following device-specific features:
   - **Metal rendering performance**: The MetalRenderer should initialize
     successfully on any device running iOS 17. Check that particles render
     smoothly at 60 fps. The simulation uses instanced point rendering with
     up to 2000 particles (configurable down to 500 in the Settings view).
   - **Audio**: Toggle sonification on in the Settings view. You should hear
     ambient chord tones that change with each epoch transition. The audio
     uses AVAudioEngine with four sine-wave source nodes mapped to epoch-
     specific chord frequencies.
   - **Orientation**: Rotate the device to test portrait and landscape modes.
   - **Thermal behavior**: Run the simulation at maximum speed (20x) for
     several minutes. Monitor whether the device becomes excessively warm.
     If needed, the `SimulationLimits.maxParticlesBattery` (800) and
     `maxParticlesLowPerf` (500) constants provide lower particle counts for
     battery-conscious operation.

### Wireless Debugging (Optional)

After connecting via USB at least once:

1. Go to **Window > Devices and Simulators** in Xcode.
2. Select your device.
3. Check **Connect via network**.
4. Once paired (a globe icon appears next to the device name), you can
   disconnect the USB cable and run/debug wirelessly, provided both the Mac
   and device are on the same Wi-Fi network.

---

## 8. App Store Connect Setup

App Store Connect is the web portal where you manage your app's metadata,
screenshots, pricing, and submissions.

### Accessing App Store Connect

1. Open Safari and navigate to https://appstoreconnect.apple.com.
2. Sign in with your Apple Developer account.

### Creating the App Record

1. On the App Store Connect dashboard, click **My Apps**.
2. Click the **+** button in the top left and select **New App**.
3. Fill in the required fields:
   - **Platforms**: Check **iOS**.
   - **Name**: `In The Beginning` (this is the name shown on the App Store;
     it must be unique across the App Store and no longer than 30 characters).
   - **Primary Language**: English (U.S.) (or your preferred language).
   - **Bundle ID**: Select the Bundle Identifier you configured in Xcode
     (e.g., `com.yourname.InTheBeginning`). If it does not appear in the
     dropdown, ensure your Xcode project has been built at least once with
     automatic signing enabled, which registers the Bundle ID with Apple.
   - **SKU**: Enter a unique internal identifier, e.g., `INTHEBEGINNING001`.
     This is never shown to users.
   - **User Access**: Choose **Full Access** unless you have specific team
     access control needs.
4. Click **Create**.

### App Information

After creating the app, you land on the App Information page. Fill in:

1. **Subtitle** (optional, up to 30 characters): `Cosmic Evolution Simulator`
2. **Category**:
   - **Primary Category**: **Education**
   - **Secondary Category**: **Entertainment** (or **Simulation** if listed
     under Games -- but since this is a scientific simulation, Education is
     more appropriate and avoids being categorized with games).
3. **Content Rights**: Confirm that you have the rights to distribute this
   content.
4. **Age Rating**: Click **Edit** and answer the questionnaire. For In The
   Beginning:
   - No violence, no mature content, no gambling, no horror.
   - Select **None** or **Infrequent** for all categories.
   - The likely rating is **4+** (suitable for all ages).

### Pricing and Availability

1. Click **Pricing and Availability** in the sidebar.
2. **Price**: Select **Free** (Price Tier 0). The app does not have in-app
   purchases in its current form.
3. **Availability**: Select **All territories** to make the app available
   worldwide, or choose specific countries.

### Privacy Policy

Apple requires a privacy policy URL for all apps.

1. Create a privacy policy that describes what data the app collects. Since
   In The Beginning is an offline simulation with no networking, analytics,
   or data collection, the privacy policy can be brief. It should state:
   - The app does not collect any personal data.
   - The app does not transmit any data over the network.
   - The app does not use third-party analytics or advertising SDKs.
2. Host the privacy policy at a publicly accessible URL (e.g., on your
   personal website, a GitHub Pages site, or a free hosting service).
3. Enter the URL in the **Privacy Policy URL** field on the App Information
   page.

### App Privacy (Data Collection)

1. In App Store Connect, navigate to **App Privacy**.
2. Click **Get Started**.
3. When asked "Do you or your third-party partners collect data from this
   app?", select **No, we do not collect data from this app**.
4. Click **Save**.

The app's Info.plist already declares `ITSAppUsesNonExemptEncryption` as
`false`, which means the app does not use encryption beyond standard HTTPS
(and in fact uses no networking at all). This avoids the export compliance
questionnaire.

### Preparing Screenshots

Apple requires screenshots for the App Store listing. You need screenshots for
at least one device size. For full coverage, provide screenshots for:

- **6.9-inch** (iPhone 16 Pro Max) -- 1320 x 2868 pixels
- **6.7-inch** (iPhone 15 Pro Max / 14 Pro Max) -- 1290 x 2796 pixels
- **6.5-inch** (iPhone 15 Plus / 14 Plus) -- 1284 x 2778 pixels
- **iPad Pro 13-inch** -- 2064 x 2752 pixels

To capture screenshots:

1. Run the app in the Simulator using the appropriate device size.
2. Advance the simulation to interesting visual states:
   - **Planck / Inflation epoch**: Bright, high-energy particles.
   - **Nucleosynthesis**: Atoms forming from particles.
   - **Star Formation**: Stars igniting, heavier elements.
   - **Earth / Life**: Molecules, water, amino acids, first cells.
   - **Settings view**: Showing the configuration options.
3. In the Simulator, press **Cmd+S** to save a screenshot to your Desktop.
4. Alternatively, in Xcode's Debug menu, select **Debug > Simulate Screenshot**
   to capture the screen.

You need at minimum 3 screenshots and can provide up to 10 per device size.
Aim for 5-6 screenshots showing different epochs and features.

### App Store Metadata

On the version page (e.g., "Version 1.0"), fill in:

1. **Description** (up to 4000 characters). Example:

   > In The Beginning is a real-time cosmic evolution simulator that models the
   > entire history of the universe, from the Planck epoch through the emergence
   > of life.
   >
   > Watch as quantum fluctuations seed the structure of spacetime, quarks confine
   > into protons and neutrons, nucleosynthesis forges the lightest elements, atoms
   > form as the universe cools, stars ignite and forge heavier elements, our solar
   > system coalesces, Earth forms with oceans, and self-replicating molecules give
   > rise to the first living cells.
   >
   > Features:
   > - 13 scientifically-grounded cosmic epochs from Planck to Present
   > - Real-time particle simulation with adjustable speed and particle count
   > - Metal-accelerated GPU rendering with epoch-specific visual themes
   > - Audio sonification mapping cosmic evolution to musical harmonies
   > - Live statistics: temperature, particle counts, atoms, molecules, cells
   > - Interactive epoch timeline with detailed descriptions
   > - Supports iPhone and iPad in all orientations
   >
   > Built with SwiftUI, Metal, and AVAudioEngine using real physical constants
   > scaled for computational tractability. Educational and mesmerizing.

2. **Keywords** (up to 100 characters, comma-separated):
   `simulation,universe,physics,cosmology,big bang,evolution,science,education,particles,atoms`

3. **Support URL**: A URL where users can get help (your website, a GitHub
   repository issues page, or an email contact page).

4. **Marketing URL** (optional): Your app's marketing website.

5. **Promotional Text** (up to 170 characters; can be updated without a new
   submission):
   `Witness the birth of the universe. From quantum foam to living cells, watch 13.8 billion years of cosmic evolution unfold in real time.`

6. **What's New in This Version**: For the initial release, write:
   `Initial release. Explore the complete cosmic evolution from the Big Bang to the emergence of life.`

---

## 9. Archive and Upload

### Preparing for Archive

Before archiving, make sure:

1. The scheme is set to **Any iOS Device (arm64)** as the destination. You
   cannot archive with a simulator selected.
   - In the destination selector, scroll past the simulators and select
     **Any iOS Device (arm64)**.
2. The build configuration for the **Archive** action is set to **Release**
   (this is the default and should not need changing).
3. The version number (e.g., `1.0`) and build number (e.g., `1`) are set
   correctly in the target's General tab. Each upload to App Store Connect
   requires a unique build number, so increment it for each upload.

### Creating the Archive

1. Go to **Product > Archive** in the Xcode menu bar.
2. Xcode performs a clean Release build for arm64.
3. If errors occur, fix them and try again. Common issues:
   - Missing signing identity: Ensure your team is selected and automatic
     signing is enabled.
   - Metal shader compilation errors: Ensure `Shaders.metal` compiles without
     warnings. The shader uses standard Metal Shading Language features
     (point sprites, instanced rendering, smoothstep).
4. When the build succeeds, the **Organizer** window opens automatically,
   showing your new archive.

### The Organizer

The Organizer (accessible anytime via **Window > Organizer**) lists all your
archives. Each archive includes:

- The compiled app binary.
- Debug symbols (dSYMs) for crash report symbolication.
- The signing identity and provisioning profile used.

### Uploading to App Store Connect

1. In the Organizer, select the archive you just created.
2. Click **Distribute App**.
3. Select **App Store Connect** as the distribution method.
4. Click **Next**.
5. Select **Upload** (not "Export" -- Export creates an IPA for manual
   distribution; Upload sends directly to App Store Connect).
6. On the distribution options screen:
   - **Strip Swift symbols**: Leave checked (reduces app size).
   - **Upload your app's symbols**: Leave checked (enables Apple to
     symbolicate crash reports for you).
   - **Manage Version and Build Number**: Leave checked (Xcode verifies and
     increments if needed).
7. Click **Next**.
8. Xcode automatically selects the appropriate **Distribution certificate**
   (Apple Distribution) and **provisioning profile**. If this is your first
   time, Xcode will create them. Verify the selections look correct.
9. Click **Upload**.
10. Xcode uploads the build to App Store Connect. This may take several
    minutes depending on your internet connection and the binary size.
11. When the upload completes, you see a success message.

### Post-Upload Processing

After uploading:

1. Log in to App Store Connect at https://appstoreconnect.apple.com.
2. Navigate to **My Apps > In The Beginning**.
3. Go to the **TestFlight** tab.
4. Your build appears with a status of **Processing**. Apple's servers
   analyze the binary for issues. This typically takes 5-30 minutes.
5. If processing succeeds, the build status changes to **Ready to Submit**
   (for App Store) or **Ready for Testing** (for TestFlight).
6. If processing fails, you receive an email describing the issues. Common
   processing issues:
   - Missing app icon.
   - Invalid binary architecture.
   - Missing privacy manifest (for apps using certain APIs). Since In The
     Beginning does not use tracking APIs, this is unlikely.

---

## 10. TestFlight

TestFlight allows you to distribute pre-release builds to testers before
submitting to the App Store. It is highly recommended to beta test before
your first public release.

### Internal Testing

Internal testers are members of your Apple Developer team (up to 100 people).

1. In App Store Connect, go to **My Apps > In The Beginning > TestFlight**.
2. Under **Internal Group**, click the **+** button to create a group (e.g.,
   "Core Testers").
3. Click **Add Testers** and enter the Apple IDs (email addresses) of your
   internal testers.
4. Select the build you uploaded and click **Enable Automatic Distribution**
   for the internal group, or manually add the build.
5. Internal testers receive an email invitation to install the TestFlight app
   (free on the App Store) and test your app.
6. Internal builds do **not** require Beta App Review. They are available
   immediately.

### External Testing

External testers are people outside your development team (up to 10,000).

1. In TestFlight, click **External Testing** and create a group (e.g.,
   "Beta Testers").
2. Add testers by email or share a public TestFlight link.
3. When you add a build to an external testing group for the first time,
   Apple performs a **Beta App Review**. This typically takes 24-48 hours.
4. Fill in the required information:
   - **Test Information**: Describe what testers should focus on (e.g.,
     "Test the simulation from Planck epoch through Present. Try adjusting
     speed and particle count in Settings. Report any visual glitches,
     crashes, or audio issues.").
   - **Contact Information**: Your email for testers to reach you.
   - **Privacy Policy URL**: The same one from Section 8.
5. Once approved, external testers receive an invitation.

### What Testers Should Verify

Provide testers with guidance. Suggested test cases for In The Beginning:

- [ ] App launches without crashing.
- [ ] Tapping Play starts the simulation from Planck epoch.
- [ ] Particles appear and animate smoothly.
- [ ] Epoch transitions are logged and the timeline updates.
- [ ] All 13 epochs are reachable (run at maximum speed).
- [ ] Simulation completes at "Present" epoch (tick 300,000).
- [ ] Reset button clears state and returns to Planck.
- [ ] Speed slider adjusts simulation speed (0.25x to 10x via slider,
      up to 20x via swipe gesture).
- [ ] Settings view opens and all controls function.
- [ ] Visualization style picker works (Particles, Glow, Minimal, Heatmap).
- [ ] Audio toggle enables/disables sonification.
- [ ] When audio is on, chord tones change at epoch transitions.
- [ ] Stats overlay shows correct data (particle count, temperature, atoms,
      molecules, cells).
- [ ] Event log overlay shows simulation events.
- [ ] App works in both portrait and landscape orientations.
- [ ] App works on iPad with all four orientations.
- [ ] No excessive battery drain or thermal throttling during extended runs.

### Collecting Feedback

- Testers can submit feedback directly through the TestFlight app by taking
  a screenshot (which prompts a feedback dialog) or through the TestFlight
  beta feedback option.
- Monitor the **Feedback** section in App Store Connect under TestFlight.
- Address any reported crashes by downloading the crash logs from App Store
  Connect and symbolizing them with your archive's dSYMs in the Xcode
  Organizer.

---

## 11. App Review and Release

### Submitting for Review

When you are confident the app is ready:

1. In App Store Connect, go to **My Apps > In The Beginning**.
2. Click the version (e.g., **1.0 Prepare for Submission**).
3. Ensure all metadata is complete:
   - Screenshots for all required device sizes.
   - App description, keywords, support URL, privacy policy URL.
   - Age rating questionnaire completed.
   - App privacy information filled out.
4. Under **Build**, click the **+** button and select the build you want to
   submit (the one you uploaded and that passed processing).
5. Under **Version Release**, choose:
   - **Manually release this version** -- You decide when the approved app
     goes live.
   - **Automatically release this version** -- The app goes live immediately
     upon approval.
   - **Automatically release this version after App Review, on a specific
     date** -- Schedule the release.
6. Under **App Review Information**, optionally provide:
   - **Contact Information**: Your name, phone, and email for the review team
     to contact you.
   - **Notes for the reviewer**: Explain the app's purpose. Example:

     > This is a scientific/educational simulation of cosmic evolution. The
     > app models physics from the Big Bang (Planck epoch, ~10^-43 seconds
     > after the origin of the universe) through the emergence of biological
     > life on Earth. It uses real physical constants and models quantum
     > field theory, nucleosynthesis, chemistry, and biological evolution.
     >
     > To see the full simulation:
     > 1. Launch the app.
     > 2. Tap the Play button.
     > 3. Open Settings and set speed to maximum (20x) to advance quickly
     >    through epochs.
     > 4. The simulation progresses through 13 epochs and completes at
     >    "Present" (tick 300,000).
     >
     > The app requires no login, collects no data, and has no in-app
     > purchases or advertisements.

7. Click **Add for Review** (or **Submit for Review**).
8. Confirm the submission.

### Review Timeline

- App Review typically takes **24-48 hours** but can occasionally take
  several days.
- You receive email notifications when the review status changes.
- Check the status anytime in App Store Connect.

### Common Rejection Reasons for This Type of App

The App Store Review Guidelines (https://developer.apple.com/app-store/review/guidelines/)
contain rules that are particularly relevant to simulation and educational apps.
Be aware of these potential rejection reasons:

#### Guideline 4.2 -- Minimum Functionality
- **Risk**: Apple may consider the app too simple if it appears to be just an
  animation or screensaver.
- **Mitigation**: The app has substantial interactive features: play/pause/
  reset controls, speed adjustment, particle count configuration, visualization
  style selection, audio toggle, statistics overlay, event log, epoch timeline,
  and a settings view. Highlight these in your reviewer notes.

#### Guideline 2.3.1 -- Accurate Metadata
- **Risk**: If the description overpromises (e.g., claiming "accurate physics
  simulation" when the physics is simplified).
- **Mitigation**: Use honest language like "scientifically-grounded" or
  "models based on real physical constants scaled for computational
  tractability." Avoid claiming it is a research-grade physics engine.

#### Guideline 4.3 -- Spam (Similar Apps)
- **Risk**: Low risk, as cosmic evolution simulators are uncommon on the
  App Store.
- **Mitigation**: None needed unless you publish multiple similar apps.

#### Guideline 2.1 -- App Completeness
- **Risk**: The reviewer may not understand how to use the app and assume
  it is incomplete.
- **Mitigation**: Provide clear reviewer notes (as shown above) explaining
  how to run the simulation and what to expect at each epoch.

#### Guideline 1.1.6 -- Realistic Simulations
- **Risk**: Very low. This guideline targets violent or dangerous simulations.
  A cosmic evolution simulator is not violent.
- **Mitigation**: None needed.

#### Performance Concerns
- **Risk**: If the app crashes during review, it will be rejected.
- **Mitigation**: Test extensively on a real device, especially on an older
  supported device (e.g., iPhone XS, which supports iOS 17). Monitor for
  memory pressure when running at maximum particle count (2000) and speed.

### Responding to Review Feedback

If your app is rejected:

1. You receive an email with a **Resolution Center** link.
2. Open the Resolution Center in App Store Connect.
3. Read the rejection reason carefully.
4. You can:
   - **Reply** to the reviewer with clarifications (e.g., if they
     misunderstood the app's purpose).
   - **Submit a new build** with fixes if the rejection requires code changes.
   - **Appeal** the decision if you believe the rejection is incorrect (use
     the **Appeal** button in App Store Connect or contact
     https://developer.apple.com/contact/app-store/?topic=appeal).
5. Be professional, concise, and specific in your responses.

---

## 12. General Public Release

### Setting Pricing

1. In App Store Connect, go to **Pricing and Availability**.
2. Confirm the price is set to **Free** ($0.00 / Tier 0).
3. If you later want to add a price, you can change it here. Price changes
   take effect within 24 hours.

### Territory Availability

1. Under **Availability**, review the list of territories.
2. For maximum reach, select all 175 territories.
3. If there are legal or content reasons to exclude certain regions, uncheck
   them.

### Releasing the App

If you selected **Manually release this version** during submission:

1. After App Review approval, the status changes to **Pending Developer
   Release**.
2. Go to the version page in App Store Connect.
3. Click **Release This Version**.
4. The app typically appears on the App Store within 24 hours (often within
   a few hours).

### Phased Release

Phased release gradually rolls out the update to users over 7 days. This is
useful for updates, but for your initial launch you may want immediate
availability. To configure:

1. On the version page, under **Phased Release for Automatic Updates**, you
   can enable or disable phased release.
2. For the **initial release (version 1.0)**, phased release does not apply
   because there are no existing users to update. All users who search for
   and download the app get it immediately.
3. For **subsequent updates** (version 1.1, 1.2, etc.), consider enabling
   phased release so that if a critical bug is discovered, you can pause the
   rollout before it reaches all users.

### Monitoring Crash Reports

After release, monitor app stability:

1. In App Store Connect, go to **Analytics** to see download numbers,
   impressions, and engagement.
2. Open Xcode and go to **Window > Organizer > Crashes**.
   - Xcode downloads and symbolicates crash reports from App Store users.
   - Review crash logs to identify bugs.
   - Common areas to monitor for In The Beginning:
     - **MetalRenderer**: GPU resource exhaustion on older devices.
     - **AudioEngine**: AVAudioEngine failures if the audio session is
       interrupted (e.g., phone call).
     - **Universe.advanceTick()**: Potential issues at epoch boundaries
       where subsystems transition.
3. In the Xcode Organizer, the **Energy** and **Metrics** tabs show:
   - Battery usage reports.
   - Launch time metrics.
   - Memory usage.
   - Disk writes.

### Updating the App

To release updates:

1. Increment the **build number** (e.g., from `1` to `2`) for each upload.
   If you also want to change the user-visible version, increment the
   **version number** (e.g., from `1.0` to `1.1`).
2. Make your code changes.
3. Archive and upload as described in Section 9.
4. In App Store Connect, create a new version (e.g., 1.1) under **My Apps >
   In The Beginning**.
5. Add the new build to the version.
6. Fill in **What's New in This Version**.
7. Submit for review.

### Post-Launch Checklist

- [ ] Verify the app appears in App Store search results for relevant terms
      (search for "cosmic simulation," "big bang simulator," "universe
      evolution").
- [ ] Download and install the app from the App Store on a device to confirm
      it works correctly as distributed.
- [ ] Monitor crash reports daily for the first week.
- [ ] Respond to user reviews in App Store Connect under **Ratings and
      Reviews**.
- [ ] Consider writing an App Store feature pitch to Apple's editorial team
      at https://developer.apple.com/contact/app-store/?topic=featuring
      (educational and visually impressive apps are good candidates for
      featuring).

---

## Quick Reference: Complete Workflow Summary

```
1.  Install Xcode from Mac App Store
2.  Enroll in Apple Developer Program ($99/year)
3.  Add Apple ID to Xcode > Settings > Accounts
4.  Create Xcode project, add all source files
5.  Set Bundle ID, team, signing (automatic)
6.  Set deployment target to iOS 17.0
7.  Add app icon (1024x1024 PNG) to Assets.xcassets
8.  Build and test in Simulator (Cmd+R)
9.  Test on physical device via USB
10. Create app record in App Store Connect
11. Fill in all metadata, screenshots, privacy policy
12. Archive: Product > Archive
13. Upload: Organizer > Distribute App > App Store Connect > Upload
14. Beta test via TestFlight (internal + external)
15. Submit for App Review
16. Release to App Store upon approval
17. Monitor crash reports and user feedback
```

---

## Appendix: Project File Reference

All source files for the In The Beginning iOS app:

| File | Purpose |
|------|---------|
| `Package.swift` | Swift Package Manager manifest (iOS 17 / macOS 14 / tvOS 17) |
| `Info.plist` | App configuration (display name, orientations, encryption flag) |
| `App.swift` | @main entry point, creates Universe and SimulationView |
| `Simulator/Constants.swift` | Physical constants, 13 Epoch definitions, simulation limits |
| `Simulator/QuantumField.swift` | Quantum field: particles, pair production, annihilation |
| `Simulator/AtomicSystem.swift` | Nucleosynthesis, recombination, stellar fusion |
| `Simulator/ChemicalSystem.swift` | Water, molecules, amino acids, nucleotides |
| `Simulator/Biosphere.swift` | Abiogenesis, cell division, mutation, natural selection |
| `Simulator/Environment.swift` | Temperature, radiation, atmospheric conditions |
| `Simulator/Universe.swift` | Top-level orchestrator: runs 13 epochs, produces renderables |
| `Renderer/MetalRenderer.swift` | MTKViewDelegate: instanced point rendering on GPU |
| `Renderer/Shaders.metal` | Metal vertex/fragment shaders: particles, atoms, cells |
| `Audio/AudioEngine.swift` | AVAudioEngine: 4-voice sine synthesis, epoch chord mapping |
| `Views/SimulationView.swift` | Main UI: Canvas rendering, controls, stats, event log |
| `Views/EpochTimelineView.swift` | Horizontal scrolling epoch timeline with progress bar |
| `Views/SettingsView.swift` | Settings sheet: speed, particles, visualization, audio |
