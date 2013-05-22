from rs import error_reporting
import logging, os



try:
    if os.path.isdir('rs/proprietary'):
        from rs.proprietary import search_engine_overrides
    else:
        raise Exception("Proprietary directory is not defined")
        
except:
    # if it doesn't exist (NameError) don't print an error - but just let us know that it doesn't exist
    logging.warning("Unable to import search_engine_overrides\n")
    