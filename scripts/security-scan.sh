#!/bin/bash

################################################################################
# Security Scanning Script for Delicious Lotus
#
# This script performs comprehensive security scanning including:
# - Python dependency vulnerabilities (safety, pip-audit)
# - Docker image vulnerabilities (Trivy)
# - Code security issues (Bandit)
# - Terraform misconfigurations (tfsec)
# - Secret detection (gitleaks)
#
# Usage: ./scripts/security-scan.sh [--ci] [--fail-on-critical]
#
# Options:
#   --ci                Exit with non-zero code on any findings
#   --fail-on-critical  Exit with non-zero code only on critical/high issues
#   --skip-trivy        Skip Trivy Docker image scanning
#   --skip-tfsec        Skip Terraform security scanning
#   --help              Show this help message
#
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$PROJECT_ROOT/security-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CI_MODE=false
FAIL_ON_CRITICAL=false
SKIP_TRIVY=false
SKIP_TFSEC=false
EXIT_CODE=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --ci)
      CI_MODE=true
      shift
      ;;
    --fail-on-critical)
      FAIL_ON_CRITICAL=true
      shift
      ;;
    --skip-trivy)
      SKIP_TRIVY=true
      shift
      ;;
    --skip-tfsec)
      SKIP_TFSEC=true
      shift
      ;;
    --help)
      head -n 20 "$0" | tail -n 15
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Create reports directory
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}  Delicious Lotus Security Scanning${NC}"
echo -e "${BLUE}  Started at: $(date)${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

################################################################################
# Function: Check if command exists
################################################################################
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

################################################################################
# Function: Install missing tools
################################################################################
install_tools() {
  echo -e "${YELLOW}Checking for required security tools...${NC}"

  # Check Python tools
  if ! command_exists safety; then
    echo -e "${YELLOW}Installing safety...${NC}"
    pip install --quiet safety
  fi

  if ! command_exists pip-audit; then
    echo -e "${YELLOW}Installing pip-audit...${NC}"
    pip install --quiet pip-audit
  fi

  if ! command_exists bandit; then
    echo -e "${YELLOW}Installing bandit...${NC}"
    pip install --quiet bandit
  fi

  # Check Trivy (Docker image scanner)
  if ! command_exists trivy && [ "$SKIP_TRIVY" = false ]; then
    echo -e "${YELLOW}Installing Trivy...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
      curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
    elif [[ "$OSTYPE" == "darwin"* ]]; then
      brew install trivy
    else
      echo -e "${YELLOW}Trivy installation not supported on this OS. Skipping Trivy scan.${NC}"
      SKIP_TRIVY=true
    fi
  fi

  # Check tfsec (Terraform security scanner)
  if ! command_exists tfsec && [ "$SKIP_TFSEC" = false ]; then
    echo -e "${YELLOW}Installing tfsec...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
      curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash
    elif [[ "$OSTYPE" == "darwin"* ]]; then
      brew install tfsec
    else
      echo -e "${YELLOW}tfsec installation not supported on this OS. Skipping Terraform scan.${NC}"
      SKIP_TFSEC=true
    fi
  fi

  # Check gitleaks (secret detection)
  if ! command_exists gitleaks; then
    echo -e "${YELLOW}Installing gitleaks...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
      wget -qO- https://github.com/gitleaks/gitleaks/releases/download/v8.18.1/gitleaks_8.18.1_linux_x64.tar.gz | tar xz -C /tmp
      sudo mv /tmp/gitleaks /usr/local/bin/
    elif [[ "$OSTYPE" == "darwin"* ]]; then
      brew install gitleaks
    else
      echo -e "${YELLOW}gitleaks installation not supported on this OS. Skipping secret detection.${NC}"
    fi
  fi

  echo -e "${GREEN}✓ All required tools are installed${NC}"
  echo ""
}

################################################################################
# 1. Dependency Vulnerability Scanning
################################################################################
scan_dependencies() {
  echo -e "${BLUE}[1/6] Scanning Python dependencies for vulnerabilities...${NC}"

  local requirements_file="$PROJECT_ROOT/fastapi/requirements.txt"

  if [ ! -f "$requirements_file" ]; then
    echo -e "${RED}✗ requirements.txt not found at $requirements_file${NC}"
    return 1
  fi

  # Safety check
  echo -e "${YELLOW}  Running safety check...${NC}"
  if safety check --file="$requirements_file" --json > "$REPORTS_DIR/safety_$TIMESTAMP.json" 2>&1; then
    echo -e "${GREEN}  ✓ No vulnerabilities found by safety${NC}"
  else
    echo -e "${RED}  ✗ Vulnerabilities found by safety${NC}"
    cat "$REPORTS_DIR/safety_$TIMESTAMP.json" | jq '.' || cat "$REPORTS_DIR/safety_$TIMESTAMP.json"
    EXIT_CODE=1
  fi

  # pip-audit check
  echo -e "${YELLOW}  Running pip-audit...${NC}"
  if pip-audit --requirement="$requirements_file" --format=json > "$REPORTS_DIR/pip-audit_$TIMESTAMP.json" 2>&1; then
    echo -e "${GREEN}  ✓ No vulnerabilities found by pip-audit${NC}"
  else
    echo -e "${RED}  ✗ Vulnerabilities found by pip-audit${NC}"
    cat "$REPORTS_DIR/pip-audit_$TIMESTAMP.json" | jq '.' || cat "$REPORTS_DIR/pip-audit_$TIMESTAMP.json"
    EXIT_CODE=1
  fi

  echo ""
}

################################################################################
# 2. Code Security Scanning (Bandit)
################################################################################
scan_code() {
  echo -e "${BLUE}[2/6] Scanning Python code for security issues...${NC}"

  local app_dir="$PROJECT_ROOT/fastapi/app"

  if [ ! -d "$app_dir" ]; then
    echo -e "${RED}✗ Application directory not found at $app_dir${NC}"
    return 1
  fi

  echo -e "${YELLOW}  Running Bandit...${NC}"

  # Run Bandit (returns non-zero if issues found)
  if bandit -r "$app_dir" -f json -o "$REPORTS_DIR/bandit_$TIMESTAMP.json" 2>&1; then
    echo -e "${GREEN}  ✓ No security issues found by Bandit${NC}"
  else
    # Check if there are HIGH or CRITICAL issues
    local critical_count=$(cat "$REPORTS_DIR/bandit_$TIMESTAMP.json" | jq '[.results[] | select(.issue_severity=="HIGH" or .issue_severity=="CRITICAL")] | length')
    local medium_count=$(cat "$REPORTS_DIR/bandit_$TIMESTAMP.json" | jq '[.results[] | select(.issue_severity=="MEDIUM")] | length')
    local low_count=$(cat "$REPORTS_DIR/bandit_$TIMESTAMP.json" | jq '[.results[] | select(.issue_severity=="LOW")] | length')

    echo -e "${YELLOW}  ⚠ Security issues found:${NC}"
    echo -e "    Critical/High: $critical_count"
    echo -e "    Medium: $medium_count"
    echo -e "    Low: $low_count"

    # Show critical/high issues
    if [ "$critical_count" -gt 0 ]; then
      echo -e "${RED}  Critical/High Issues:${NC}"
      cat "$REPORTS_DIR/bandit_$TIMESTAMP.json" | jq -r '.results[] | select(.issue_severity=="HIGH" or .issue_severity=="CRITICAL") | "    - \(.test_id): \(.issue_text) (\(.filename):\(.line_number))"'
      EXIT_CODE=1
    fi

    if [ "$FAIL_ON_CRITICAL" = false ]; then
      EXIT_CODE=1
    fi
  fi

  echo ""
}

################################################################################
# 3. Docker Image Scanning (Trivy)
################################################################################
scan_docker_images() {
  if [ "$SKIP_TRIVY" = true ]; then
    echo -e "${YELLOW}[3/6] Skipping Docker image scanning (--skip-trivy)${NC}"
    echo ""
    return 0
  fi

  echo -e "${BLUE}[3/6] Scanning Docker images for vulnerabilities...${NC}"

  local dockerfile="$PROJECT_ROOT/fastapi/Dockerfile"

  if [ ! -f "$dockerfile" ]; then
    echo -e "${RED}✗ Dockerfile not found at $dockerfile${NC}"
    return 1
  fi

  echo -e "${YELLOW}  Building Docker image for scanning...${NC}"

  # Build image with temporary tag
  local image_name="delicious-lotus-backend:security-scan"
  if docker build -t "$image_name" -f "$dockerfile" "$PROJECT_ROOT/fastapi" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Image built successfully${NC}"
  else
    echo -e "${RED}  ✗ Failed to build Docker image${NC}"
    return 1
  fi

  echo -e "${YELLOW}  Running Trivy scan...${NC}"

  # Scan image with Trivy
  trivy image --severity HIGH,CRITICAL --format json --output "$REPORTS_DIR/trivy_$TIMESTAMP.json" "$image_name" 2>&1

  # Parse results
  local critical_count=$(cat "$REPORTS_DIR/trivy_$TIMESTAMP.json" | jq '[.Results[].Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length')
  local high_count=$(cat "$REPORTS_DIR/trivy_$TIMESTAMP.json" | jq '[.Results[].Vulnerabilities[]? | select(.Severity=="HIGH")] | length')

  if [ "$critical_count" -eq 0 ] && [ "$high_count" -eq 0 ]; then
    echo -e "${GREEN}  ✓ No critical or high vulnerabilities found${NC}"
  else
    echo -e "${RED}  ✗ Vulnerabilities found in Docker image:${NC}"
    echo -e "    Critical: $critical_count"
    echo -e "    High: $high_count"

    # Show top 5 critical vulnerabilities
    if [ "$critical_count" -gt 0 ]; then
      echo -e "${RED}  Top Critical Vulnerabilities:${NC}"
      cat "$REPORTS_DIR/trivy_$TIMESTAMP.json" | jq -r '[.Results[].Vulnerabilities[]? | select(.Severity=="CRITICAL")] | .[:5] | .[] | "    - \(.VulnerabilityID): \(.PkgName) \(.InstalledVersion) -> \(.FixedVersion // "no fix")"'
    fi

    EXIT_CODE=1
  fi

  # Clean up temporary image
  docker rmi "$image_name" > /dev/null 2>&1 || true

  echo ""
}

################################################################################
# 4. Terraform Security Scanning (tfsec)
################################################################################
scan_terraform() {
  if [ "$SKIP_TFSEC" = true ]; then
    echo -e "${YELLOW}[4/6] Skipping Terraform security scanning (--skip-tfsec)${NC}"
    echo ""
    return 0
  fi

  echo -e "${BLUE}[4/6] Scanning Terraform configurations for security issues...${NC}"

  local terraform_dir="$PROJECT_ROOT/terraform"

  if [ ! -d "$terraform_dir" ]; then
    echo -e "${RED}✗ Terraform directory not found at $terraform_dir${NC}"
    return 1
  fi

  echo -e "${YELLOW}  Running tfsec...${NC}"

  # Run tfsec
  if tfsec "$terraform_dir" --format json --out "$REPORTS_DIR/tfsec_$TIMESTAMP.json" 2>&1; then
    echo -e "${GREEN}  ✓ No security issues found in Terraform${NC}"
  else
    # Parse results
    local critical_count=$(cat "$REPORTS_DIR/tfsec_$TIMESTAMP.json" | jq '[.results[] | select(.severity=="CRITICAL")] | length')
    local high_count=$(cat "$REPORTS_DIR/tfsec_$TIMESTAMP.json" | jq '[.results[] | select(.severity=="HIGH")] | length')
    local medium_count=$(cat "$REPORTS_DIR/tfsec_$TIMESTAMP.json" | jq '[.results[] | select(.severity=="MEDIUM")] | length')

    echo -e "${YELLOW}  ⚠ Security issues found in Terraform:${NC}"
    echo -e "    Critical: $critical_count"
    echo -e "    High: $high_count"
    echo -e "    Medium: $medium_count"

    # Show critical/high issues
    if [ "$critical_count" -gt 0 ] || [ "$high_count" -gt 0 ]; then
      echo -e "${RED}  Critical/High Issues:${NC}"
      cat "$REPORTS_DIR/tfsec_$TIMESTAMP.json" | jq -r '.results[] | select(.severity=="CRITICAL" or .severity=="HIGH") | "    - \(.rule_id): \(.description) (\(.location.filename):\(.location.start_line))"'
      EXIT_CODE=1
    fi
  fi

  echo ""
}

################################################################################
# 5. Secret Detection (gitleaks)
################################################################################
scan_secrets() {
  echo -e "${BLUE}[5/6] Scanning for secrets in code...${NC}"

  if ! command_exists gitleaks; then
    echo -e "${YELLOW}  ⚠ gitleaks not installed, skipping secret detection${NC}"
    echo ""
    return 0
  fi

  echo -e "${YELLOW}  Running gitleaks...${NC}"

  # Run gitleaks
  if gitleaks detect --source="$PROJECT_ROOT" --report-path="$REPORTS_DIR/gitleaks_$TIMESTAMP.json" --no-git 2>&1; then
    echo -e "${GREEN}  ✓ No secrets detected${NC}"
  else
    echo -e "${RED}  ✗ Potential secrets found in code${NC}"

    # Show findings
    if [ -f "$REPORTS_DIR/gitleaks_$TIMESTAMP.json" ]; then
      local secret_count=$(cat "$REPORTS_DIR/gitleaks_$TIMESTAMP.json" | jq '. | length')
      echo -e "    Secrets found: $secret_count"

      # Show first 5 secrets
      echo -e "${RED}  Potential Secrets:${NC}"
      cat "$REPORTS_DIR/gitleaks_$TIMESTAMP.json" | jq -r '.[:5] | .[] | "    - \(.RuleID): \(.File):\(.StartLine)"'
    fi

    EXIT_CODE=1
  fi

  echo ""
}

################################################################################
# 6. Generate Summary Report
################################################################################
generate_summary() {
  echo -e "${BLUE}[6/6] Generating summary report...${NC}"

  local summary_file="$REPORTS_DIR/summary_$TIMESTAMP.txt"

  cat > "$summary_file" <<EOF
================================================================================
Delicious Lotus Security Scan Summary
================================================================================
Scan Date: $(date)
Project: Delicious Lotus Video Generation Platform
Scan Type: Comprehensive Security Audit

================================================================================
SCAN RESULTS
================================================================================

1. Dependency Vulnerabilities (safety, pip-audit)
   - Report: $REPORTS_DIR/safety_$TIMESTAMP.json
   - Report: $REPORTS_DIR/pip-audit_$TIMESTAMP.json

2. Code Security (Bandit)
   - Report: $REPORTS_DIR/bandit_$TIMESTAMP.json

3. Docker Image Vulnerabilities (Trivy)
   - Report: $REPORTS_DIR/trivy_$TIMESTAMP.json

4. Terraform Security (tfsec)
   - Report: $REPORTS_DIR/tfsec_$TIMESTAMP.json

5. Secret Detection (gitleaks)
   - Report: $REPORTS_DIR/gitleaks_$TIMESTAMP.json

================================================================================
RECOMMENDATIONS
================================================================================

HIGH PRIORITY:
- Review all CRITICAL and HIGH severity findings
- Update vulnerable dependencies immediately
- Rotate any exposed secrets
- Apply security patches to container base images

MEDIUM PRIORITY:
- Address MEDIUM severity code issues
- Review Terraform security recommendations
- Update infrastructure configurations

LOW PRIORITY:
- Review LOW severity findings
- Implement additional security controls
- Schedule regular security scans

================================================================================
NEXT STEPS
================================================================================

1. Review detailed reports in $REPORTS_DIR
2. Create tickets for each critical/high finding
3. Update dependencies and rebuild images
4. Re-run security scan to verify fixes
5. Document any accepted risks (with justification)

================================================================================
For questions, contact: security@delicious-lotus.com
================================================================================
EOF

  echo -e "${GREEN}  ✓ Summary report generated: $summary_file${NC}"
  echo ""

  # Display summary
  cat "$summary_file"
}

################################################################################
# Main Execution
################################################################################
main() {
  # Install required tools
  install_tools

  # Run all scans
  scan_dependencies
  scan_code
  scan_docker_images
  scan_terraform
  scan_secrets

  # Generate summary
  generate_summary

  # Final status
  echo -e "${BLUE}=================================================${NC}"
  if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Security scan completed successfully${NC}"
    echo -e "${GREEN}  No critical issues found${NC}"
  else
    echo -e "${RED}✗ Security scan completed with findings${NC}"
    echo -e "${RED}  Please review reports in: $REPORTS_DIR${NC}"
  fi
  echo -e "${BLUE}=================================================${NC}"

  # Exit with appropriate code
  if [ "$CI_MODE" = true ]; then
    exit $EXIT_CODE
  elif [ "$FAIL_ON_CRITICAL" = true ] && [ $EXIT_CODE -ne 0 ]; then
    exit $EXIT_CODE
  else
    exit 0
  fi
}

# Run main function
main
