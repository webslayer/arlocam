from arlo import Arlo

from datetime import timedelta, date
import datetime

def get_links(USERNAME, PASSWORD):
	try:
	    # Instantiating the Arlo object automatically calls Login(), which returns an oAuth token that gets cached.
	    # Subsequent successful calls to login will update the oAuth token.
	    arlo = Arlo(USERNAME, PASSWORD)
	    # At this point you're logged into Arlo.

	    today = (date.today() - timedelta(days=0)).strftime("%Y%m%d")
	    seven_days_ago = (date.today() - timedelta(days=7)).strftime("%Y%m%d")

	    # Get all of the recordings for a date range.
	    library = arlo.GetLibrary(seven_days_ago, today)

	    links = dict()

	    # Iterate through the recordings in the library.
	    for i, recording in enumerate(library):
	        # Get video as a chunked stream; this function returns a generator.
	        stream = recording['presignedContentUrl']
	        links[f'links{i}'] = stream

	    return links


	except Exception as e:
	    print(e) 
	    return str(e)
