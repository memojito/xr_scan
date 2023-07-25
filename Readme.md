## xr_scan
An interactive data visualisation application for a LiDAR scanner Cube 1 by Blickfeld.
Check out the Cube 1 official documentation: https://docs.blickfeld.com/cube/latest/index.html.


## Configuration

1. Create a "static" directory and a "config.toml" file inside.
2. Example config.toml:

```
['general']
ip = "0.0.0.0"

['scanner_ui']
background_photo_path = '/resources/bg.jpg'
```

where ip -- the scanner's ip address,
background_photo_path -- the path of the background photo
