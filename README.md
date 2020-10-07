# hal-fuzz-extra
Extension of hal-fuzz that provides support for multiple peripherals in particular:
* Added support for microSD card.
* Added support for TFT LCD Display.
* Added model of generic storage device (Disk).
* Created utility to manipulate FAT32 file systems on-the-fly (used to import fuzzed inputs into models)

Credits to the original authors of HALucinator: http://subwire.net/publication/halucinator/