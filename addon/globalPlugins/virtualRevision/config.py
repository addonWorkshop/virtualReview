import config

# Named after the add-on id so it does not share settings with the upstream Virtual Review.
config.conf.spec["virtualRevisionRework"] = {
    "play_beep": "boolean(default=true)",
    "uia_console_grabbing": "boolean(default=false)",
}


def get_config():
    return config.conf["virtualRevisionRework"]
