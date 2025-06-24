# AppVolumeControl Release Creator (PowerShell Version)
param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$ReleaseNotes
)

Write-Host "🚀 AppVolumeControl Release Creator" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Creating release for version: $Version" -ForegroundColor Yellow
if ($ReleaseNotes) {
    Write-Host "📝 Release notes: $ReleaseNotes" -ForegroundColor Yellow
}
Write-Host ""

# Check if we're in a git repository
try {
    git status | Out-Null
} catch {
    Write-Host "❌ Error: Not in a git repository" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

# Check if there are uncommitted changes
$uncommitted = git diff --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: You have uncommitted changes" -ForegroundColor Yellow
    Write-Host "Please commit or stash them before creating a release" -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
    exit 1
}

# Check if tag already exists
$existingTag = git tag -l $Version
if ($existingTag) {
    Write-Host "❌ Error: Tag $Version already exists" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "✅ Pre-checks passed" -ForegroundColor Green
Write-Host ""

# Build the executable
Write-Host "🔨 Building executable..." -ForegroundColor Yellow
& .\build.bat
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "✅ Build completed" -ForegroundColor Green
Write-Host ""

# Create and push the tag
Write-Host "🏷️  Creating tag: $Version" -ForegroundColor Yellow
if ($ReleaseNotes) {
    Write-Host "📝 Adding release notes: $ReleaseNotes" -ForegroundColor Yellow
    git tag -a $Version -m $ReleaseNotes
} else {
    git tag $Version
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create tag" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "📤 Pushing tag to GitHub..." -ForegroundColor Yellow
git push origin $Version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to push tag" -ForegroundColor Red
    Write-Host "You may need to configure your git remote" -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host ""
Write-Host "🎉 Release $Version created successfully!" -ForegroundColor Green
if ($ReleaseNotes) {
    Write-Host "📝 Release notes included: $ReleaseNotes" -ForegroundColor Green
}
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Go to GitHub Actions to monitor the build: https://github.com/sirotenkoran/volume_control/actions"
Write-Host "2. Check the release: https://github.com/sirotenkoran/volume_control/releases"
Write-Host "3. Verify the exe file is included in the release"
Write-Host ""
Write-Host "💡 The GitHub Actions workflow will automatically:" -ForegroundColor Cyan
Write-Host "   - Build the executable"
Write-Host "   - Create a GitHub Release"
Write-Host "   - Upload AppVolumeControl.exe"
Write-Host "   - Generate release notes"
Write-Host ""

Read-Host "Press Enter to continue" 