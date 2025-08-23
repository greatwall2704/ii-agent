#!/bin/bash
"""
Wrapper script for HTML to PDF conversion tools.

This script provides a simple interface to convert HTML slides to PDF
using different rendering engines with fallback options.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
SRC_DIR=""
OUTPUT=""
ENGINE="playwright"
PAGE_FORMAT="A4"
ORIENTATION="landscape"
INSTALL_DEPS=false

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
HTML Slides to PDF Converter

Usage: $0 [OPTIONS]

Options:
    -s, --src-dir DIR       Source directory containing HTML slides (required)
    -o, --output FILE       Output PDF file path (default: slides.pdf in source dir)
    -e, --engine ENGINE     Rendering engine: playwright, selenium, wkhtmltopdf (default: playwright)
    -f, --format FORMAT     Page format: A4, Letter, etc. (default: A4)
    -r, --orientation ORIENT Page orientation: landscape, portrait (default: landscape)
    -i, --install           Install required dependencies
    -h, --help              Show this help message

Examples:
    $0 -s ./my-slides -o presentation.pdf
    $0 -s ./slides -e selenium -f Letter -r portrait
    $0 -i -s ./slides  # Install deps and convert

Engines:
    playwright      - Best quality, handles JS well (recommended)
    selenium        - Good compatibility, reliable
    wkhtmltopdf     - Fast, lightweight, basic JS support
EOF
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Install Python packages
    if command -v pip3 &> /dev/null; then
        pip3 install -r "$(dirname "$0")/requirements_pdf.txt"
    elif command -v pip &> /dev/null; then
        pip install -r "$(dirname "$0")/requirements_pdf.txt"
    else
        print_error "pip not found. Please install Python pip first."
        exit 1
    fi
    
    # Install Playwright browsers if using playwright
    if [[ "$ENGINE" == "playwright" ]]; then
        print_status "Installing Playwright browsers..."
        python3 -m playwright install chromium
    fi
    
    # Install wkhtmltopdf if using wkhtmltopdf engine
    if [[ "$ENGINE" == "wkhtmltopdf" ]]; then
        print_status "Checking for wkhtmltopdf..."
        if ! command -v wkhtmltopdf &> /dev/null; then
            print_warning "wkhtmltopdf not found. Installing..."
            if command -v apt-get &> /dev/null; then
                sudo apt-get update && sudo apt-get install -y wkhtmltopdf
            elif command -v yum &> /dev/null; then
                sudo yum install -y wkhtmltopdf
            elif command -v brew &> /dev/null; then
                brew install wkhtmltopdf
            else
                print_error "Cannot install wkhtmltopdf automatically. Please install it manually."
                exit 1
            fi
        fi
    fi
    
    print_status "Dependencies installed successfully!"
}

# Function to convert slides
convert_slides() {
    local script_dir="$(dirname "$0")"
    local python_cmd=""
    
    # Find Python command
    if command -v python3 &> /dev/null; then
        python_cmd="python3"
    elif command -v python &> /dev/null; then
        python_cmd="python"
    else
        print_error "Python not found. Please install Python first."
        exit 1
    fi
    
    print_status "Converting slides using $ENGINE engine..."
    print_status "Source: $SRC_DIR"
    print_status "Output: $OUTPUT"
    print_status "Format: $PAGE_FORMAT ($ORIENTATION)"
    
    case "$ENGINE" in
        "playwright")
            $python_cmd "$script_dir/html_slides_to_pdf_playwright.py" \
                --src-dir "$SRC_DIR" \
                --out "$OUTPUT" \
                --page-format "$PAGE_FORMAT" \
                --orientation "$ORIENTATION"
            ;;
        "selenium")
            $python_cmd "$script_dir/html_slides_to_pdf.py" \
                --src-dir "$SRC_DIR" \
                --out "$OUTPUT" \
                --page-size "$PAGE_FORMAT" \
                --orientation "$ORIENTATION"
            ;;
        "wkhtmltopdf")
            $python_cmd "$script_dir/html_slides_to_pptx.py" \
                --src-dir "$SRC_DIR" \
                --out "$OUTPUT"
            ;;
        *)
            print_error "Unknown engine: $ENGINE"
            exit 1
            ;;
    esac
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--src-dir)
            SRC_DIR="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -e|--engine)
            ENGINE="$2"
            shift 2
            ;;
        -f|--format)
            PAGE_FORMAT="$2"
            shift 2
            ;;
        -r|--orientation)
            ORIENTATION="$2"
            shift 2
            ;;
        -i|--install)
            INSTALL_DEPS=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$SRC_DIR" ]] && [[ "$INSTALL_DEPS" != true ]]; then
    print_error "Source directory is required"
    show_usage
    exit 1
fi

# Install dependencies if requested
if [[ "$INSTALL_DEPS" == true ]]; then
    install_dependencies
    if [[ -z "$SRC_DIR" ]]; then
        print_status "Dependencies installed. You can now run the converter."
        exit 0
    fi
fi

# Set default output if not specified
if [[ -z "$OUTPUT" ]]; then
    OUTPUT="$SRC_DIR/slides.pdf"
fi

# Validate source directory
if [[ ! -d "$SRC_DIR" ]]; then
    print_error "Source directory does not exist: $SRC_DIR"
    exit 1
fi

# Convert slides
convert_slides

print_status "Conversion completed successfully!"
print_status "Output file: $OUTPUT"
