import gettext

_ = gettext.gettext


class PictureGroup:
    def __init__(self, group_name):
        self.name = group_name
        self.trip = None
        self.pictures = {}  # Structure is conversion_type: picture model
        self.locations = {}

    def add_picture(self, picture):
        # Check trip matches the group's trip
        if not self.trip:
            self.trip = picture.trip
        if picture.trip and picture.trip != self.trip:
            raise ValueError(
                "Picture " + picture.name + " has the wrong trip for group " + self.name
            )

        # The picture name starts with the group name ==> easy
        if picture.name.startswith(self.name):
            conversion_type = picture.name.replace(self.name, "")
            if conversion_type not in self.pictures:
                self.pictures[conversion_type] = []
            self.pictures[conversion_type].append(picture)
        # Otherwise we have to re-convert all images
        elif self.name.startswith(picture.name):
            prefix_to_add = self.name[len(picture.name) :]
            self.name = picture.name
            self.pictures = {
                prefix_to_add + conversion_type: self.pictures[conversion_type]
                for conversion_type in self.pictures
            }
            self.pictures[""] = [picture]
        else:
            raise ValueError(
                "Picture " + picture.name + " does not belong to group " + self.name
            )

        # Update locations
        self.locations[picture.location_name] = (
            self.locations.get(picture.location_name, 0) + 1
        )

    def __repr__(self):
        return (self.name, self.trip, str(len(self.pictures)) + " pictures").__repr__()
