#!/bin/bash
# Jednostavna sinhronizacija za Git Bash
# Pokreni ovo svakih 5 minuta

echo "🔄 Provjeravam ima li novih promjena..."

# 1. Povuci tude promjene
git pull origin main 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Preuzeo sam tude promjene!"
else
    echo "⚠️  Nema novih promjena ili greska"
fi

# 2. Provjeri ima li mojih promjena
status=$(git status --porcelain 2>/dev/null)

if [ -n "$status" ]; then
    echo "📝 Imam promjene za poslati..."

    # Dodaj sve promjene
    git add . 2>/dev/null

    # Spremi promjene sa porukom
    vrijeme=$(date +"%H:%M")
    git commit -m "Promjene u $vrijeme" 2>/dev/null

    # Posalji na internet
    git push origin main 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "🚀 Poslao sam promjene! Prijatelj ce ih vidjeti."
    else
        echo "❌ Ne mogu poslati - netko drugi je promijenio prije mene"
    fi
else
    echo "✨ Sve je vec sinhronizirano!"
fi

echo "🎉 Gotovo! Mozes nastaviti raditi."