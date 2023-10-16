#!/bin/bash
################################################################################
# Script for initialize the GIMM Odoo repository
# Author: Viet Pham
#-------------------------------------------------------------------------------
# Place this content in it and then make the file executable:
# sudo chmod +x init.sh
# Execute the script to init the Odoo repository:
# ./update
################################################################################

git clone --recurse-submodules -j8 git@gitlab.com:grimm_gastronomiebedarf/grimm_odoo_13.git
