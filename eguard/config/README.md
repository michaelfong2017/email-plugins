# config
Admin should configure only the file `eguard.yml` by reading `eguard-default.yml`
and figuring out what configurations should be overriden by `eguard.yml`.

Essentially, configurations under the first level key `path` have to be configured
because the paths to different mail directories and even mailbox structure vary
from mail server to mail server.

Beware of software update (if any) that changes `eguard-default.yml`. User configurations
may have to be rechecked.

1. Configure `eguard.yml`. Don't manually edit `eguard-default.yml` and the `eguard-merged.yml`, which are to be generated in the next step.

2. Start/Restart eguard every time `eguard.yml` has changed due to user configuration or `eguard-default.yml` has changed due to a software update, in order to generate `eguard-merged.yml` which is the only configuration file to be processed.