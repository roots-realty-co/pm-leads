#!/bin/bash
# Packages lambda_newsletter.py + dependencies into a zip ready for AWS Lambda.
# Run from the Roots/ root directory: bash newsletter/deploy.sh

set -e

FUNCTION_NAME="newsletter-slack"
PACKAGE_DIR="newsletter/package"
ZIP_FILE="newsletter/lambda_newsletter.zip"

echo "Cleaning old build..."
rm -rf "$PACKAGE_DIR" "$ZIP_FILE"
mkdir -p "$PACKAGE_DIR"

echo "Installing dependencies..."
pip3 install feedparser --quiet --target "$PACKAGE_DIR"

echo "Copying function..."
cp newsletter/lambda_newsletter.py "$PACKAGE_DIR/lambda_function.py"

echo "Zipping..."
cd "$PACKAGE_DIR" && zip -r "../lambda_newsletter.zip" . -x "*.pyc" -x "*/__pycache__/*" > /dev/null
cd ../..

echo "Done. Upload newsletter/lambda_newsletter.zip to AWS Lambda."
echo ""
echo "Lambda settings:"
echo "  Runtime:  Python 3.12"
echo "  Handler:  lambda_function.lambda_handler"
echo "  Timeout:  60 seconds"
echo "  Memory:   256 MB"
echo ""
echo "Environment variables to set in Lambda console:"
echo "  CLAUDE_API_KEY"
echo "  SLACK_BOT_TOKEN"
echo "  SLACK_CONTENT_CHANNEL_ID"
echo ""
echo "EventBridge schedule: cron(0 14 ? * MON *)"
echo "  = Every Monday 8am MDT (14:00 UTC)"
echo "  Note: adjust to cron(0 15 ? * MON *) in winter (MST)"
