# In The Beginning -- Android Build and Google Play Store Deployment Guide

A complete, step-by-step guide for building the **In The Beginning** Kotlin Android
application and publishing it on the Google Play Store. This document covers every
stage from installing prerequisites through post-launch monitoring.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Google Play Developer Account](#2-google-play-developer-account)
3. [Opening the Project in Android Studio](#3-opening-the-project-in-android-studio)
4. [Configuring the Project](#4-configuring-the-project)
5. [Signing Configuration](#5-signing-configuration)
6. [Building in Android Studio](#6-building-in-android-studio)
7. [Running in the Emulator](#7-running-in-the-emulator)
8. [Running on a Physical Device](#8-running-on-a-physical-device)
9. [Building a Release AAB](#9-building-a-release-aab)
10. [Google Play Console Setup](#10-google-play-console-setup)
11. [Internal Testing](#11-internal-testing)
12. [Closed and Open Testing](#12-closed-and-open-testing)
13. [Production Release](#13-production-release)
14. [Post-Launch](#14-post-launch)

---

## 1. Prerequisites

### 1.1 System Requirements

Before you begin, confirm your development machine meets these minimums:

| Requirement        | Windows                   | macOS                    | Linux                     |
|--------------------|---------------------------|--------------------------|---------------------------|
| OS version         | Windows 10 (64-bit)       | macOS 10.14 (Mojave)+   | 64-bit Linux, GNOME/KDE  |
| RAM                | 8 GB minimum, 16 GB recommended | 8 GB minimum, 16 GB recommended | 8 GB minimum, 16 GB recommended |
| Disk space         | 8 GB free (16 GB+ with SDK and emulator images) | Same | Same |
| Screen resolution  | 1280 x 800 minimum       | Same                     | Same                      |

The **In The Beginning** project requires:

- **JDK 17** (the project sets `jvmTarget = "17"` and `JavaVersion.VERSION_17`)
- **Android SDK API level 34** (`compileSdk = 34`, `targetSdk = 34`)
- **Kotlin 1.9.22** (managed by the Gradle plugin)
- **Android Gradle Plugin 8.3.0**

### 1.2 Install JDK 17

Android Studio bundles a JDK, but if you need a standalone installation:

1. Download **Eclipse Temurin JDK 17** from https://adoptium.net/ or use the JDK
   bundled with Android Studio (found under **File > Settings > Build, Execution,
   Deployment > Build Tools > Gradle > Gradle JDK**).
2. On macOS you can also install via Homebrew: `brew install --cask temurin@17`.
3. Verify installation by opening a terminal and running `java -version`. You should
   see output containing `openjdk version "17.x.x"`.

### 1.3 Install Android Studio

1. Visit the official download page:
   **https://developer.android.com/studio**
2. Download the installer for your operating system.
3. Run the installer:
   - **Windows**: Execute the `.exe` file and follow the setup wizard. Accept the
     default installation location.
   - **macOS**: Open the `.dmg` file and drag Android Studio into your Applications
     folder.
   - **Linux**: Extract the archive to a location of your choice (e.g.,
     `/opt/android-studio`) and run `studio.sh` from the `bin/` directory.
4. On first launch, the Android Studio Setup Wizard will appear. Choose **Standard**
   installation type, which installs:
   - Android SDK
   - Android SDK Platform (latest stable)
   - Android Virtual Device (a default emulator image)
5. Accept all license agreements when prompted.

### 1.4 Install the Required SDK Components

After Android Studio finishes the initial setup:

1. Open **Settings** (Windows/Linux: **File > Settings**; macOS: **Android Studio >
   Settings**).
2. Navigate to **Languages & Frameworks > Android SDK**.
3. Under the **SDK Platforms** tab, check **Android 14 (API 34)** and ensure it is
   installed.
4. Under the **SDK Tools** tab, confirm these are installed:
   - Android SDK Build-Tools (34.x.x)
   - Android SDK Platform-Tools
   - Android Emulator
   - Android SDK Command-line Tools
5. Click **Apply**, then **OK** to download and install any missing components.

---

## 2. Google Play Developer Account

You need a Google Play Developer account to publish apps on the Play Store.

### 2.1 Register for a Developer Account

1. Go to **https://play.google.com/console/signup** in a web browser.
2. Sign in with the Google Account you want to use as the developer account.
3. Accept the Google Play Developer Distribution Agreement.
4. Pay the **one-time registration fee of $25 USD** via the payment method linked to
   your Google Account.
5. Complete your account details:
   - **Developer name**: The name displayed publicly on Google Play (e.g., "In The
     Beginning Team" or your organization name).
   - **Contact email**: A publicly visible support email address.
   - **Contact phone number**: Required by Google but not publicly displayed.

### 2.2 Set Up Your Organization Profile

If you are publishing as an organization rather than an individual:

1. In the Google Play Console, go to **Setup > Developer account > Account details**.
2. Select **Organization** as the account type.
3. Provide:
   - Legal organization name
   - Organization address
   - Organization phone number
   - Organization website (if available)
4. Google may require identity verification (submitting a D-U-N-S number or government
   documents). Follow the on-screen prompts if verification is requested.
5. Save your changes.

Account registration can take up to 48 hours to be fully verified, so complete this
step well before you plan to publish.

---

## 3. Opening the Project in Android Studio

### 3.1 Import the Project

1. Launch Android Studio.
2. From the Welcome screen, select **Open**.
3. Navigate to the project root directory:
   ```
   /home/user/inthebeginning/apps/kotlin
   ```
4. Select the `kotlin` folder (which contains the top-level `build.gradle.kts` and
   `settings.gradle.kts`) and click **OK**.
5. Android Studio will detect this as a Gradle project and begin importing.

### 3.2 Gradle Sync

On import, Android Studio triggers a Gradle sync automatically:

1. Watch the **Build** tool window at the bottom of the IDE. You will see messages
   such as "Gradle sync started" and progress indicators.
2. The sync downloads all dependencies declared in `build.gradle.kts`, including:
   - Jetpack Compose BOM 2024.02.00 and all Compose UI libraries
   - AndroidX Activity Compose 1.8.2
   - AndroidX Lifecycle libraries 2.7.0
   - AndroidX Core KTX 1.12.0
   - Kotlin Coroutines 1.7.3
3. If sync completes successfully, you will see "Gradle sync finished" with a green
   checkmark in the status bar.

### 3.3 Resolving Common Sync Issues

If the sync fails, try these fixes:

- **"SDK location not found"**: Go to **File > Project Structure > SDK Location** and
  set the Android SDK path (typically `~/Android/Sdk` on Linux/macOS or
  `C:\Users\<you>\AppData\Local\Android\Sdk` on Windows).
- **"Could not find com.android.application:8.3.0"**: Ensure the `google()` and
  `mavenCentral()` repositories are accessible. Check your internet connection and
  proxy settings under **File > Settings > Appearance & Behavior > System Settings >
  HTTP Proxy**.
- **JDK version mismatch**: The project requires JDK 17. Go to **File > Settings >
  Build, Execution, Deployment > Build Tools > Gradle** and set **Gradle JDK** to a
  JDK 17 installation.
- **Kotlin version conflict**: The project uses Kotlin 1.9.22. If prompted to update,
  you may do so, but test thoroughly afterward.

After resolving any issues, re-sync by clicking the **Sync Project with Gradle Files**
button (elephant icon with a blue arrow) in the toolbar, or by selecting **File >
Sync Project with Gradle Files**.

---

## 4. Configuring the Project

The project comes pre-configured, but here is a reference for every important value and
where to find it. These values live in `apps/kotlin/app/build.gradle.kts`.

### 4.1 Application ID

```kotlin
applicationId = "com.inthebeginning"
```

This is the unique identifier for the app on Google Play. It must be globally unique
across the entire Play Store. Once you upload the first version, you cannot change it.

If `com.inthebeginning` is already taken, change it to something unique such as
`com.yourcompany.inthebeginning`. Update it in the `defaultConfig` block of
`app/build.gradle.kts`.

Note: The debug build variant appends `.debug` to the application ID automatically
(configured via `applicationIdSuffix = ".debug"` in the `debug` build type), so debug
and release can coexist on the same device.

### 4.2 Version Code and Version Name

```kotlin
versionCode = 1
versionName = "1.0.0"
```

- **`versionCode`**: An integer that must increase with every upload to Google Play.
  Google uses this internally to determine update order. For your first release, `1` is
  correct. For subsequent releases, increment it (2, 3, 4, ...).
- **`versionName`**: A human-readable version string shown to users in the Play Store
  listing. The project uses semantic versioning (`MAJOR.MINOR.PATCH`). `"1.0.0"` is
  appropriate for the initial release.

### 4.3 SDK Versions

```kotlin
compileSdk = 34
minSdk = 26
targetSdk = 34
```

- **`compileSdk = 34`**: The API level the app is compiled against (Android 14). This
  determines which Android APIs are available at compile time.
- **`minSdk = 26`**: The lowest Android version the app supports (Android 8.0 Oreo).
  Devices running anything older than API 26 will not see the app on Google Play. API
  26 was chosen because it provides the baseline Kotlin and Compose compatibility.
- **`targetSdk = 34`**: Declares that the app has been tested against Android 14
  behaviors. Google Play requires new apps to target a recent API level (within one
  year of the latest major version).

### 4.4 Compose Configuration

```kotlin
buildFeatures {
    compose = true
}

composeOptions {
    kotlinCompilerExtensionVersion = "1.5.8"
}
```

This enables Jetpack Compose and pins the Compose compiler extension to version 1.5.8,
which is compatible with Kotlin 1.9.22. Do not change these independently -- the
Compose compiler version must match the Kotlin version.

### 4.5 ProGuard / R8 Configuration

The release build type enables code shrinking and resource shrinking:

```kotlin
release {
    isMinifyEnabled = true
    isShrinkResources = true
    proguardFiles(
        getDefaultProguardFile("proguard-android-optimize.txt"),
        "proguard-rules.pro"
    )
}
```

R8 (the default code shrinker) removes unused code and resources, reducing the APK/AAB
size. If you encounter runtime issues in release builds (typically
`ClassNotFoundException` or reflection failures), add keep rules to the
`proguard-rules.pro` file in the `app/` directory.

### 4.6 Namespace and Project Name

- **Namespace**: `com.inthebeginning` (set in `app/build.gradle.kts`, used for
  generated R and BuildConfig classes).
- **Project name**: `InTheBeginning` (set in `settings.gradle.kts` as
  `rootProject.name`).
- **App display name**: "In The Beginning" (set in `res/values/strings.xml` as
  `app_name`).

---

## 5. Signing Configuration

Every Android app must be digitally signed before it can be installed on a device.
Debug builds are signed automatically with a debug keystore. Release builds require
your own keystore.

### 5.1 Understanding Signing

- **Debug keystore**: Generated automatically by Android Studio at
  `~/.android/debug.keystore`. Used only for local development and testing. Apps signed
  with a debug key cannot be uploaded to Google Play.
- **Release keystore**: A keystore you create and control. It contains a private key
  used to sign your release builds. You must safeguard this keystore -- if you lose it,
  you can never update your app on Google Play (unless you enrolled in Play App
  Signing).

### 5.2 Create a Release Keystore via Android Studio

1. In Android Studio, go to **Build > Generate Signed Bundle / APK**.
2. In the dialog, select **Android App Bundle** and click **Next**.
3. Under **Key store path**, click **Create new...**.
4. In the **New Key Store** dialog, fill in:
   - **Key store path**: Choose a secure location outside the project directory, for
     example `~/keystores/inthebeginning-release.jks`. Do NOT place it inside the Git
     repository.
   - **Password**: Choose a strong password (16+ characters, mixed case, numbers,
     symbols). Record it in a password manager.
   - **Confirm password**: Re-enter the same password.
   - **Alias**: `inthebeginning-release` (or any descriptive name).
   - **Key password**: Can be the same as the keystore password, or a different one.
   - **Validity (years)**: `25` (Google recommends at least 25 years).
   - **Certificate**:
     - **First and Last Name**: Your name or organization name.
     - **Organizational Unit**: (optional) e.g., "Mobile Development".
     - **Organization**: Your company or team name.
     - **City or Locality**: Your city.
     - **State or Province**: Your state/province.
     - **Country Code (XX)**: Two-letter country code (e.g., `US`).
5. Click **OK** to create the keystore.
6. You are returned to the Generate Signed Bundle dialog with the new keystore filled
   in. You can proceed with generating a signed build now, or click **Cancel** to
   generate it later.

### 5.3 Storing the Keystore Securely

The release keystore is the single most critical artifact for your app's identity on
Google Play. Follow these practices:

- **Never commit the keystore to version control.** Add `*.jks` and `*.keystore` to
  your `.gitignore`.
- **Back up the keystore** to at least two secure locations (encrypted cloud storage,
  hardware security module, or a USB drive in a safe).
- **Store passwords** in a password manager (such as 1Password, Bitwarden, or a
  corporate secrets vault).
- **Document the keystore location, alias, and password references** in a private
  internal document accessible only to authorized team members.

### 5.4 Enroll in Play App Signing (Recommended)

Google Play App Signing provides an additional layer of protection:

1. When you upload your first AAB to Google Play, the Play Console will prompt you to
   enroll in Play App Signing.
2. Google manages the app signing key on their secure infrastructure. You sign your
   upload with an "upload key" (your keystore), and Google re-signs the final APK
   delivered to users.
3. If you ever lose your upload key, Google can reset it for you without affecting
   users.
4. Enrollment is strongly recommended and is the default for new apps.

---

## 6. Building in Android Studio

### 6.1 Debug vs. Release Builds

The project defines two build types in `app/build.gradle.kts`:

| Aspect              | Debug                              | Release                          |
|---------------------|------------------------------------|----------------------------------|
| Application ID      | `com.inthebeginning.debug`         | `com.inthebeginning`             |
| Code minification   | Disabled (`isMinifyEnabled = false`)| Enabled (`isMinifyEnabled = true`)|
| Resource shrinking  | Disabled                           | Enabled (`isShrinkResources = true`)|
| ProGuard/R8         | Not applied                        | Applied with `proguard-android-optimize.txt` |
| Signing             | Debug keystore (automatic)         | Release keystore (manual)        |
| Debuggable          | Yes                                | No                               |

### 6.2 Selecting the Build Variant

1. In Android Studio, open the **Build Variants** tool window (**View > Tool Windows >
   Build Variants**, or click the tab on the lower-left side panel).
2. In the table that appears, find the `:app` module row.
3. Click the **Active Build Variant** dropdown and select either `debug` or `release`.
4. Android Studio will re-sync to apply the variant selection.

### 6.3 Building the Project

1. Select **Build > Make Project** from the menu bar (or press **Ctrl+F9** on
   Windows/Linux, **Cmd+F9** on macOS).
2. Watch the **Build** tool window at the bottom. You will see:
   - Gradle tasks executing (compiling Kotlin, processing resources, running R8 for
     release, etc.).
   - Warnings and errors (if any) listed with clickable file references.
3. On success, the status bar shows **"Build completed successfully"**.
4. Build output locations:
   - **Debug APK**: `app/build/outputs/apk/debug/app-debug.apk`
   - **Release APK** (if signing is configured in Gradle):
     `app/build/outputs/apk/release/app-release.apk`

### 6.4 Viewing Build Output and Errors

- The **Build** tool window shows a hierarchical log of all build steps. Expand any
  step to see details.
- Errors appear in red with file paths and line numbers. Click an error to jump to the
  source file.
- For Compose-specific errors (e.g., `@Composable invocations can only happen...`),
  the error message will reference the composable function. These are typically caused
  by calling composable functions from non-composable contexts.

---

## 7. Running in the Emulator

### 7.1 Setting Up an Android Virtual Device (AVD)

1. In Android Studio, open the **Device Manager** by clicking the phone icon in the
   right-side toolbar, or via **Tools > Device Manager**.
2. Click **Create Virtual Device**.
3. In the **Select Hardware** screen:
   - Choose a device definition. Recommended: **Pixel 7** (a modern device with a
     common screen size).
   - Click **Next**.
4. In the **System Image** screen:
   - Select the **Recommended** tab.
   - Choose an image with **API 34** (Android 14), specifically the **"UpsideDownCake"
     x86_64** image for best emulator performance.
   - If the image is not yet downloaded, click the **Download** link next to it and
     wait for it to complete.
   - Click **Next**.
5. In the **Verify Configuration** screen:
   - **AVD Name**: Accept the default (e.g., "Pixel 7 API 34") or rename it.
   - **Startup orientation**: Portrait.
   - Under **Show Advanced Settings**, you can adjust:
     - **RAM**: 2048 MB or higher recommended.
     - **Internal Storage**: 2048 MB minimum.
     - **Enable hardware keyboard**: Check this for convenience.
   - Click **Finish**.

### 7.2 Choosing the API Level

Since the project sets `minSdk = 26` and `targetSdk = 34`:

- Your emulator should run **API 34** to test against the target SDK and ensure
  compatibility with the latest Android behaviors.
- Optionally create a second AVD with **API 26** (Android 8.0) to verify the app works
  on the minimum supported version.
- The OpenGL ES renderer in the app uses Android framework classes (`android.opengl.*`)
  which are available on all API levels from 26 onward. The emulator supports OpenGL
  ES through host GPU acceleration.

### 7.3 Running the App

1. In the toolbar at the top of Android Studio, select your AVD from the device
   dropdown (left of the green Run button). It will appear as something like
   "Pixel 7 API 34".
2. Ensure the build variant is set to **debug** (see Section 6.2).
3. Click the **Run** button (green triangle) or press **Shift+F10** (Windows/Linux) /
   **Ctrl+R** (macOS).
4. Android Studio will:
   - Build the debug APK.
   - Launch the emulator (if not already running). First boot takes 1-2 minutes.
   - Install the APK onto the emulator.
   - Launch the app.
5. The "In The Beginning" app opens showing the **Cosmic Simulation** screen with the
   Planck epoch. Press the **Play** button to start the simulation.

### 7.4 Using the Emulator Toolbar

The emulator window has a vertical toolbar on the right side:

- **Power**: Simulate power button press.
- **Volume Up/Down**: Adjust volume.
- **Rotate Left/Right**: Test landscape orientation. The app handles orientation
  changes via `configChanges` in the manifest (`orientation|screenSize|screenLayout|
  smallestScreenSize|density`), meaning the Activity is not recreated on rotation.
- **Screenshot**: Capture a screenshot (useful for Play Store listing screenshots).
- **Extended Controls (...)**: Opens a panel with:
  - **Location**: Set GPS coordinates.
  - **Battery**: Simulate battery levels.
  - **Phone**: Simulate incoming calls/SMS.
  - **Virtual sensors**: Simulate accelerometer, gyroscope, etc.

---

## 8. Running on a Physical Device

### 8.1 Enabling Developer Options

1. On your Android device, open **Settings**.
2. Scroll down and tap **About phone** (or **About device**).
3. Find **Build number** and tap it **seven times** rapidly.
4. You will see a toast message: "You are now a developer!"
5. Go back to **Settings**. A new **Developer options** menu item now appears (often
   under **System** or directly in the main settings list).

### 8.2 USB Debugging

1. Open **Settings > Developer options**.
2. Toggle on **USB debugging**.
3. Connect your device to your computer with a USB cable.
4. A dialog appears on the device: "Allow USB debugging?" Check **Always allow from
   this computer** and tap **Allow**.
5. In Android Studio, your device will appear in the device dropdown in the toolbar,
   showing the device model and serial number.
6. Select your device and click **Run** to install and launch the debug build.

### 8.3 Wireless Debugging (Android 11+)

If your device runs Android 11 (API 30) or higher and is on the same Wi-Fi network
as your computer:

1. Open **Settings > Developer options**.
2. Toggle on **Wireless debugging**.
3. Tap **Wireless debugging** to enter the submenu.
4. Tap **Pair device with pairing code**. A dialog shows an IP address, port, and
   pairing code.
5. In Android Studio, open the **Device Manager**, click the **Physical** tab, and
   click **Pair using Wi-Fi**. Enter the pairing code.
6. Once paired, the device appears in the device dropdown and can be used wirelessly
   without a USB cable.

### 8.4 Running on the Device

1. Select your physical device from the device dropdown.
2. Click **Run** (or press **Shift+F10** / **Ctrl+R**).
3. Android Studio builds, installs, and launches the app on your device.
4. The simulation's Compose UI and Canvas-based visualizations will render natively.
   The OpenGL ES renderer uses the device's GPU directly, so performance will typically
   be better than the emulator.
5. Use **Logcat** (the tab at the bottom of Android Studio) to view real-time logs.
   Filter by `com.inthebeginning` to see only your app's output.

---

## 9. Building a Release AAB

Google Play requires **Android App Bundles (AAB)** for all new apps. An AAB allows
Google Play to generate optimized APKs for each device configuration, reducing download
size for users.

### 9.1 Generate a Signed Bundle

1. In Android Studio, go to **Build > Generate Signed Bundle / APK**.
2. Select **Android App Bundle** and click **Next**.
3. Fill in the signing information:
   - **Module**: `app` (this should be pre-selected).
   - **Key store path**: Browse to your release keystore (e.g.,
     `~/keystores/inthebeginning-release.jks`).
   - **Key store password**: Enter the keystore password.
   - **Key alias**: `inthebeginning-release` (or the alias you chose).
   - **Key password**: Enter the key password.
4. Optionally check **Remember passwords** if you are on a secure, personal machine.
5. Click **Next**.
6. On the next screen:
   - **Destination Folder**: Accept the default or choose a location.
   - **Build Variants**: Select **release**.
7. Click **Create**.
8. Android Studio will:
   - Compile the project.
   - Run R8 code shrinking and resource shrinking.
   - Package the app into an AAB file.
   - Sign it with your release key.
9. On success, a notification appears: **"Generate Signed Bundle: Locate"**. Click
   **locate** to open the output directory.
10. The AAB file is at:
    ```
    app/build/outputs/bundle/release/app-release.aab
    ```

### 9.2 Verify the AAB

Before uploading, you can verify the AAB locally:

1. Download **bundletool** from https://github.com/google/bundletool/releases.
2. Generate APKs from the bundle to test on a device:
   ```
   java -jar bundletool.jar build-apks \
     --bundle=app/build/outputs/bundle/release/app-release.aab \
     --output=inthebeginning.apks \
     --ks=~/keystores/inthebeginning-release.jks \
     --ks-key-alias=inthebeginning-release
   ```
3. Install the APKs on a connected device:
   ```
   java -jar bundletool.jar install-apks --apks=inthebeginning.apks
   ```

This confirms that the AAB produces a working app before you upload it to Google Play.

---

## 10. Google Play Console Setup

### 10.1 Create the App

1. Log in to the **Google Play Console** at https://play.google.com/console.
2. Click **Create app** on the home page.
3. Fill in the app details:
   - **App name**: `In The Beginning`
   - **Default language**: English (United States) -- or your primary language.
   - **App or game**: Select **Game** (this is a simulation, which fits the game
     category) or **App** (if you prefer it listed as an educational/simulation app).
   - **Free or paid**: Select **Free**.
4. Check the declarations:
   - Confirm the app meets the Developer Program Policies.
   - Confirm the app is subject to US export laws.
5. Click **Create app**.

### 10.2 Store Listing

Navigate to **Grow > Store presence > Main store listing** in the left sidebar.

#### App Details

- **App name**: `In The Beginning` (up to 30 characters).
- **Short description** (up to 80 characters):
  ```
  Simulate the cosmos from the Big Bang to the emergence of life.
  ```
- **Full description** (up to 4000 characters):
  ```
  In The Beginning is an interactive cosmic evolution simulator that
  takes you on a journey from the very first moments of the universe
  to the emergence of complex life.

  Watch the Planck epoch give way to cosmic inflation. See quarks
  confine into protons and neutrons during the Hadron epoch.
  Witness nucleosynthesis forge hydrogen and helium. Experience
  recombination as the universe becomes transparent and the cosmic
  microwave background is released.

  Explore star formation, the birth of our solar system, the
  formation of Earth, and the origin of self-replicating molecules.
  Follow the DNA era as life evolves, complete with epigenetic
  regulation and environmental pressures.

  Features:
  - Real-time simulation spanning 13 cosmic epochs
  - Beautiful Canvas and OpenGL ES visualizations
  - Material You (Material 3) dark-themed interface
  - Interactive controls: play, pause, reset, adjustable speed
  - Pinch-to-zoom and pan on the cosmic visualization
  - Live event log tracking key cosmic milestones
  - Real-time stats: temperature, particle counts, elements, life
  - Settings screen with visualization style selection
  - Smooth animations powered by Jetpack Compose

  Built with Kotlin, Jetpack Compose, and Kotlin Coroutines.
  Requires Android 8.0 (Oreo) or later.
  ```

#### Graphics Assets

You need the following screenshots and images. Use the emulator screenshot feature
(Section 7.4) to capture them:

- **Phone screenshots**: At least 2, up to 8 screenshots. Recommended resolution:
  1080 x 1920 pixels (portrait) or 1920 x 1080 (landscape).
  - Screenshot 1: The simulation during the Planck/Inflation epoch (Big Bang
    visualization with expanding rings).
  - Screenshot 2: The Star Formation epoch showing the nebula and star field.
  - Screenshot 3: The Biosphere epoch showing Earth, DNA helix, and cells.
  - Screenshot 4: The Settings screen.
  - Screenshot 5: The Event Log showing cosmic milestone entries.
- **7-inch tablet screenshots** (optional): At least 2, if you want to show tablet
  layout.
- **10-inch tablet screenshots** (optional): At least 2.
- **Feature graphic**: 1024 x 500 pixels. A banner image shown at the top of the
  Play Store listing. Create a graphic with the app name, a cosmic background, and
  a simulation preview.
- **App icon**: 512 x 512 pixels. The high-resolution icon matching your
  `@mipmap/ic_launcher` resource.

Upload all graphics under the **Main store listing** page and click **Save**.

### 10.3 Content Rating Questionnaire

1. Navigate to **Policy > App content > Content rating**.
2. Click **Start questionnaire**.
3. Enter your **email address** for the rating authority to contact you.
4. Select a **category**. For this app, choose **Utility, Productivity, Communication,
   or Other** (or **Game** > **Simulation** if you registered it as a game).
5. Answer the questions honestly. For "In The Beginning":
   - Violence: **No** (the simulation depicts cosmic events, not interpersonal
     violence).
   - Sexual content: **No**.
   - Language: **No** (no user-generated content, no profanity).
   - Controlled substances: **No**.
   - User interaction: **No** (the app is single-player, offline only).
6. Click **Save** and then **Next** to calculate ratings.
7. Review the generated ratings for each region (ESRB, PEGI, etc.) and click **Submit**.

### 10.4 Target Audience and Content

1. Navigate to **Policy > App content > Target audience and content**.
2. Select the target age group. Since this is a cosmic simulation with educational
   value but no specific child-safety requirements, select **13 and over** or
   **16-17 and 18 and over**.
3. Confirm the app is not primarily child-directed.
4. Click **Save**.

### 10.5 Data Safety Form

1. Navigate to **Policy > App content > Data safety**.
2. This app does not require any special permissions (the `AndroidManifest.xml`
   declares no permissions), does not access the internet, and does not collect any
   user data. Fill in:
   - **Does your app collect or share any of the required user data types?** Select
     **No**.
   - **Does your app collect data?** Select **No**.
   - **Does your app share data with third parties?** Select **No**.
   - **Security practices**: You can state that data is not collected, so encryption
     of data in transit is not applicable.
3. Click **Save** and then **Submit**.

### 10.6 Privacy Policy

Google requires a privacy policy URL, even for apps that do not collect data.

1. Create a simple privacy policy page hosted on a website you control. It should
   state that the app does not collect, store, or transmit any personal data. Example:
   ```
   Privacy Policy for In The Beginning

   Last updated: [date]

   In The Beginning is an offline cosmic simulation app. It does not collect,
   store, or transmit any personal data, usage data, or analytics. The app
   does not require an internet connection and does not communicate with any
   external servers.

   Contact: [your email]
   ```
2. Host this page and note the URL.
3. In the Play Console, navigate to **Policy > App content > Privacy policy**.
4. Enter the URL of your privacy policy.
5. Click **Save**.

---

## 11. Internal Testing

Internal testing allows you to distribute a build to a small group of trusted testers
before wider release.

### 11.1 Create an Internal Testing Track

1. In the Google Play Console, navigate to **Release > Testing > Internal testing**.
2. Click **Create new release**.
3. If prompted about Play App Signing, click **Continue** to enroll (recommended, see
   Section 5.4).
4. Under **App bundles**, click **Upload** and select your signed AAB file:
   ```
   app/build/outputs/bundle/release/app-release.aab
   ```
5. Wait for the upload and processing to complete. Google validates the bundle format,
   signing, and basic manifest requirements.
6. Enter **Release notes** for this version:
   ```
   Initial internal testing release of In The Beginning (1.0.0).
   - Full cosmic simulation from Planck epoch to Present.
   - Canvas-based visualization with Compose UI.
   - Adjustable speed, play/pause/reset controls.
   ```
7. Click **Save** and then **Review release**.
8. Review the summary and click **Start rollout to Internal testing**.

### 11.2 Add Testers

1. Navigate to **Release > Testing > Internal testing**.
2. Click the **Testers** tab.
3. Click **Create email list** or select an existing list.
4. Add testers by entering their Google Account email addresses (up to 100 testers
   for internal testing).
5. Click **Save changes**.

### 11.3 Share the Opt-In Link

1. On the **Testers** tab, scroll down to find the **How testers join your test**
   section.
2. Copy the **opt-in URL**. It will look like:
   ```
   https://play.google.com/apps/internaltest/[long-token]
   ```
3. Send this link to your testers via email, Slack, or any communication channel.
4. Testers must:
   - Open the link on their Android device or in a browser while signed into their
     Google Account.
   - Accept the invitation to become a tester.
   - Install the app from the Play Store link provided after opting in.
5. Internal test releases are typically available to testers within a few minutes of
   upload.

---

## 12. Closed and Open Testing

After internal testing confirms the app works correctly, expand testing to larger
groups.

### 12.1 Closed Testing (Alpha)

Closed testing lets you invite specific groups of testers, such as QA teams, beta
community members, or stakeholder groups.

1. Navigate to **Release > Testing > Closed testing**.
2. Click **Create track** if no track exists, or select an existing track (e.g.,
   "Alpha").
3. Click **Create new release**.
4. Upload the AAB (you can reuse the same AAB from internal testing, or upload an
   updated one with a higher `versionCode`).
5. Enter release notes.
6. Click **Save**, then **Review release**, then **Start rollout to Closed testing**.

#### Managing Testers for Closed Testing

1. Go to the **Testers** tab of the closed testing track.
2. You can add testers by:
   - **Email lists**: Add individual email addresses (up to 2,000 per list).
   - **Google Groups**: Enter a Google Group email address. All members of the group
     become testers.
3. Share the opt-in link (similar to internal testing).

### 12.2 Open Testing (Beta)

Open testing makes the app available to anyone who finds the opt-in link. This is
useful for gathering broad feedback before a production launch.

1. Navigate to **Release > Testing > Open testing**.
2. Click **Create new release**.
3. Upload the AAB.
4. Enter release notes.
5. Click **Save**, then **Review release**, then **Start rollout to Open testing**.
6. Open testing does not require manually adding testers. Anyone with the link can
   join. The app may also appear in Play Store search results with a "Beta" label.

### 12.3 Gathering Feedback and Crash Reports

During testing phases:

- **Play Console feedback**: Navigate to **Quality > Android vitals** and
  **Quality > Ratings and reviews** to see tester feedback.
- **Pre-launch reports**: Google runs automated tests on the uploaded AAB using a
  variety of real devices. Navigate to **Release > Pre-launch report** to see:
  - Screenshots of the app running on different devices.
  - Crash logs and ANR reports from automated exploration.
  - Accessibility and performance suggestions.
- **Crash reports**: Navigate to **Quality > Android vitals > Crashes and ANRs**. This
  shows stack traces of any crashes testers encounter. Since the release build has R8
  minification enabled (`isMinifyEnabled = true`), stack traces will be obfuscated.
  Upload a mapping file to de-obfuscate:
  1. Find the mapping file at `app/build/outputs/mapping/release/mapping.txt` after
     building the release AAB.
  2. In the Play Console, navigate to the specific release on the testing track.
  3. Click on the release, then find the **Deobfuscation files** section.
  4. Upload `mapping.txt`.

---

## 13. Production Release

When testing confirms the app is stable and ready for public distribution, promote it
to production.

### 13.1 Promoting from Testing to Production

Option A -- **Promote an existing release**:

1. Navigate to **Release > Testing > Closed testing** (or whichever track has your
   latest tested release).
2. Select the release you want to promote.
3. Click **Promote release** and select **Production**.
4. Review the release details. Update the release notes for the production audience:
   ```
   In The Beginning 1.0.0 -- initial release.

   Experience the complete history of the universe in an interactive
   simulation. From the Big Bang through star formation, planet
   creation, and the emergence of life.
   ```
5. Click **Save**, then **Review release**.

Option B -- **Create a new production release**:

1. Navigate to **Release > Production**.
2. Click **Create new release**.
3. Upload the AAB and enter release notes.
4. Click **Save**, then **Review release**.

### 13.2 Pricing and Distribution

1. The app pricing was set to **Free** when the app was created (Section 10.1). Free
   apps cannot be changed to paid later, but you can add in-app purchases in future
   versions if needed.
2. Navigate to **Release > Production > Countries/regions** (or configure during the
   release review step).
3. Click **Add countries/regions**.
4. Select the countries where you want the app to be available. For maximum reach,
   click **Select all** to distribute to all available countries.
5. Click **Add** to confirm.

### 13.3 Staged Rollout

Google allows you to roll out a production release gradually to reduce risk:

1. On the **Review release** page, you will see a **Rollout percentage** option.
2. For a first release, you can choose:
   - **100%**: The app becomes available to all users immediately.
   - **A lower percentage** (e.g., 20%): Only a fraction of users in each country will
     see the update. You can increase the percentage over time.
3. Recommended strategy for version 1.0.0:
   - Start at **20%** for the first 24-48 hours. Monitor crash rates in Android
     Vitals.
   - If crash-free rate is above 99%, increase to **50%**.
   - After another 24 hours with good metrics, increase to **100%**.
4. To increase the rollout:
   - Go to **Release > Production**.
   - Click the current release.
   - Click **Increase rollout** and set the new percentage.

### 13.4 Submit for Review

1. After setting all options, click **Start rollout to Production**.
2. Google reviews the app. For new apps, this review typically takes a few hours to
   several days.
3. During review, the app status shows **"In review"** in the Play Console dashboard.
4. If the review passes, the status changes to **"Available on Google Play"** and the
   app appears in Play Store search results.
5. If the review is rejected, Google sends an email explaining the policy violation.
   Address the issue, update the app or listing, and resubmit.

---

## 14. Post-Launch

### 14.1 Monitoring Android Vitals

Android Vitals is your primary dashboard for app health. Navigate to **Quality >
Android vitals** in the Play Console.

#### Key Metrics

- **Crash rate**: Percentage of daily sessions with at least one crash. Google's "bad
  behavior threshold" is 1.09%. Aim for well below this.
- **ANR rate**: Application Not Responding events (the app's main thread is blocked
  for 5+ seconds). Threshold is 0.47%. The "In The Beginning" app runs the simulation
  loop on `Dispatchers.Default` (background thread) and updates UI via Compose state
  flow, which should keep the main thread responsive. Monitor this metric to confirm.
- **Excessive wakeups**: Not applicable for this app (no background services or alarms).
- **Stuck partial wake locks**: Not applicable (no wake locks used).

#### Crash Reports

1. Go to **Quality > Android vitals > Crashes and ANRs**.
2. View individual crash clusters grouped by stack trace.
3. Ensure the R8 mapping file is uploaded (Section 12.3) so stack traces show original
   class and method names instead of obfuscated identifiers.
4. Common things to watch for in this app:
   - **OpenGL ES errors**: If the `SimulationRenderer` encounters device-specific GPU
     issues.
   - **Out of memory**: The simulation tracks particles, elements, and biological
     entities. Monitor memory consumption on low-RAM devices (minSdk 26 includes
     devices with 1-2 GB RAM).
   - **Compose rendering issues**: Rare but possible on older API levels close to
     minSdk 26.

### 14.2 Responding to Reviews

1. Navigate to **Quality > Ratings and reviews**.
2. Read user reviews and respond to them directly from the Play Console.
3. Best practices:
   - Respond to negative reviews promptly and professionally.
   - Thank users for positive feedback.
   - If a user reports a bug, ask for device model and Android version.
   - Update your response after fixing a reported issue to let the user know.

### 14.3 Updating the App

When you are ready to release a new version:

1. **Update the version** in `apps/kotlin/app/build.gradle.kts`:
   ```kotlin
   defaultConfig {
       applicationId = "com.inthebeginning"
       minSdk = 26
       targetSdk = 34
       versionCode = 2              // Increment this
       versionName = "1.1.0"        // Update this
       // ...
   }
   ```
   - `versionCode` must be strictly greater than the previous upload. Google Play
     rejects uploads with equal or lower version codes.
   - `versionName` follows semantic versioning:
     - **1.0.1**: Bug fix release (patch).
     - **1.1.0**: New feature release (minor).
     - **2.0.0**: Major overhaul or breaking changes (major).

2. **Build a new signed AAB** following Section 9.

3. **Upload the new AAB** to the appropriate testing track first (internal, closed, or
   open) to validate the update with testers.

4. **Promote to production** after testing, optionally using a staged rollout.

5. **Upload the new mapping file** (`mapping.txt`) for the updated release so crash
   reports remain readable.

### 14.4 Version Management Strategy

For the "In The Beginning" app, consider this versioning plan:

| Version   | versionCode | Description                                      |
|-----------|-------------|--------------------------------------------------|
| 1.0.0     | 1           | Initial release, all 13 epochs, Canvas visualization |
| 1.1.0     | 2           | OpenGL ES rendering mode fully integrated        |
| 1.2.0     | 3           | Additional visualization styles, performance tuning |
| 1.3.0     | 4           | Tablet-optimized layout, landscape mode           |
| 2.0.0     | 5           | Major UI overhaul or new simulation systems       |

### 14.5 Ongoing Maintenance Checklist

- **Target SDK**: Google requires apps to target an API level within one year of the
  latest Android release. When Android 15 is released, update `targetSdk` to 35 and
  test for behavioral changes.
- **Dependency updates**: Periodically update Jetpack Compose BOM, AndroidX libraries,
  and Kotlin version. Test thoroughly after updating.
- **Gradle plugin updates**: Update the Android Gradle Plugin and Gradle wrapper as
  new versions are released. Check compatibility with your Kotlin and Compose versions.
- **Store listing refresh**: Update screenshots and descriptions when significant
  visual changes are made to the app.
- **Pre-launch report**: Review the automated pre-launch report for every new release
  upload. It tests on real devices and may catch device-specific issues.

---

## Quick Reference: Key Project Values

| Property                  | Value                          | File                           |
|---------------------------|--------------------------------|--------------------------------|
| Application ID            | `com.inthebeginning`           | `app/build.gradle.kts`        |
| Namespace                 | `com.inthebeginning`           | `app/build.gradle.kts`        |
| App display name          | In The Beginning               | `res/values/strings.xml`      |
| Project name              | InTheBeginning                 | `settings.gradle.kts`         |
| Version code              | 1                              | `app/build.gradle.kts`        |
| Version name              | 1.0.0                          | `app/build.gradle.kts`        |
| compileSdk                | 34                             | `app/build.gradle.kts`        |
| minSdk                    | 26 (Android 8.0 Oreo)         | `app/build.gradle.kts`        |
| targetSdk                 | 34 (Android 14)                | `app/build.gradle.kts`        |
| Kotlin version            | 1.9.22                         | `build.gradle.kts`            |
| Android Gradle Plugin     | 8.3.0                          | `build.gradle.kts`            |
| Compose BOM               | 2024.02.00                     | `app/build.gradle.kts`        |
| Compose compiler          | 1.5.8                          | `app/build.gradle.kts`        |
| JVM target                | 17                             | `app/build.gradle.kts`        |
| Debug application ID      | `com.inthebeginning.debug`     | `app/build.gradle.kts`        |
| R8 minification (release) | Enabled                        | `app/build.gradle.kts`        |
| Resource shrinking        | Enabled                        | `app/build.gradle.kts`        |
| Permissions               | None                           | `AndroidManifest.xml`          |
| Main activity             | `.MainActivity`                | `AndroidManifest.xml`          |
| Theme                     | `Theme.InTheBeginning`         | `res/values/themes.xml`       |
