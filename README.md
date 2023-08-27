# PyDive
An application to manage scuba diving-related data & files


## Why?
I am a scuba diver and instructor. I also take dive pictures since a few months. And I use both paper and Subsurface as a dive log.
I would like to have a single app that allows me to:
- Manage dive pictures between various locations (SD card, USB stick, archive folder)
- Convert RAW pictures to JPG (I actually have multiple conversion methods, so I need to choose which one to use for each picture)
- Scan my paper dive log and link it to actual dives (and change EXIF data accordingly, to facilitate import in Subsurface)
- Add information to a given dive log image (to help my students for example)
I have no idea whether this will be useful for other people. Probably not, but who knows?

## What is the status of this project?

What is done:
- Models for pictures, picture groups, storage locations, divelog, dive
- Display / Edit of settings (will evolve depending on progress on other items)
- Display / copy / conversion of image, individually or in batches (background processing)
- Display of in-progress background processing
- Display & split of paper dive log scans

What is remaining:
- Views: home, dive analysis/comments

## What else should you know?

So far, I have built only small python scripts and a single PyQt5 application.
Therefore, all this is as much an experimentation as a functional application.

The images are courtesy of [Elegant Themes](https://www.elegantthemes.com/blog/freebie-of-the-week/beautiful-flat-icons-for-free), and were released under GPL.

## Disclaimer

Scuba diving is a dangerous sport. It requires training, good organization and quick reactions to prevent injuries and death. There are (too many) deaths every year, and any dive store should be happy to train you and share our passion.
Dive at your own risk, and don't blame me or GitHub if you make mistakes.