#!/bin/bash

if [ -z "$1" ]; then
    echo "$0 <VERSION>"
    echo "    VERSION: Must be 3 o 4."
    exit 0
fi

cp ordinario/account.xml ../modules/account_es/
cp ordinario/tax$1.xml ../modules/account_es/tax.xml
cp pymes/acount.xml ../modules/account_es_pyme/
cp pymes/tax$1.xml ../modules/account_es_pyme/tax.xml
cp aeat/340.xml ../modules/aeat_340/
cp aeat/349.xml ../modules/aeat_349/
