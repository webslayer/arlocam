from arlo import Arlo
from datetime import timedelta, date
import datetime

class ArloWrap(object):
	"""docstring for ArloWrap"""
	def __init__(self, USERNAME, PASSWORD):
		super(ArloWrap, self).__init__()
		self.arlo = Arlo(USERNAME, PASSWORD)

	def get_links(self):
		try:

			today = (date.today() - timedelta(days=0)).strftime("%Y%m%d")
		    seven_days_ago = (date.today() - timedelta(days=7)).strftime("%Y%m%d")

		    # Get all of the recordings for a date range.
		    library = self.arlo.GetLibrary(seven_days_ago, today)

		    links = dict()

		    # Iterate through the recordings in the library.
		    for i, recording in enumerate(library):
		        # Get video as a chunked stream; this function returns a generator.
		        stream = recording['presignedContentUrl']
		        links[f'links{i}'] = stream

		    return links


		except Exception as e:
		    return str(e)


	def take_snapshot(self):
	    try:

	        # Get the list of devices and filter on device type to only get the basestation.
	        # This will return an array which includes all of the basestation's associated metadata.
	        basestations = self.arlo.GetDevices('basestation')
	        
	        # Get the list of devices and filter on device type to only get the cameras.
	        # This will return an array of cameras, including all of the cameras' associated metadata.
	        cameras = self.arlo.GetDevices('camera')

	        # Trigger the snapshot.
	        url = self.arlo.TriggerFullFrameSnapshot(basestations[0], cameras[0]);
	        
	        # Download snapshot.
	        self.arlo.DownloadSnapshot(url, 'snapshot.jpg')

	        return "success"
	        
	    except Exception as e:
	        return str(e)
