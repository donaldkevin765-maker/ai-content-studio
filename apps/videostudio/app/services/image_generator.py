from __future__ import annotations
import random
from pathlib import Path
from loguru import logger
from app.config import settings


class ImageGenerator:
    async def generate(self, prompt: str, output_path: str) -> str:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if settings.hf_api_token:
            return await self._huggingface(prompt, str(out))
        if settings.use_local_sd:
            return await self._local_sd(prompt, str(out))
        return await self._placeholder(prompt, str(out))

    async def _huggingface(self, prompt: str, output_path: str) -> str:
        import httpx
        try:
            api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            headers = {"Authorization": f"Bearer {settings.hf_api_token}"}
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(api_url, headers=headers, json={"inputs": prompt})
                resp.raise_for_status()
                with open(output_path, "wb") as f:
                    f.write(resp.content)
            logger.info(f"Immagine HuggingFace: {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"Errore HuggingFace: {e}, fallback placeholder")
            return await self._placeholder(prompt, output_path)

    async def _local_sd(self, prompt: str, output_path: str) -> str:
        try:
            import torch
            from diffusers import StableDiffusionPipeline
            pipe = StableDiffusionPipeline.from_pretrained(
                settings.sd_model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            )
            if torch.cuda.is_available():
                pipe = pipe.to("cuda")
            image = pipe(prompt, width=settings.video_width, height=settings.video_height).images[0]
            image.save(output_path)
            logger.info(f"Immagine SD: {output_path}")
            return output_path
        except ImportError:
            logger.warning("diffusers non installato, fallback placeholder")
            return await self._placeholder(prompt, output_path)
        except Exception as e:
            logger.error(f"Errore SD: {e}")
            return await self._placeholder(prompt, output_path)

    async def _placeholder(self, prompt: str, output_path: str) -> str:
        try:
            from PIL import Image, ImageDraw, ImageFont
            w, h = settings.video_width, settings.video_height
            rng = random.Random(hash(prompt))
            bg = tuple(rng.randint(15, 55) for _ in range(3))
            img = Image.new("RGB", (w, h), bg)
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype(str(settings.FONTS_DIR / "NotoSans-Regular.ttf"), 40)
                font_sm = ImageFont.truetype(str(settings.FONTS_DIR / "NotoSans-Regular.ttf"), 22)
            except Exception:
                font = ImageFont.load_default()
                font_sm = font
            draw.text((w // 2 - 50, 60), "[ AI Generated ]", fill="white", font=font_sm)
            lines = prompt.split(", ")
            y = h // 2 - len(lines) * 30
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                x = (w - (bbox[2] - bbox[0])) // 2
                draw.text((x, y), line, fill="white", font=font)
                y += 60
            img.save(output_path, quality=85)
            logger.info(f"Placeholder: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Errore placeholder: {e}")
            raise
