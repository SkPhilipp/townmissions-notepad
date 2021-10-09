import re
from enum import Enum

from cv2 import cv2
from pytesseract import pytesseract

TOWN_MISSION_0_0 = [676, 457]
TOWN_MISSION_1_1 = [1178, 1348]
TOWN_MISSION_COLUMN_WIDTH = TOWN_MISSION_1_1[0] - TOWN_MISSION_0_0[0]
TOWN_MISSION_ROW_HEIGHT = TOWN_MISSION_1_1[1] - TOWN_MISSION_0_0[1]
TOWN_MISSION_TOP_LEFT = [1181, 459]
TOWN_MISSION_IN_PROGRESS_TOP_LEFT = [1308, 470]
TOWN_MISSION_IN_PROGRESS_TOP_LEFT_OFFSET = [
    TOWN_MISSION_IN_PROGRESS_TOP_LEFT[0] - TOWN_MISSION_TOP_LEFT[0],
    TOWN_MISSION_IN_PROGRESS_TOP_LEFT[1] - TOWN_MISSION_TOP_LEFT[1]
]
TOWN_MISSION_IN_PROGRESS_BOTTOM_RIGHT = [1533, 507]
TOWN_MISSION_CONTENT_TOP_LEFT = [1195, 527]
TOWN_MISSION_CONTENT_TOP_LEFT_OFFSET = [
    TOWN_MISSION_CONTENT_TOP_LEFT[0] - TOWN_MISSION_TOP_LEFT[0],
    TOWN_MISSION_CONTENT_TOP_LEFT[1] - TOWN_MISSION_TOP_LEFT[1]
]
TOWN_MISSION_CONTENT_BOTTOM_RIGHT = [1645, 756]

POSITION_START = [3410, 20]
POSITION_DIMENSIONS = [
    3836 - POSITION_START[0],
    38 - POSITION_START[1]
]


class TownMissionCard:
    def __init__(self, column, row):
        self.x = TOWN_MISSION_0_0[0] + column * TOWN_MISSION_COLUMN_WIDTH
        self.y = TOWN_MISSION_0_0[1] + row * TOWN_MISSION_ROW_HEIGHT

    def region_in_progress(self):
        return [
            self.x + TOWN_MISSION_IN_PROGRESS_TOP_LEFT_OFFSET[0],
            self.y + TOWN_MISSION_IN_PROGRESS_TOP_LEFT_OFFSET[1],
            TOWN_MISSION_IN_PROGRESS_BOTTOM_RIGHT[0] - TOWN_MISSION_IN_PROGRESS_TOP_LEFT[0],
            TOWN_MISSION_IN_PROGRESS_BOTTOM_RIGHT[1] - TOWN_MISSION_IN_PROGRESS_TOP_LEFT[1]
        ]

    def region_mission_content(self):
        return [
            self.x + TOWN_MISSION_CONTENT_TOP_LEFT_OFFSET[0],
            self.y + TOWN_MISSION_CONTENT_TOP_LEFT_OFFSET[1],
            TOWN_MISSION_CONTENT_BOTTOM_RIGHT[0] - TOWN_MISSION_CONTENT_TOP_LEFT[0],
            TOWN_MISSION_CONTENT_BOTTOM_RIGHT[1] - TOWN_MISSION_CONTENT_TOP_LEFT[1]
        ]


class TownBoardCapture:
    def __init__(self, image):
        self.image = image

    @staticmethod
    def _card(index):
        column = index % 6
        row = 1 if index >= 6 else 0
        return TownMissionCard(column, row)

    def _image_region(self, region):
        x = region[0]
        y = region[1]
        in_progress_w = region[2]
        in_progress_h = region[3]
        return self.image[y:y + in_progress_h, x:x + in_progress_w]

    def mission_in_progress(self, index):
        card = self._card(index)
        region_image = self._image_region(card.region_in_progress())
        region_image_inverted = cv2.bitwise_not(region_image)
        region_text = pytesseract.image_to_string(region_image_inverted)
        return "PROGRESS" in region_text

    def mission_content(self, index):
        card = self._card(index)
        region_image = self._image_region(card.region_mission_content())
        region_image_inverted = cv2.bitwise_not(region_image)
        region_text = pytesseract.image_to_string(region_image_inverted, config="--psm 4")
        return region_text

    def position_content(self):
        region_image = self._image_region([
            POSITION_START[0],
            POSITION_START[1],
            POSITION_DIMENSIONS[0],
            POSITION_DIMENSIONS[1]
        ])
        region_image_inverted = cv2.bitwise_not(region_image)
        region_text = pytesseract.image_to_string(region_image_inverted, config="--psm 4")
        return region_text

    def position(self):
        """
        Parses the x & y position of the character using the position information on screen.
        :return:
        """
        content = self.position_content()
        content_normalized = re.sub(r'\s+', ' ', content.lower())
        match = re.search(r'position \[(\d+).*? (\d+).*', content_normalized)
        if match:
            return [int(match.group(1)), int(match.group(2))]
        else:
            print(f"[WARN] Unable to TownBoardCapture.position() where self.position_content() == \"{content}\"")
            return [0, 0]

    def town(self):
        position = self.position()
        if abs(position[0] - 8848) < 100 and abs(position[1] - 751 < 100):
            return "first-light"
        if abs(position[0] - 9364) < 100 and abs(position[1] - 2752 < 100):
            return "windsward"
        if abs(position[0] - 8945) < 100 and abs(position[1] - 4206 < 100):
            return "everfall"
        if abs(position[0] - 7328) < 100 and abs(position[1] - 3769 < 100):
            return "monarchs-bluffs"
        if abs(position[0] - 7913) < 100 and abs(position[1] - 1896 < 100):
            return "cutlass-keys"
        if abs(position[0] - 11469) < 100 and abs(position[1] - 5323 < 100):
            return "weavers-fen"
        if abs(position[0] - 9554) < 100 and abs(position[1] - 6396 < 100):
            return "brightwood"
        print(f"[WARN] Unable to TownBoardCapture.town() where self.position() == {position}")
        return None


class TownMissionType(Enum):
    FORGE = "forge"
    COOK = "cook"
    ACQUIRE = "acquire"
    HUNT = "hunt"
    SEARCH = "search"
    UNKNOWN = "unknown"


class TownMission:
    def __init__(self, content):
        self.content = re.sub(r'\s+', ' ', content.lower())
        if "search" in self.content and "return" in self.content:
            self.type = TownMissionType.SEARCH
        elif "acquire" in self.content and "deliver" in self.content:
            self.type = TownMissionType.ACQUIRE
        elif "forge" in self.content and "deliver" in self.content:
            self.type = TownMissionType.FORGE
        elif "cook" in self.content and "deliver" in self.content:
            self.type = TownMissionType.COOK
        elif "hunt" in self.content:
            self.type = TownMissionType.HUNT
        else:
            print(f"[WARN] Unable to TownMission.__init__(self, content) where content == \"{content}\"")
            self.type = TownMissionType.UNKNOWN

    def resource(self):
        if self.type == TownMissionType.ACQUIRE:
            match = re.search('deliver\\s*\\d*\\s+([\\w\\s]+)\\.?', self.content)
            return match.group(1)
        if self.type == TownMissionType.FORGE:
            match = re.search('deliver\\s*([\\w\\s]+)\\.?', self.content)
            group = match.group(1)
            return re.sub(r'set of ', '', group)
        if self.type == TownMissionType.COOK:
            match = re.search('deliver\\s*([\\w\\s]+)\\.?', self.content)
            return match.group(1)
        if self.type == TownMissionType.HUNT:
            match = re.search('hunt\\s*\\d*\\s+([\\w]+)\\.?', self.content)
            return match.group(1)
        return None

    def units(self):
        if self.type == TownMissionType.ACQUIRE:
            match = re.search('deliver\\s*(\\d+)', self.content)
            return int(match.group(1))
        if self.type == TownMissionType.FORGE:
            return 1
        if self.type == TownMissionType.COOK:
            return 1
        if self.type == TownMissionType.HUNT:
            match = re.search('hunt\\s*(\\d+)', self.content)
            return int(match.group(1))
        return None
