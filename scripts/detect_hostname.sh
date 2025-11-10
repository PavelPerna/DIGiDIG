#!/bin/bash
# Detects the preferred hostname for DIGiDIG services

hostname -I | awk '{print $1}' || echo "Unable to detect hostname"
