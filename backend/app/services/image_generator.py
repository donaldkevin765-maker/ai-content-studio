from __future__ import annotations
import random
from pathlib import Path
from loguru import logger
from app.config import settings


class ImageGenerator:
    TARGET_W = settings.video_width  # 3840
    TARGET_H = settings.video_height  # 2160

    async def generate(self, prompt: str, output_path: str) -> str:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # 1. SDXL via HuggingFace Inference API (free, se token configurato)
        if settings.hf_api_token:
            return await self._huggingface(prompt, str(out))

        # 2. Local Stable Diffusion (se disponibile)
        if settings.use_local_sd:
            return await self._local_sd(prompt, str(out))

        # 3. Prova HuggingFace senza token (alcuni modelli permettono accesso anonimo con rate limit)
        try:
            return await self._huggingface(prompt, str(out))
        except Exception:
            pass

        # 4. Placeholder 4K (fallback finale)
        logger.info("Nessun token HF configurato. Crea un token gratuito su huggingface.co/settings/tokens")
        return await self._placeholder(prompt, str(out))

    async def _huggingface(self, prompt: str, output_path: str) -> str:
        import httpx
        from PIL import Image as PILImage

        # Arricchisci prompt per video fotorealistici
        enhanced = (
            f"{prompt}, cinematic shot, highly detailed, 4K, photorealistic, "
            "professional lighting, sharp focus, vibrant colors, 16:9 aspect ratio"
        )

        # Costruisci headers: solo Authorization se il token è configurato
        headers: dict[str, str] = {}
        if settings.hf_api_token:
            headers["Authorization"] = f"Bearer {settings.hf_api_token}"

        models = [
            # SD3.5 Large (migliore qualita, ~10s)
            "stabilityai/stable-diffusion-3.5-large",
            # SDXL (ottimo, ~5-8s)
            "stabilityai/stable-diffusion-xl-base-1.0",
            # SDXL Turbo (veloce, ~2-3s)
            "stabilityai/sdxl-turbo",
        ]

        errors = []
        for model_id in models:
            try:
                api_url = f"https://api-inference.huggingface.co/models/{model_id}"

                async with httpx.AsyncClient(timeout=180.0) as client:
                    resp = await client.post(
                        api_url,
                        headers=headers or None,
                        json={"inputs": enhanced},
                    )

                if resp.status_code == 503:
                    logger.warning(f"{model_id.split('/')[1]}: modello in caricamento, provo altro")
                    errors.append(f"{model_id}: {resp.status_code}")
                    continue

                resp.raise_for_status()

                # Salva immagine temporanea
                temp_path = output_path.replace(".png", "_raw.png")
                with open(temp_path, "wb") as f:
                    f.write(resp.content)

                # Apri e upscala a 4K con Pillow LANCZOS
                img = PILImage.open(temp_path)
                if img.size != (self.TARGET_W, self.TARGET_H):
                    img = img.resize((self.TARGET_W, self.TARGET_H), PILImage.LANCZOS)
                img.save(output_path, quality=95)

                # Pulisci temp
                Path(temp_path).unlink(missing_ok=True)

                logger.info(f"Immagine AI: {output_path} (modello={model_id}, {img.size[0]}x{img.size[1]})")
                return output_path

            except Exception as e:
                errors.append(f"{model_id}: {e}")
                logger.warning(f"Modello {model_id} fallito: {e}, provo altro")
                continue

        logger.error(f"Tutti i modelli HuggingFace falliti: {errors}")
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

            image = pipe(
                prompt,
                width=self.TARGET_W,
                height=self.TARGET_H,
                num_inference_steps=30,
                guidance_scale=7.5,
            ).images[0]
            image.save(output_path, quality=95)
            logger.info(f"Immagine SD locale: {output_path}")
            return output_path

        except ImportError:
            logger.warning("diffusers non installato, fallback placeholder")
            return await self._placeholder(prompt, output_path)
        except Exception as e:
            logger.error(f"Errore SD locale: {e}")
            return await self._placeholder(prompt, output_path)

    async def _placeholder(self, prompt: str, output_path: str) -> str:
        """Placeholder 4K con gradienti e design migliore del semplice colore."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import math

            w, h = self.TARGET_W, self.TARGET_H
            rng = random.Random(hash(prompt))

            # Crea gradiente di sfondo
            img = Image.new("RGB", (w, h))
            draw = ImageDraw.Draw(img)

            # Gradiente da scuro a medio
            c1 = tuple(rng.randint(10, 40) for _ in range(3))
            c2 = tuple(min(c + 60, 120) for c in c1)
            for y in range(h):
                ratio = y / h
                r = int(c1[0] + (c2[0] - c1[0]) * ratio)
                g = int(c1[1] + (c2[1] - c1[1]) * ratio)
                b = int(c1[2] + (c2[2] - c1[2]) * ratio)
                for x in range(0, w, 16):
                    draw.rectangle([x, y, x + 15, y], fill=(r, g, b))

            # Cerchi decorativi
            for _ in range(8):
                cx = rng.randint(100, w - 100)
                cy = rng.randint(100, h - 100)
                rad = rng.randint(50, 200)
                alpha = rng.randint(10, 30)
                draw.ellipse(
                    [cx - rad, cy - rad, cx + rad, cy + rad],
                    outline=(200, 200, 200, alpha),
                    width=2,
                )

            # Testo prompt
            try:
                font = ImageFont.truetype(str(settings.FONTS_DIR / "NotoSans-Regular.ttf"), 56)
                font_sm = ImageFont.truetype(str(settings.FONTS_DIR / "NotoSans-Regular.ttf"), 32)
            except Exception:
                font = ImageFont.load_default()
                font_sm = font

            draw.text((w // 2 - 200, 80), "[ AI Generated Image ]", fill=(255, 255, 255, 180), font=font_sm)

            lines = prompt.split(". ")
            y_start = h // 2 - len(lines) * 40
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line[:80], font=font)
                x = (w - (bbox[2] - bbox[0])) // 2
                draw.text((x, y_start + i * 80), line[:80], fill=(220, 220, 220), font=font)

            img.save(output_path, quality=90)
            logger.info(f"Placeholder 4K: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Errore placeholder: {e}")
            raise
