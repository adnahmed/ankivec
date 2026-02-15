#!/bin/bash
set -e

install () {
  echo "Installing runtime dependencies to vendor directory..."
  rm -rf vendor
  pip install -r requirements-runtime.txt -t vendor
  echo "Dependencies installed to vendor/"
}

build () {
  echo "Building..."
  rm -rf dist
  mkdir -p dist

  cp *.py dist/ 2>/dev/null || true
  cp manifest.json dist/
  cp config.json dist/
  cp -r src dist/
  cp -r vendor dist/ 2>/dev/null || (echo "Vendor directory not found. Running install..."; install; cp -r vendor dist/)

  # Nuke any pycache
  find dist -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

  # Zip it
  cd dist
  zip -9 -r ankivec.ankiaddon .
  cd ..
  
  echo "Build complete: dist/ankivec.ankiaddon"
}

clean () {
  echo "Cleaning..."
  rm -rf dist
  rm -rf ~/.config/Anki2/addons21/ankivec 2>/dev/null || true
  rm -rf ~/Library/Application\ Support/Anki2/addons21/ankivec 2>/dev/null || true
}

link-dev () {
  echo "Linking development environment..."
  # macOS
  if [ "$(uname)" = "Darwin" ]; then
    rm -rf ~/Library/Application\ Support/Anki2/addons21/ankivec
    ln -s "$(pwd)" ~/Library/Application\ Support/Anki2/addons21/ankivec
  # Linux
  elif [ "$(uname)" = "Linux" ]; then
    rm -rf ~/.config/Anki2/addons21/ankivec
    ln -s "$(pwd)" ~/.config/Anki2/addons21/ankivec
  else
    echo "Unsupported OS for link-dev"
    exit 1
  fi
  echo "Development link created"
}

link-dist () {
  echo "Linking dist build..."
  # macOS
  if [ "$(uname)" = "Darwin" ]; then
    rm -rf ~/Library/Application\ Support/Anki2/addons21/ankivec
    ln -s "$(pwd)/dist" ~/Library/Application\ Support/Anki2/addons21/ankivec
  # Linux
  elif [ "$(uname)" = "Linux" ]; then
    rm -rf ~/.config/Anki2/addons21/ankivec
    ln -s "$(pwd)/dist" ~/.config/Anki2/addons21/ankivec
  else
    echo "Unsupported OS for link-dist"
    exit 1
  fi
  echo "Dist link created"
}

# Main command dispatcher
case "$1" in
  install)
    install
    ;;
  build)
    clean
    build
    ;;
  clean)
    clean
    ;;
  link-dev)
    link-dev
    ;;
  link-dist)
    link-dist
    ;;
  *)
    echo "Invalid command: $1"
    echo ""
    echo "Available commands:"
    echo "  install     - Install runtime dependencies to vendor/"
    echo "  build       - Create production build (ankivec.ankiaddon)"
    echo "  clean       - Remove dist/ and Anki addon symlink"
    echo "  link-dev    - Symlink current directory to Anki addons21"
    echo "  link-dist   - Symlink dist/ to Anki addons21 for testing builds"
    exit 1
    ;;
esac

echo "Done"
