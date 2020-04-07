from arlo import Arlo

def take_snapshot(USERNAME, PASSWORD):
    try:
        # Instantiating the Arlo object automatically calls Login(), which returns an oAuth token that gets cached.
        # Subsequent successful calls to login will update the oAuth token.
        arlo = Arlo(USERNAME, PASSWORD)
        # At this point you're logged into Arlo.

        # Get the list of devices and filter on device type to only get the basestation.
        # This will return an array which includes all of the basestation's associated metadata.
        basestations = arlo.GetDevices('basestation')
        
        # Get the list of devices and filter on device type to only get the cameras.
        # This will return an array of cameras, including all of the cameras' associated metadata.
        cameras = arlo.GetDevices('camera')

        # Trigger the snapshot.
        url = arlo.TriggerFullFrameSnapshot(basestations[0], cameras[0]);
        
        # Download snapshot.
        arlo.DownloadSnapshot(url, 'snapshot.jpg')

    return "success"
        
    except Exception as e:
        return str(e)