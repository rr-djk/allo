#!/bin/bash
# Wrapper shell pour la commande record.
#
# Installation :
#   sudo cp record.sh /usr/local/bin/record
#   sudo chmod +x /usr/local/bin/record
#
# Lancement :
#   record &
python3 /home/rr-djk/Documents/projets/allo/record.py "$@"
