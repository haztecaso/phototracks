# phototracks

**phototracks** is a tool for geolocating photos based on GPX tracks from your
photography promenades. 

Right now it does the following:

- Look for images and track files in two input folders.
- Get a *timestamp* for each photo. It will try reading the *timestamp* from the
  image file name. Otherwise it will read the EXIF metadata.
- Assign a track to each photo (the track that started before the image was
  taken and ended after).
- For each track and photo, look at the closest point in time from the track to
  the timestamp of the image. Add this point as a gpx waypoint.
- Save the new gpx files with the image waypoints.

And these are the features I want to implement next:

- [ ] Web viewer of tracks, with image thumbnails generation.
- [ ] Organisation of python cli app to make some parameters configurable.
- [ ] Modification of image EXIF metadata to include location.
