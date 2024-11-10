# Hermes Package tracking for Home Assistant

[Homeassistant](https://www.home-assistant.io/) custom module for tracking [Hermes](https://www.myhermes.de) packages.

## Installation

Copy the code to a subfolder of `custom_compoents` folder.

## Usage

Activated the component by adding following to your `configuration.yaml`

```
sensor:
  - platform: hermes
```

### Track a package

Call `hermes.register` with `{ "package_id": "<tracking no>", "package_name": "optional package name for easy identification"}`

### Remove a package from tracking

Call `hermes.unregister` with `{ "package_id": "<tracking no>" }`


To view all your packages in a nice fashion, you may want to use [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) card to view them all as a list in lovelace:

```
- card:
    type: entities
  filter:
    include:
      - domain: hermes
  type: 'custom:auto-entities'
```

## Credits

This plugin is heavily based on [dhl custom component](https://github.com/glance-/dhl) by [`@glance-`](https://github.com/glance-), many thanks 🎉

