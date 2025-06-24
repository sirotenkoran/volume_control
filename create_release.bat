@echo off
setlocal enabledelayedexpansion

echo 🚀 AppVolumeControl Release Creator
echo =================================

REM Check if version argument is provided
if "%1"=="" (
    echo ❌ Error: Please provide a version number
    echo Usage: create_release.bat v1.2.3 [release_notes]
    echo Example: create_release.bat v1.0.0 "Bug fixes and performance improvements"
    echo Example: create_release.bat v1.0.0
    pause
    exit /b 1
)

set VERSION=%1

REM Handle release notes - collect all remaining arguments
set RELEASE_NOTES=
shift
:collect_notes
if not "%1"=="" (
    if defined RELEASE_NOTES (
        set "RELEASE_NOTES=!RELEASE_NOTES! %1"
    ) else (
        set "RELEASE_NOTES=%1"
    )
    shift
    goto collect_notes
)

echo.
echo 📋 Creating release for version: %VERSION%
if defined RELEASE_NOTES (
    echo 📝 Release notes: !RELEASE_NOTES!
)
echo.

REM Check if we're in a git repository
git status >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Not in a git repository
    pause
    exit /b 1
)

REM Check if there are uncommitted changes
git diff --quiet
if errorlevel 1 (
    echo ⚠️  Warning: You have uncommitted changes
    echo Please commit or stash them before creating a release
    pause
    exit /b 1
)

REM Check if tag already exists
git tag -l %VERSION% | findstr /c:"%VERSION%" >nul
if not errorlevel 1 (
    echo ❌ Error: Tag %VERSION% already exists
    pause
    exit /b 1
)

echo ✅ Pre-checks passed
echo.

REM Build the executable
echo 🔨 Building executable...
call build.bat
if errorlevel 1 (
    echo ❌ Build failed
    pause
    exit /b 1
)

echo ✅ Build completed
echo.

REM Create and push the tag
echo 🏷️  Creating tag: %VERSION%
if defined RELEASE_NOTES (
    echo 📝 Adding release notes: !RELEASE_NOTES!
    git tag -a %VERSION% -m "!RELEASE_NOTES!"
) else (
    git tag %VERSION%
)
if errorlevel 1 (
    echo ❌ Failed to create tag
    pause
    exit /b 1
)

echo 📤 Pushing tag to GitHub...
git push origin %VERSION%
if errorlevel 1 (
    echo ❌ Failed to push tag
    echo You may need to configure your git remote
    pause
    exit /b 1
)

echo.
echo 🎉 Release %VERSION% created successfully!
if defined RELEASE_NOTES (
    echo 📝 Release notes included: !RELEASE_NOTES!
)
echo.
echo 📋 Next steps:
echo 1. Go to GitHub Actions to monitor the build: https://github.com/sirotenkoran/volume_control/actions
echo 2. Check the release: https://github.com/sirotenkoran/volume_control/releases
echo 3. Verify the exe file is included in the release
echo.
echo 💡 The GitHub Actions workflow will automatically:
echo    - Build the executable
echo    - Create a GitHub Release
echo    - Upload AppVolumeControl.exe
echo    - Generate release notes
echo.
pause 