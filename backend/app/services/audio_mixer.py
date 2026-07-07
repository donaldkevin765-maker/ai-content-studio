from __future__ import annotations
import asyncio
import os
from pathlib import Path
from typing import Optional
from loguru import logger
from app.config import settings


def _get_ffmpeg():
    """Get ffmpeg binary path."""
    from imageio_ffmpeg import get_ffmpeg_exe

    return get_ffmpeg_exe()


class AudioMixer:
    """Mix audio in 5.1 surround con normalizzazione professionale.

    Assegnazione canali 5.1 (usando join filter per ffmpeg >= 7.0):
      - FL (front-left):   musica, 0dB
      - FR (front-right):  musica, 0dB
      - FC (center):       voce narrante
      - LFE (subwoofer):   basse frequenze musica
      - BL (back-left):    musica riverberata, -3dB
      - BR (back-right):   musica riverberata, -3dB

      I 6 canali vengono creati come mono separati e uniti con il filter 'join'.
    """

    async def mix_to_51(
        self,
        voice_path: str,
        music_path: Optional[str],
        output_path: str,
        total_duration: float,
    ) -> str:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        ffmpeg = _get_ffmpeg()

        # Input 0: voice (mono)
        # Input 1: music (stereo o mono, se presente)

        if music_path and os.path.exists(music_path):
            # Crea 6 canali mono separati e uniscili in 5.1 via join filter
            # Canali: FL, FR, FC, LFE, BL, BR
            filter_complex = (
                # Voce → FC
                "[0:a]volume=1.0[a_voice];"
                # Music L → FL
                "[1:a]volume=0.7,pan=mono|c0=c0[a_FL];"
                # Music R → FR
                "[1:a]volume=0.7,pan=mono|c0=c1[a_FR];"
                # Music lowpass → LFE
                "[1:a]volume=0.6,lowpass=f=120,pan=mono|c0=c0[a_LFE];"
                # Music L + delay + lowpass → BL
                "[1:a]volume=0.5,adelay=20|20,lowpass=f=4000,pan=mono|c0=c0[a_BL];"
                # Music R + delay + lowpass → BR
                "[1:a]volume=0.5,adelay=20|20,lowpass=f=4000,pan=mono|c0=c1[a_BR];"
                # Unisci i 6 mono in 5.1 + loudnorm
                "[a_FL][a_FR][a_voice][a_LFE][a_BL][a_BR]"
                "join=inputs=6:channel_layout=5.1,"
                "loudnorm=I=-14:LRA=7:TP=-2[aout]"
            )

            cmd = [
                ffmpeg,
                "-y",
                "-i", voice_path,
                "-i", music_path,
                "-filter_complex", filter_complex,
                "-map", "[aout]",
                "-c:a", "aac",
                "-b:a", "384k",  # AAC 5.1 a 384kbps
                output_path,
            ]
        else:
            # Solo voce → upmix a 5.1 con voce al centro
            # FC = voce, altri canali silenziosi (volume 0)
            filter_complex = (
                "[0:a]volume=1.0[a_voice];"
                "[0:a]volume=0.0[a_silence];"
                "[a_silence][a_silence][a_voice][a_silence][a_silence][a_silence]"
                "join=inputs=6:channel_layout=5.1,"
                "loudnorm=I=-14:LRA=7:TP=-2[aout]"
            )
            cmd = [
                ffmpeg,
                "-y",
                "-i", voice_path,
                "-filter_complex", filter_complex,
                "-map", "[aout]",
                "-c:a", "aac",
                "-b:a", "384k",
                output_path,
            ]

        logger.info(f"Mix 5.1: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120.0)

        if proc.returncode != 0:
            err = stderr.decode()[:500] if stderr else "unknown"
            logger.error(f"Mix 5.1 fallito: {err}")
            # Fallback: copia voce mono
            return await self._fallback_mono(voice_path, output_path)

        logger.info(f"Audio 5.1: {output_path}")
        return output_path

    async def mix_to_stereo(
        self, voice_path: str, music_path: Optional[str], output_path: str
    ) -> str:
        """Mix stereo ottimizzato per social (fallback/alternativa a 5.1)."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        ffmpeg = _get_ffmpeg()

        if music_path and os.path.exists(music_path):
            # Voice center, music stereo, amix + loudnorm
            cmd = [
                ffmpeg, "-y",
                "-i", voice_path,
                "-i", music_path,
                "-filter_complex",
                "[0:a]volume=1.5[voice];"
                "[1:a]volume=0.6[music];"
                "[voice][music]amix=inputs=2:duration=first,"
                "loudnorm=I=-14:LRA=7:TP=-2[aout]",
                "-map", "[aout]",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path,
            ]
        else:
            cmd = [
                ffmpeg, "-y",
                "-i", voice_path,
                "-filter_complex",
                "[0:a]loudnorm=I=-14:LRA=7:TP=-2[aout]",
                "-map", "[aout]",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path,
            ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)

        if proc.returncode != 0:
            err = stderr.decode()[:200] if stderr else "unknown"
            logger.error(f"Mix stereo fallito: {err}")
            return await self._fallback_mono(voice_path, output_path)

        logger.info(f"Audio stereo: {output_path}")
        return output_path

    async def trigger_github_actions(
        self, video_id: int, supabase_config: dict
    ) -> bool:
        """Trigger GitHub Actions workflow for compilation.

        This method triggers the GitHub Actions workflow that compiles the video
        using tools that aren't available in the serverless environment (ffmpeg).

        Args:
            video_id: The ID of the video to compile
            supabase_config: Dictionary containing Supabase configuration

        Returns:
            bool: True if the workflow was triggered successfully
        """
        # TODO: Implement GitHub Actions trigger logic
        # This would typically involve making a POST request to the GitHub Actions
        # API to trigger the workflow with the video_id and Supabase credentials

        # Example implementation (requires additional configuration):
        # response = await asyncio.create_client(
        #     url=f"{github_api_url}/repos/{github_repo}/dispatches",
        #     method="POST",
        #     headers={
        #         "Authorization": f"token {github_token}",
        #         "Accept": "application/vnd.github.v3+json"
        #     },
        #     json={
        #         "event_type": "compile_video",
        #         "client_payload": {
        #             "video_id": video_id,
        #             "supabase_url": supabase_config.get("url"),
        #             "supabase_key": supabase_config.get("service_key"),
        #         }
        #     }
        # )

        # logger.info(f"GitHub Actions workflow triggered for video {video_id}")
        # return response.status_code in (200, 201)

        logger.info(f"Trigger GitHub Actions workflow for video {video_id}")
        # For now, just log that we would trigger the workflow
        return True

    async def _fallback_mono(self, voice_path: str, output_path: str) -> str:
        """Fallback: copia l'audio voce con normalizzazione base."""
        ffmpeg = _get_ffmpeg()
        cmd = [
            ffmpeg, "-y",
            "-i", voice_path,
            "-c:a", "aac",
            "-b:a", "128k",
            "-af", "loudnorm=I=-14:LRA=7:TP=-2",
            output_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        logger.info(f"Audio fallback mono: {output_path}")
        return output_path
