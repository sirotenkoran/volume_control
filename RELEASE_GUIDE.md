# 🚀 Release Guide

This guide explains how to create releases and manage the automated build process.

## 📋 Prerequisites

- GitHub repository with Actions enabled
- Write access to the repository
- Git configured locally

## 🔄 Automated Build Process

### Build Test (Every Push)
- **Trigger**: Every push to `main` or `master` branch
- **Action**: Builds the exe file and uploads as artifact
- **Purpose**: Verify that the code builds successfully
- **Location**: GitHub Actions → Artifacts → `AppVolumeControl-Test`

### Release Build (Tag-based)
- **Trigger**: Push a tag starting with `v` (e.g., `v1.2.3`)
- **Action**: Builds the exe and creates a GitHub Release
- **Purpose**: Create official releases for users
- **Location**: GitHub → Releases

## 🏷️ Creating a Release

### Option 1: Using the Automated Script (Recommended)

The easiest way to create a release is using the included `create_release.bat` script:

```bash
# Create a release with version v1.2.3
create_release.bat v1.2.3

# Create a release with version and release notes
create_release.bat v1.2.3 "Bug fixes and performance improvements"
```

This script will:
- ✅ Check if you're in a git repository
- ✅ Verify there are no uncommitted changes
- ✅ Check if the tag already exists
- ✅ Build the executable locally
- ✅ Create the git tag (with optional release notes)
- ✅ Push the tag to GitHub
- ✅ Provide next steps and monitoring links

### Option 2: Manual Process

If you prefer to do it manually:

#### Step 1: Prepare Your Changes
```bash
# Make your changes and test locally
python main.py

# Commit your changes
git add .
git commit -m "Add new feature: profile management"
git push origin main
```

#### Step 2: Create a Release Tag
```bash
# Create a new tag (use semantic versioning)
git tag v1.2.3

# Or create an annotated tag with release notes
git tag -a v1.2.3 -m "Bug fixes and performance improvements"

# Push the tag to trigger the release build
git push origin v1.2.3
```

#### Step 3: Monitor the Build
1. Go to GitHub → Actions
2. Find the "Build and Release" workflow
3. Monitor the build progress
4. Check that the release was created successfully

## 📝 Adding Release Notes

### Method 1: Using the Script (Recommended)
```bash
create_release.bat v1.2.3 "Bug fixes and performance improvements"
```

### Method 2: Manual Annotated Tag
```bash
git tag -a v1.2.3 -m "Bug fixes and performance improvements"
git push origin v1.2.3
```

### Method 3: Edit After Creation
1. Create the release using any method above
2. Go to GitHub → Releases
3. Click "Edit" on the created release
4. Add detailed release notes in the description field
5. Save the changes

## 📦 Release Assets

Each release will automatically include:
- `AppVolumeControl.exe` - The main executable
- Release notes (auto-generated from commits or from tag message)
- Source code (zip/tar.gz)

## 🔧 Manual Release (if needed)

If you need to create a release manually:

1. Go to GitHub → Releases → "Draft a new release"
2. Choose a tag or create a new one
3. Write release notes
4. Upload the `AppVolumeControl.exe` from your local `dist/` folder
5. Publish the release

## 🐛 Troubleshooting

### Build Fails
- Check the Actions logs for error details
- Verify all dependencies are in `requirements.txt`
- Ensure `icon.ico` exists in the root directory
- Test the build locally with `build.bat`

### Release Not Created
- Verify the tag format starts with `v`
- Check that the tag was pushed to GitHub
- Ensure the workflow has proper permissions
- Check the Actions logs for errors

### Exe Not Included
- Verify the build step completed successfully
- Check that the file path in the workflow is correct
- Ensure the exe file was created in the `dist/` folder

## 📝 Best Practices

### Version Numbering
Use semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Notes
- Write clear, user-friendly release notes
- Include new features and bug fixes
- Mention any breaking changes
- Add usage examples if needed

### Testing
- Always test locally before creating a release
- Verify the exe works on a clean system
- Test with different configurations
- Check that the icon displays correctly

## 🔗 Useful Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)
- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)

## 📊 Release Checklist

Before creating a release, ensure:

- [ ] All changes are committed and pushed
- [ ] Local build works: `build.bat`
- [ ] Application runs correctly: `python main.py`
- [ ] Tests pass (if any)
- [ ] Documentation is updated
- [ ] Version number is appropriate
- [ ] Release notes are prepared

## 🎯 Quick Commands

```bash
# Build locally
build.bat

# Test locally
python main.py

# Create and push a release
git tag v1.2.3
git push origin v1.2.3

# Check build status
# Go to: https://github.com/sirotenkoran/volume_control/actions
```

### Monitor Builds
- GitHub Actions: `https://github.com/sirotenkoran/volume_control/actions`
- Releases: `https://github.com/sirotenkoran/volume_control/releases` 