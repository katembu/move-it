# List all reports here
__all__ = ('UtilizationReport',)

# This is the way we get the celery workers
# to register all of the ReportDefinition tasks
from reportgen.definitions import *

