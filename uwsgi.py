import publicprize.controller as ppc
import logging

logging.getLogger().setLevel(logging.INFO)
# Needs to be explicit
ppc.init()
app = ppc.app()
