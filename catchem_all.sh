#!/bin/bash
set -e

script_name=`basename "$0"`

print_help() {
    printf "\n Usage: bash $script_name [OPTION]\n\n"
    printf " OPTIONS:\n"
    printf " -t,  --type  [ pdf | epub | all ]    Specifies which filetypes to download.\n"
    printf " Example: bash $script_name -t pdf  Default: pdf\n"
    printf "\n -h,  --help                          Prints this help dialog.\n\n"
}

while [ $# -gt 0 ]; do
    key="$1"
    case $key in
        -h|--help)
        print_help
        exit 0
        ;;
        -t|--type)
        type="$2"
        shift;
        shift;
        ;;
        *) # unknown option
        printf " ERROR: $script_name: unknown argument: '$1'\n"
        print_help
        exit 1
    esac
done

if which python3 > /dev/null 2>&1; then
    if [ ! -f ./.venv/bin/activate ]; then
        echo "Creating python3 virtual environment."
        python3 -m venv .venv > /dev/null 2>&1 || py3venv_failed=true
        if [ "$py3venv_failed" = true ]; then
            rm -rf .venv
            virtualenv -p $(which python3) .venv
        fi;
    fi;
    source .venv/bin/activate
    echo "Installing packages, please wait..."
    pip3 install -r requirements.txt 1>/dev/null
    python3 get_springer.py --type $type
elif which python > /dev/null 2>&1; then
    if [ ! -f ./.venv/bin/activate ]; then
        if ! which virtualenv > /dev/null 2>&1; then
            pip install virtualenv
        fi;
        echo "Creating python virtual environment."
        virtualenv -p $(which python) .venv
    fi;
    source .venv/bin/activate
    echo "Installing packages, please wait..."
    pip install -r requirements2x.txt 1>/dev/null
    python get_springer.py --type $type
else
    echo "ERROR: Could not find python in the local environment. Exiting..."
    exit 1
fi
