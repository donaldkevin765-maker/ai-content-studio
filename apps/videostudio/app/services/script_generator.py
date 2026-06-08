from __future__ import annotations
import json
import httpx
from loguru import logger
from app.config import settings


class ScriptGenerator:
    def __init__(self):
        self.ollama_url = f"{settings.ollama_base_url}/api/generate"
        self.model = settings.ollama_model

    async def generate(self, topic: str, duration_sec: int = 60, style: str = "informativo") -> dict:
        logger.info(f"Generazione script: topic={topic}, durata={duration_sec}s, stile={style}")

        provider_order = ["ensemble", "ollama"]

        for provider in provider_order:
            try:
                if provider == "ensemble":
                    from app.services.llm_providers import LLMEnsemble
                    result = await LLMEnsemble().generate(self._build_prompt(topic, duration_sec, style))
                    if result:
                        return self._parse_llm_result(result, topic, duration_sec, style)
                elif provider == "ollama" and settings.ollama_base_url:
                    return await self._generate_with_llm(topic, duration_sec, style)
            except Exception as e:
                logger.warning(f"Provider {provider} fallito: {e}")
                continue

        return self._generate_template(topic, duration_sec, style)

    def _build_prompt(self, topic: str, duration_sec: int, style: str) -> str:
        num_scenes = max(2, min(8, duration_sec // 10))
        return f"""Sei un scriptwriter professionista per video brevi. Genera uno script per un video di {duration_sec} secondi sul tema: "{topic}".
Stile: {style}
Numero di scene: {num_scenes}

Rispondi SOLO con JSON valido nel formato:
{{
  "scenes": [
    {{"content": "testo narrato della scena", "image_prompt": "descrizione per generare immagine", "duration": 5.0}},
    ...
  ]
}}

Ogni scena deve avere un contenuto di circa 2-3 frasi. Le image_prompt devono essere descrittive e visive.
La durata totale di tutte le scene deve essere circa {duration_sec} secondi."""

    def _parse_llm_result(self, result: str, topic: str, duration_sec: int, style: str) -> dict:
        import re as _re
        num_scenes = max(2, min(8, duration_sec // 10))
        try:
            cleaned = _re.sub(r"^```(?:json)?\s*|\s*```$", "", result.strip(), flags=_re.MULTILINE)
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = _re.search(r"\{.*\}", result, _re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    raise
            else:
                raise
        scenes = []
        for i, s in enumerate(data.get("scenes", [])):
            scenes.append({
                "content": s.get("content", f"Scena {i+1} sul tema {topic}"),
                "image_prompt": s.get("image_prompt", topic),
                "subtitle_text": s.get("content", f"Scena {i+1}"),
                "duration": float(s.get("duration", duration_sec / num_scenes)),
            })
        full_script = "\n\n".join(s["content"] for s in scenes)
        return {"full_script": full_script, "scenes": scenes}

    async def _generate_with_llm(self, topic: str, duration_sec: int, style: str) -> dict:
        prompt = self._build_prompt(topic, duration_sec, style)

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                self.ollama_url,
                json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
            )
            resp.raise_for_status()

        raw = resp.json().get("response", "")
        return self._parse_llm_result(raw, topic, duration_sec, style)

    def _generate_template(self, topic: str, duration_sec: int, style: str) -> dict:
        import random
        rng = random.Random(settings.script_seed + hash(topic) + duration_sec)

        templates = {
            "informativo": {
                "intro": f"Oggi parleremo di {topic}.",
                "patterns": [
                    f"Ecco cosa devi sapere su {topic}: {{}}",
                    f"Un aspetto fondamentale di {topic} è {{}}",
                    "Molte persone non sanno che {}",
                    "Per approfondire: {}",
                ],
                "outro": f"Grazie per aver guardato questo video su {topic}. Iscriviti per altri contenuti!",
            },
            "divertente": {
                "intro": f"Pronto per qualcosa di assurdo su {topic}?",
                "patterns": [
                    "Immagina questo: {}",
                    "Non ci crederai, ma {}",
                    "Ok, questa è buona: {}",
                    "E la ciliegina sulla torta? {}",
                ],
                "outro": f"Se hai riso, metti un like! Ci vediamo al prossimo video su {topic}.",
            },
            "didattico": {
                "intro": f"In questo video imparerai i concetti fondamentali di {topic}.",
                "patterns": [
                    "Primo concetto: {}",
                    "Passiamo al secondo punto: {}",
                    "Ora vediamo come {} si collega al quadro generale",
                    "Esempio pratico: {}",
                ],
                "outro": f"Ricapitolando, oggi hai imparato le basi di {topic}. Esercitati!",
            },
            "motivazionale": {
                "intro": f"Oggi parliamo di {topic}. Un tema che può cambiare la tua vita.",
                "patterns": [
                    "Quando pensi a questo, ricordati che {}",
                    "La verità è che {}. Sta a te decidere",
                    "Non dimenticare mai: {}",
                    "Ecco il punto cruciale: {}",
                ],
                "outro": f"Se questo video ti ha ispirato, condividilo. Vai e conquista!",
            },
            "serio": {
                "intro": f"Benvenuto. Oggi affronteremo un tema importante: {topic}.",
                "patterns": [
                    "Analizziamo i dati: {}",
                    "Le ricerche mostrano che {}",
                    "Un punto critico: {}",
                    "In conclusione, {}",
                ],
                "outro": f"Spero questo approfondimento ti sia stato utile. Ci vediamo al prossimo video.",
            },
        }

        details_pool = [
            "questo argomento sta rivoluzionando il modo in cui lavoriamo",
            "i numeri parlano chiaro: la crescita è esponenziale",
            "sempre più persone si stanno avvicinando a questo tema",
            "le possibilità sono infinite se sai dove guardare",
            "il futuro è già qui, sta a noi coglierne le opportunità",
            "l'innovazione non si ferma mai",
            "la conoscenza è il vero potere",
            "ogni grande cambiamento inizia con una piccola idea",
        ]

        tmpl = templates.get(style, templates["informativo"])
        num_scenes = max(2, min(8, duration_sec // 10))
        scene_dur = round(duration_sec / num_scenes, 1)

        selected = rng.sample(details_pool, min(len(details_pool), num_scenes))

        scenes = []
        for i, detail in enumerate(selected):
            pattern = rng.choice(tmpl["patterns"])
            content = pattern.format(detail)
            scenes.append({
                "content": content,
                "image_prompt": f"{topic}, {detail[:60]}, stile professionale, illustration, 4k",
                "subtitle_text": content,
                "duration": scene_dur,
            })

        full_script = f"{tmpl['intro']}\n\n" + "\n\n".join(s["content"] for s in scenes) + f"\n\n{tmpl['outro']}"
        return {"full_script": full_script, "scenes": scenes}
