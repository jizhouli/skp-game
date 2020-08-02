# -*- coding: utf-8 -*-

# FIX BUG
# [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
import urllib.request
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

SECRET_ID = "AKIxxxx"
SECRET_KEY = "xxxxxxx"
