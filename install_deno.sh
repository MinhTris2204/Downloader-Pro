#!/bin/bash
# Install Deno if not already installed

if ! command -v deno &> /dev/null
then
    echo "Deno not found, installing..."
    curl -fsSL https://deno.land/install.sh | sh
    export DENO_INSTALL="$HOME/.deno"
    export PATH="$DENO_INSTALL/bin:$PATH"
    echo "Deno installed successfully!"
else
    echo "Deno already installed: $(deno --version | head -n 1)"
fi

# Verify installation
deno --version
