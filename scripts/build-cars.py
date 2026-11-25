
import json
from pathlib import Path

# Repository root
ROOT = Path(__file__).resolve().parent.parent
CARS_FOLDER = ROOT / "cars"

# Test output only. Do not overwrite the existing cars.json.
OUTPUT = ROOT / "cars.generated.json"

def resolve_photo(photo, car_id):
    if not isinstance(photo, str) or not photo.strip():
        raise ValueError(f"Invalid photo for {car_id}")

    photo = photo.strip().replace("\\", "/")
    path = Path(photo)

    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe photo path: {photo}")

    # Existing photographs in root or car-images/
    if (ROOT / path).is_file():
        return photo

    # New photographs uploaded to the car's own folder
    new_path = Path("cars") / car_id / "photos" / path

    if len(path.parts) == 1 and (ROOT / new_path).is_file():
        return new_path.as_posix()

    raise FileNotFoundError(f"Photo not found: {car_id} / {photo}")


def build():
    records = {}
    for file in sorted(CARS_FOLDER.glob("*/index.json")):
        with file.open("r", encoding="utf-8") as f:
            car = json.load(f)

        car_id = car.get("id")
        if not isinstance(car_id, str) or car_id != file.parent.name:
            raise ValueError(f"Car ID does not match folder: {file}")

        if car_id in records:
            raise ValueError(f"Duplicate car ID: {car_id}")

        photos = car.get("photos", [])
        if not isinstance(photos, list):
            raise ValueError(f"Invalid photos list: {file}")

        car["photos"] = [
            resolve_photo(photo, car_id)
            for photo in photos
        ]
        records[car_id] = car

    if not records:
        raise ValueError("No individual car records found")

    # Keep the current vehicle display order
    old_file = ROOT / "cars.json"
    with old_file.open("r", encoding="utf-8") as f:
        old_data = json.load(f)

    old_order = [
        car["id"] for car in old_data["cars"]
    ]

    ordered_ids = [
        car_id for car_id in old_order if car_id in records
    ]
    ordered_ids += [
        car_id for car_id in records if car_id not in ordered_ids
    ]

    result = {
        "cars": [records[car_id] for car_id in ordered_ids]
    }

    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print(f"Successfully generated {len(ordered_ids)} cars")
    print(f"Test output: {OUTPUT.name}")
    for car in result["cars"]:
        print(f"{car['id']}: {len(car['photos'])} photos")


if __name__ == "__main__":
    build()
