hnstatus
====

hnstatus reads usage information from a HughesNet Gen5 modem and summarises it in a nice simple GUI. If the appropriate Python libraries are installed it will also display a StatusIcon to give you the modems current status at a glance.
-------------------------------------------------------------------------------------

###hnstatus is for users of HughesNet. It's been tested with an HT2000W modem.

hnstatus is written in Python3 with no support for Python2.

For the StatusIcon to work, you will need Pillow.

**pip3 install pillow**

Planned improvements are to add logging so you will be able to see a nice graph of your usage history.

Current known problems are that the HN modem status codes are not documented, so the only codes that hnstatus can show are ones that I've figured out from trial and error. With more users reporting various status codes to me, I hope to improve that.

To run, just clone this repository, or download the zip and extract it. You can then just run hnstatus.py.

**hnstatus has currently only been tested on Linux Mint. It should work on any Debian based OS. Please report any problems so I can improve hnstatus.**

**hnstatus may work on Windows with the proper PyGTK modules installed, but as I have no Windows systems to test with it's unknown exactly what would be needed**

If you use hnstatus and like it, donations are appreciated. Paypal donations can be made at https://paypal.me/bmillham
