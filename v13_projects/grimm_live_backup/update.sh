#!/bin/bash
################################################################################
# Script for update the GIMM Odoo Repository
# Author: Viet Pham
#-------------------------------------------------------------------------------
# Place this content in it and then make the file executable:
# sudo chmod +x update.sh
# Execute the script to install Odoo:
# ./update
################################################################################

git pull

git submodule update --init --recursive
