from rs import error_reporting
import logging


try:
    from rs.proprietary import search_engine_overrides
except NameError:
    # if it doesn't exist (NameError) don't print an error - but just let us know that it doesn't exist
    logging.info("Unable to import search_engine_overrides\n")
except:
    # Notify of all other errors
    error_reporting.log_exception(logging.critical)