# UV viewer Extension 
![UV viewer](/exts/com.soliptionpictures.hunter/data/preview.png)

# About

This extension can show object's UV in viewport
This Extension is heavily inspried by Camera Reticle Extension 
I create this entension mainly to check if my UV is right since Omniverse does not natively support UV check

# Adding Extensions

To add this extension to your Omniverse app:

Clone the extension from: https://github.com/lydd8888/kit-exts-uv_viewer
Go into: Extension Manager -> Gear Icon -> Setting
Add Local Link to Extension Search Path:../uv_viewer_extension/kit-exts-uv_viewer/exts

# App Link Setup

If `app` folder link doesn't exist or broken it can be created again. For better developer experience it is recommended to create a folder link named `app` to the *Omniverse Kit* app installed from *Omniverse Launcher*. Convenience script to use is included.

Run:

```
> link_app.bat
```

If successful you should see `app` folder link in the root of this repo.

If multiple Omniverse apps is installed script will select recommended one. Or you can explicitly pass an app:

```
> link_app.bat --app create
```

You can also just pass a path to create link to:

```
> link_app.bat --path "C:/Users/bob/AppData/Local/ov/pkg/create-2021.3.4"
```



