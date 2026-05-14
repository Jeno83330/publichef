import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ExifTags


class ImageProcessor:

    def __init__(self):
        self.brightness_factor = float(os.getenv("IMG_BRIGHTNESS", "1.05"))
        self.contrast_factor   = float(os.getenv("IMG_CONTRAST",   "1.10"))
        self.saturation_factor = float(os.getenv("IMG_SATURATION", "1.08"))
        self.sharpness_factor  = float(os.getenv("IMG_SHARPNESS",  "1.15"))
        self.ig_portrait_size  = (1080, 1350)

    def enhance(self, image_path: Path, output_dir: Path = None) -> Path:
        if output_dir is None:
            output_dir = image_path.parent / "enhanced"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"enhanced_{image_path.name}"

        with Image.open(image_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Correction rotation EXIF
            img = self._fix_rotation(img)

            img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=50, threshold=2))
            img = ImageEnhance.Brightness(img).enhance(self.brightness_factor)
            img = ImageEnhance.Contrast(img).enhance(self.contrast_factor)
            img = ImageEnhance.Color(img).enhance(self.saturation_factor)
            img = ImageEnhance.Sharpness(img).enhance(self.sharpness_factor)
            img = self._smart_crop(img, self.ig_portrait_size)

            img.save(output_path, "JPEG", quality=95, optimize=True)

        return output_path

    def _fix_rotation(self, img: Image.Image) -> Image.Image:
        try:
            exif = img._getexif()
            if exif is None:
                return img
            for tag, value in exif.items():
                if ExifTags.TAGS.get(tag) == 'Orientation':
                    if value == 3:
                        img = img.rotate(180, expand=True)
                    elif value == 6:
                        img = img.rotate(270, expand=True)
                    elif value == 8:
                        img = img.rotate(90, expand=True)
                    break
        except Exception:
            pass
        return img

    def _smart_crop(self, img: Image.Image, target_size: tuple) -> Image.Image:
        target_ratio  = target_size[0] / target_size[1]
        current_ratio = img.width / img.height

        if abs(current_ratio - target_ratio) / target_ratio < 0.20:
            return img

        if current_ratio > target_ratio:
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            new_height = int(img.width / target_ratio)
            top = max(0, (img.height - new_height) // 3)
            img = img.crop((0, top, img.width, top + new_height))

        return img