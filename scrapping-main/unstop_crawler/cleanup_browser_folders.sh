#!/bin/bash

# List of browser-created folders to remove
folders=(
    "AmountExtractionHeuristicRegexes"
    "AutofillStates"
    "CertificateRevocation"
    "component_crx_cache"
    "CookieReadinessList"
    "Crowd Deny"
    "Default"
    "extensions_crx_cache"
    "FileTypePolicies"
    "FirstPartySetsPreloaded"
    "GraphiteDawnCache"
    "GrShaderCache"
    "hyphen-data"
    "MEIPreload"
    "NativeMessagingHosts"
    "OnDeviceHeadSuggestModel"
    "OpenCookieDatabase"
    "OptimizationHints"
    "OriginTrials"
    "PKIMetadata"
    "PrivacySandboxAttestationsPreloaded"
    "ProbabilisticRevealTokenRegistry"
    "Profile 1"
    "Safe Browsing"
    "SafetyTips"
    "segmentation_platform"
    "ShaderCache"
    "SSLErrorAssistant"
    "Subresource Filter"
    "TpcdMetadata"
    "TrustTokenKeyCommitments"
    "WasmTtsEngine"
    "WidevineCdm"
    "ZxcvbnData"
)

# Browser-created files
files=(
    "DevToolsActivePort"
    "First Run"
    "Last Version"
    "Local State"
    "Variations"
    "first_party_sets.db"
    "first_party_sets.db-journal"
)

echo "🧹 Cleaning up browser-created folders and files..."
echo ""

# Remove folders
for folder in "${folders[@]}"; do
    if [ -d "$folder" ]; then
        echo "  ✓ Removing folder: $folder"
        rm -rf "$folder"
    fi
done

# Remove files
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ Removing file: $file"
        rm -f "$file"
    fi
done

echo ""
echo "✅ Cleanup completed!"
