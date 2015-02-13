import publicprize.controller as ppc
import logging
import logging.handlers;

# Needs to be explicit
ppc.init()
app = ppc.app()

handler = logging.handlers.RotatingFileHandler(
    '/var/log/publicprize/app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter(
        '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'))
app.logger.addHandler(handler)
