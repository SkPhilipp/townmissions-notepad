from persistence import save, load_all
from recipes import *
from recognition import *
from application import Application

from pynput import keyboard
import threading

import numpy
import win32con
import win32gui
import win32ui


class Mode(Enum):
    CURRENT_MATERIALS = "current materials"
    CURRENT_MISSIONS = "current missions"


APPLICATION = Application()
APPLICATION_MODE = Mode.CURRENT_MISSIONS

display_device_width = 3840
display_device_height = 2160

display_device_context_handle = win32gui.GetWindowDC(None)
display_device_context = win32ui.CreateDCFromHandle(display_device_context_handle)
memory_device_context = display_device_context.CreateCompatibleDC()
bitmap = win32ui.CreateBitmap()
bitmap.CreateCompatibleBitmap(display_device_context, display_device_width, display_device_height)
memory_device_context.SelectObject(bitmap)


def screenshot():
    memory_device_context.BitBlt((0, 0), (display_device_width, display_device_height), display_device_context, (0, 0), win32con.SRCCOPY)
    bitmap_str = bitmap.GetBitmapBits(True)
    bitmap_1d = numpy.frombuffer(bitmap_str, dtype='uint8')
    bitmap_1d.shape = (display_device_height, display_device_width, 4)
    return cv2.cvtColor(bitmap_1d, cv2.COLOR_RGBA2RGB)


def update_town():
    APPLICATION.update("updating...")
    try:
        capture = TownBoardCapture(screenshot())
        recipes = []
        town = capture.town()
        APPLICATION.update(f"updating... {town}")
        if town is None:
            print(f"[WARN] Skipping capture, unable to locate town")
            return
        print(f"[INFO] Parsing town mission board of town \"{town}\"")
        for i in range(0, 12):
            in_progress = capture.mission_in_progress(i)
            if in_progress:
                mission = TownMission(capture.mission_content(i))
                if mission.type == TownMissionType.UNKNOWN:
                    print(f"[WARN] Skipping mission {i}, unable to parse mission type")
                    continue
                resource = Resource.lookup(mission.resource())
                recipe = Recipe.only(resource, mission.units())
                recipes.append(recipe)

        combined_recipe = Recipe.combined(recipes)
        print(f"[INFO] Saving missions of town \"{town}\"")
        save(town, combined_recipe)
    finally:
        if APPLICATION_MODE == Mode.CURRENT_MISSIONS:
            update_current_raw_materials()
        if APPLICATION_MODE == Mode.CURRENT_MATERIALS:
            update_current_materials()


def update_current_materials():
    mapping = load_all()
    recipes = []
    for (town, recipe) in mapping.items():
        recipes.append(recipe)
    recipe_combined = Recipe.combined(recipes).sorted().merged()
    APPLICATION.update("MATERIALS:\n\n" + recipe_combined.markdown())


def update_current_raw_materials():
    mapping = load_all()
    recipes = []
    for (town, recipe) in mapping.items():
        recipes.append(recipe)
    recipe_combined = Recipe.combined(recipes).components().components().components().sorted().merged()
    APPLICATION.update("RAW MATERIALS:\n\n" + recipe_combined.markdown())


def toggle_current_materials():
    global APPLICATION_MODE
    if not APPLICATION.is_hidden() and APPLICATION_MODE == Mode.CURRENT_MATERIALS:
        APPLICATION.hide()
        return
    update_current_materials()
    APPLICATION_MODE = Mode.CURRENT_MATERIALS
    APPLICATION.show()


def toggle_current_raw_materials():
    global APPLICATION_MODE
    if not APPLICATION.is_hidden() and APPLICATION_MODE == Mode.CURRENT_MISSIONS:
        APPLICATION.hide()
        return
    update_current_raw_materials()
    APPLICATION_MODE = Mode.CURRENT_MISSIONS
    APPLICATION.show()


def in_thread(callback):
    def threaded():
        thread = threading.Thread(target=callback)
        thread.start()

    return threaded


def setup_hotkeys():
    with keyboard.GlobalHotKeys({
        '<ctrl>+8': in_thread(toggle_current_materials),
        '<ctrl>+9': in_thread(toggle_current_raw_materials),
        '<ctrl>+0': in_thread(update_town),
    }) as hotkey_listener:
        hotkey_listener.join()


if __name__ == '__main__':
    in_thread(setup_hotkeys)()
    update_current_raw_materials()
    APPLICATION.join()
